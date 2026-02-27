"""Synthesizer composes prompts and responses from an LLM.
Keep this small and testable; swap the backend easily.
"""

class Synthesizer:
    """Compose natural language responses from execution results."""

    def synthesize(self, intent: dict, results: dict) -> str:
        """Synthesize a response from intent and execution results.

        Args:
            intent: Intent dict with entities (airline, etc.)
            results: Results dict with step outcomes

        Returns:
            Natural language response string.
        """
        entities = intent.get("entities", {})
        airline = entities.get("airline", "").strip()

        # Extract from nested results structure
        gmail_result = results.get("search_gmail_for_booking", {})
        gcal_result = results.get("find_calendar_event", {})
        email_result = results.get("draft_cancellation_email", {})

        booking_reference = gmail_result.get("booking_reference")
        event_start_time = gcal_result.get("start_time")
        recipient = email_result.get("to")

        # Format event_start_time if present
        date_str = None
        if event_start_time:
            if hasattr(event_start_time, "strftime"):
                date_str = event_start_time.strftime("%Y-%m-%d")
            else:
                date_str = str(event_start_time).split()[0]

        # Synthesize response based on available data
        if booking_reference:
            if event_start_time and date_str:
                return (
                    f"I found your {airline} booking {booking_reference} "
                    f"scheduled on {date_str} and drafted a cancellation email to {recipient}."
                )
            else:
                return (
                    f"I found your {airline} booking {booking_reference} "
                    "and drafted a cancellation email."
                )
        else:
            return "I processed your cancellation request."
