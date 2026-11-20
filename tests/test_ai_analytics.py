from sqlalchemy import select, func


from app.models.ai_reply_suggestion import AIReplySuggestion


def test_ai_suggestion_statistics(
    client,
    created_ticket,
    db_session
):
    ticket_id = created_ticket["id"]

    statuses = [
        "pending",
        "approved",
        "rejected",
        "sent"
    ]

    for status in statuses:
        suggestion = AIReplySuggestion(
            ticket_id=ticket_id,
            suggested_reply=f"Test AI reply: {status}",
            status=status
        )

        db_session.add(suggestion)

    db_session.flush()


    response = client.get("/api/v1/ai-analytics/replies")
    print("ANALYTICS RESPONSE:", response.json())

    suggestions = db_session.scalars(
        select(AIReplySuggestion)
    ).all()

    for suggestion in suggestions:
        print(
            "ID:", suggestion.id,
            "STATUS:", repr(suggestion.status),
            "SENT_AT:", getattr(suggestion, "sent_at", None)
        )
    assert response.status_code == 200, response.text

    data = response.json()

    assert data["total_suggestions"] >= 4
    assert data["pending_suggestions"] >= 1
    assert data["approved_suggestions"] >= 1
    assert data["rejected_suggestions"] >= 1
    assert data["sent_suggestions"] >= 1