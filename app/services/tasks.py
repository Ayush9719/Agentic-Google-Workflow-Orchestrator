from app.services.celery_app import celery_app
from app.orchestrator.engine import OrchestratorEngine
from app.orchestrator.planner import QueryPlanner
from app.llm.classifier import IntentClassifier
from app.llm.synthesizer import Synthesizer
import asyncio


@celery_app.task
def run_orchestration(user_id: str, query: str):
    """Wrapper task to run the async orchestration pipeline in a single loop."""
    
    # Define the entire flow as a single async function
    async def _run_pipeline():
        # 1. Classify
        classifier = IntentClassifier()
        intent = await classifier.classify(query)

        # 2. Plan
        planner = QueryPlanner()
        plan = planner.build_plan(intent)

        # 3. Execute
        engine = OrchestratorEngine()
        results = await engine.execute(plan, {"user_id": user_id})
        
        return intent, results

    # Execute the entire pipeline inside ONE event loop
    intent, results = asyncio.run(_run_pipeline())

    # 4. Synthesize (Synchronous)
    synthesizer = Synthesizer()
    message = synthesizer.synthesize(intent, results)

    return {
        "message": message,
        "details": results
    }