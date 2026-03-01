import pytest
import requests
import time
import uuid

BASE_URL = "http://localhost:8000/api/v1"

def submit_and_poll(query: str, max_retries: int = 15, sleep_time: float = 1.0) -> dict:
    """Helper to submit a query and poll the live Docker API until completion with verbose logging."""
    print(f"\n[➡] Submitting query: '{query}'")
    
    payload = {
        "query": query,
        "conversation_id": str(uuid.uuid4())
    }
    
    # 1. Submit the query
    post_response = requests.post(f"{BASE_URL}/query", json=payload)
    post_response.raise_for_status()
    task_id = post_response.json().get("task_id")
    
    assert task_id is not None, "API did not return a task_id"
    print(f"[✅] Task created successfully. Task ID: {task_id}")

    # 2. Poll for the result
    for attempt in range(1, max_retries + 1):
        print(f"  [⏳] Polling attempt {attempt}/{max_retries}...")
        get_response = requests.get(f"{BASE_URL}/query/{task_id}")
        get_response.raise_for_status()
        data = get_response.json()
        
        status = data.get("status")
        
        if status in ["completed", "failed"]:
            print(f"\n[🎉] Task finished with status: {status.upper()}")
            
            # Pretty-print the final response message if it exists
            if status == "completed":
                message = data.get("result", {}).get("message", "No message provided")
                print(f"[💬] Final Response: {message}")
                
            return data
            
        # Wait before polling again
        time.sleep(sleep_time)
        
    print(f"\n[❌] Task {task_id} timed out.")
    pytest.fail(f"Task {task_id} timed out after {max_retries * sleep_time} seconds")

class TestLiveAgenticOrchestrator:
    """Integration tests hitting the live Dockerized orchestrator."""

    @pytest.mark.parametrize("query, expected_steps", [
        # --- Single Service [cite: 65] ---
        (
            "What's on my calendar next week?",
            ["find_calendar_event"]
        ),
        (
            "Find emails from sarah@company.com about the budget",
            ["search_gmail"]
        ),
        (
            "Show me PDFs in Drive from last month",
            ["search_drive_files"]
        ),

        # --- Multi-Service [cite: 69] ---
        (
            "Cancel my Turkish Airlines flight",
            ["search_gmail_for_booking", "find_calendar_event", "draft_cancellation_email"]
        ),
        (
            "Prepare for tomorrow's meeting with Acme Corp",
            ["find_calendar_event", "search_gmail", "search_drive_files"]
        ),
        (
            "Find events next week that conflict with my out-of-office doc",
            ["search_drive_files", "find_calendar_event"]
        ),

        # --- Hard Cases [cite: 73] ---
        (
            "Move the meeting with John",
            ["find_calendar_event"]
        ),
        (
            "That email about the proposal",
            # Requires conversation context: We will trigger a Gmail search
            ["search_gmail"]
        ),
        (
            "Next Tuesday",
            # Temporal reasoning: Trigger calendar search
            ["find_calendar_event"]
        ),
    ])
    def test_e2e_orchestration_queries(self, query, expected_steps):
        """Test that the live API routes queries and executes the correct DAG steps."""
        
        result_data = submit_and_poll(query)
        
        assert result_data["status"] == "completed", f"Task failed: {result_data.get('error')}"
        
        details = result_data["result"].get("details", {})
        
        # Verify the DAG executed the expected steps
        for step in expected_steps:
            assert step in details, f"Expected step '{step}' was not executed for query: {query}"


    def test_context_propagation_turkish_airlines(self):
        """Verify cross-agent context propagation in the live environment."""
        
        result_data = submit_and_poll("Cancel my Turkish Airlines flight")
        assert result_data["status"] == "completed"
        
        details = result_data["result"].get("details", {})

        # 1. Assert Gmail found the booking reference
        gmail_step = details.get("search_gmail_for_booking", {})
        assert gmail_step.get("status") == "found"
        assert "TK1234" in gmail_step.get("booking_reference", "")

        # 2. Assert the Draft Email agent received that context
        draft_step = details.get("draft_cancellation_email", {})
        assert draft_step.get("status") == "drafted"
        assert "TK1234" in draft_step.get("body", "")