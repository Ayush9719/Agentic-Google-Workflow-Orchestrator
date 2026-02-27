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
| **Hybrid retrieval** | Precision > pure vector | 10% slower than keyword-only |
| **Agent-based design** | Modularity and isolation | Slight complexity in dispatch |
| **Deterministic synthesis** | Reproducibility and testability | Less fluent than LLM responses |
| **pgvector ivfflat** | Fast approximate similarity | Index rebuild required for resharding |
| **Celery async** | Scalability and resilience | Added infrastructure (Redis, workers) |
| **Mock embeddings in demo** | Deterministic testing | Not production-quality |