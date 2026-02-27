from app.services.celery_app import celery_app
from app.orchestrator.engine import OrchestratorEngine
from app.orchestrator.planner import QueryPlanner
from app.llm.classifier import IntentClassifier
from app.llm.synthesizer import Synthesizer
import asyncio


@celery_app.task
def run_orchestration(user_id: str, query: str):
    classifier = IntentClassifier()
    intent = asyncio.run(classifier.classify(query))

    planner = QueryPlanner()
    plan = planner.build_plan(intent)

    engine = OrchestratorEngine()
    results = asyncio.run(engine.execute(plan, {"user_id": user_id}))

    # Synthesize natural language response
    synthesizer = Synthesizer()
    message = synthesizer.synthesize(intent, results)

    return {
        "message": message,
        "details": results
    }