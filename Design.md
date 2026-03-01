# � System Design

## 1. High-Level Architecture

The system is designed as a decoupled, agent-based orchestration platform.

**Core layers:**

1. **API Layer** (FastAPI) - HTTP request handling
2. **Task Queue** (Celery + Redis) - Async job execution
3. **Orchestration Engine** (DAG-based) - Execution planning and coordination
4. **Service Agents** (Gmail, Calendar) - Domain-specific retrieval and action
5. **Data Layer** (PostgreSQL + pgvector) - Persistent storage and vector search

The engine is transport-agnostic and unaware of service internals. Agents encapsulate all retrieval and execution logic.

---

## 2. Orchestration Flow

```
1. User submits natural language query
   ↓
2. Intent Classifier (LLM) extracts {airline, intent, entities, steps}
   ↓
3. QueryPlanner builds dependency-aware DAG
   ↓
4. Celery worker processes task
   ↓
5. OrchestratorEngine executes steps in dependency order
   ├→ Route to respective agent (Gmail, Calendar)
   ├→ Agent performs hybrid retrieval
   ├→ Agent extracts structured entities
   └→ Engine updates execution context
   ↓
6. ResponseSynthesizer composes natural language summary
   ↓
7. Task returns final result to client
```

---

## 3. Agent Design

Agents are **black-box service adapters** implementing the `BaseAgent` interface.

**Each agent:**
- Owns all retrieval logic (keyword + vector hybrid search)
- Performs semantic and structured filtering
- Extracts entities from results (booking references, dates, etc.)
- Updates execution context for downstream steps

**Engine responsibilities:**
- Route steps to appropriate agents
- Track completion and dependencies
- Manage context propagation
- Orchestrate parallel execution (when dependencies allow)

This separation allows independent scaling and evolution of services.

---

## 4. Hybrid Retrieval Strategy

Hybrid search balances precision and recall:

**Process:**
1. **Keyword Filter**: Use structured entities (e.g., airline name) to filter candidates via SQL ILIKE
2. **Vector Ranking**: Rank filtered results by embedding similarity (pgvector cosine ops)
3. **Fallback**: If keyword filter returns no results, use pure vector similarity

**Example:**
- Query: "Cancel Turkish Airlines flight"
- Keyword filter: `WHERE subject ILIKE '%Turkish%'` → 3 emails
- Vector ranking: Rank by `embedding <-> query_embedding` → Best match first
- Result: High precision (> 0.9) with sub-100ms latency

**Tradeoff:** Hybrid search preferred over pure vector to avoid irrelevant matches.

---

## 5. Async Execution Model

Celery workers execute orchestration tasks asynchronously.

**Advantages:**
- API remains responsive (non-blocking)
- Horizontal worker scaling for throughput
- Isolation of long-running workflows
- Graceful failure handling via task retries

---

## 6. Scaling to 1M Users

### API Layer
- Horizontally scalable FastAPI instances
- Load balancer (nginx/HAProxy)
- Stateless request handling

### Worker Layer
- Multiple Celery workers (auto-scaling)
- Separate queues for different workload types
- Task routing via priority

### Database Layer
- **Partitioning**: Tables partitioned by `user_id` (hash-based sharding)
- **Read replicas**: For high-volume retrieval queries
- **Vector indexing**: pgvector ivfflat with tuned `lists` parameter per partition
- **Connection pooling**: SQLAlchemy async pool with `pool_size=20, max_overflow=40`

### Caching Layer (Redis)
- Embeddings cache (1-hour TTL)
- Intent classification cache
- User metadata cache
- Celery task broker/backend

---

## 7. Caching Strategy

| Cache Type | TTL | Use Case |
|---|---|---|
| **Embeddings** | 1 hour | Avoid recomputing for repeated queries |
| **Intent Classification** | 5 minutes | Common queries (e.g., "cancel flight") |
| **User Metadata** | 10 minutes | Frequently accessed user preferences |
| **Search Results** | 30 seconds | Exact query matches |

---

## 8. Failure Handling

- **Partial failures**: If a step fails (e.g., calendar event not found), the plan continues with available results
- **Graceful degradation**: Response synthesizer adapts to available data
- **Retry logic**: Celery task retries on transient failures (3 attempts by default)
- **Logging**: All step outcomes logged for audit trail

---

## 9. Multi-Region Strategy

- **Stateless API**: Regions share load via DNS routing
- **Region-local Redis**: Each region has its own Celery broker
- **Database replication**: Primary in one region, read replicas in others
- **Vector search locality**: Queries routed to nearest pgvector shard
- **Cross-region sync**: Async replication for user metadata (eventual consistency)

---

## 10. Design Decisions & Tradeoffs

| Decision | Rationale | Tradeoff |
|---|---|---|
| **Local Embeddings (all-MiniLM-L6-v2)** | Avoids API latency/costs while proving pgvector math is accurate. | 384 dimensions vs OpenAI's 1536; slightly lower semantic nuance but vastly faster CPU inference. |
| **Rule-Based Intent Mocking** | Provides a deterministic, free environment to build and test the complex DAG engine. | Lacks the dynamic parsing of a true LLM. Future state replaces `classifier.py` with an OpenAI structured output call. |
| **Hybrid retrieval** | Precision > pure vector to avoid hallucinated matches. | 10% slower than keyword-only search. |
| **Agent-based design** | Modularity and isolation. | Slight complexity in dispatch and context propagation. |
| **pgvector ivfflat** | Fast approximate similarity for sub-500ms latency. | Index rebuild required for major resharding. |
| **Celery async + NullPool** | Scalability and resilience while preventing async event-loop pollution. | Added infrastructure (Redis, workers). |

---

## 11. Productionizing the LLM (Future Work)

To transition this orchestrator to production, the mocked `IntentClassifier` will be replaced with an LLM call (e.g., `gpt-4o-mini` or `claude-3-haiku`) using structured outputs. 

**Proposed Prompt Architecture:**
The LLM will be provided the user's query, the conversation context history, and the exact schema of available agent tools. It will be instructed to output a JSON object containing a `steps` array, where each step explicitly declares its `dependencies`. This allows the `QueryPlanner` to dynamically build parallelized execution DAGs on the fly, unlocking true autonomous orchestration.