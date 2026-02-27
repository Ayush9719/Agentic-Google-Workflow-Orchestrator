"""Intent classification using LLM.

Converts natural language queries into structured intent JSON.
Current implementation uses mocked LLM responses for development.
Later, wire this to OpenAI chat completions with temperature=0.
"""
import json
from typing import Any


class IntentClassifier:
    """Classify user queries into structured intent with services, entities, and steps."""

    SYSTEM_PROMPT = """You are an intent classifier for a Google Workspace Orchestration system.

Analyze the user query and return a JSON object with exactly this structure:
{
    "services": ["gmail", "gcal", "gdrive"],  # which services are needed
    "intent": "description of what to do",     # high-level intent
    "entities": {                              # extracted entities
        "key": "value"
    },
    "steps": [                                 # execution steps
        "step 1",
        "step 2"
    ]
}

Services: gmail (email), gcal (calendar), gdrive (file storage).
Extract relevant entities like dates, email addresses, file names, etc.
Steps should be in logical order for execution.

Return ONLY valid JSON. No markdown, no explanation."""

    async def classify(self, query: str) -> dict[str, Any]:
        """Classify a natural language query into structured intent.

        Args:
            query: Natural language query from user

        Returns:
            Dictionary with keys: services, intent, entities, steps
        """
        # TODO: Replace with actual OpenAI call:
        # response = openai.ChatCompletion.create(
        #     model="gpt-4",
        #     temperature=0,
        #     messages=[
        #         {"role": "system", "content": self.SYSTEM_PROMPT},
        #         {"role": "user", "content": query}
        #     ]
        # )
        # return json.loads(response["choices"][0]["message"]["content"])

        # Mocked responses for development
        query_lower = query.lower()

        if "cancel" in query_lower and "flight" in query_lower:
            return {
                "services": ["gmail", "gcal"],
                "intent": "cancel_flight",
                "entities": {
                    "airline": "Turkish Airlines"
                },
                "steps": [
                    "search_gmail_for_booking",
                    "find_calendar_event",
                    "draft_cancellation_email"
                ],
            }

        if "meeting" in query_lower:
            return {
                "services": ["gcal", "gmail"],
                "intent": "manage_meeting",
                "entities": {},
                "steps": [
                    "search_calendar_event",
                    "search_related_emails"
                ],
            }

        if "email" in query_lower:
            return {
                "services": ["gmail"],
                "intent": "manage_email",
                "entities": {},
                "steps": [
                    "search_gmail"
                ],
            }

        return {
            "services": [],
            "intent": "unknown",
            "entities": {},
            "steps": [],
        }