# 📋 API Specification

**Base URL:** `http://localhost:8000/api/v1`

---

## POST /query

Submit a natural language orchestration request.

### Request

```json
{
  "query": "Cancel my Turkish Airlines flight"
}
```

### Response

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## GET /query/{task_id}

Retrieve execution status and results.

### Response (Pending)

```json
{
  "status": "pending"
}
```

### Response (Completed)

```json
{
  "status": "completed",
  "result": {
    "message": "I found your Turkish Airlines booking TK1234 scheduled on 2026-03-09 and drafted a cancellation email to support@airline.com.",
    "details": {
      "search_gmail_for_booking": {
        "status": "found",
        "email_id": "06bdfd87-7b30-4378-b6c2-8960d4f5ec2d",
        "subject": "Turkish Airlines Flight TK1234 Confirmed",
        "booking_reference": "TK1234",
        "method": "hybrid"
      },
      "find_calendar_event": {
        "status": "found",
        "event_id": "event-123",
        "title": "Istanbul → NYC Flight TK1234",
        "start_time": "2026-03-09T10:30:00Z"
      },
      "draft_cancellation_email": {
        "status": "drafted",
        "to": "support@airline.com",
        "subject": "Cancellation Request - Turkish Airlines",
        "body": "Please cancel my Turkish Airlines booking TK1234 scheduled on 2026-03-09.\nKindly confirm the cancellation."
      }
    }
  }
}
```

### Response (Failed)

```json
{
  "status": "failed",
  "error": "Intent classification failed"
}
```

---

## Error Handling

| Status Code | Scenario |
|---|---|
| 422 | Validation error (missing/invalid query field) |
| 500 | Internal server error |
| 404 | Task ID not found |

Task-level failures (e.g., no email found) are returned in the `status: completed` response with step details showing `status: not_found`.