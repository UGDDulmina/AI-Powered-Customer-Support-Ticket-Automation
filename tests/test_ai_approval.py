from sqlalchemy import select, func
from app.models.ticket_message import TicketMessage

def test_approve_ai_suggestion(
    client,
    created_ai_suggestion,
    create_support_agent
):

    suggestion_id = created_ai_suggestion.id
    agent_id = create_support_agent["id"]

    response = client.patch(
        f"/api/v1/tickets/{suggestion_id}/review",
        json={
            "action": "approve",
            "agent_id": agent_id,
            "edited_reply": None
        }
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["status"] == "approved"
    assert data["id"] == suggestion_id
    assert data["reviewed_by_agent_id"] == agent_id
    assert data["reviewed_at"] is not None

def test_reject_ai_suggestion(
    client,
    created_ai_suggestion,
    create_support_agent
):

    suggestion_id = created_ai_suggestion.id
    agent_id = create_support_agent["id"]

    response = client.patch(
        f"/api/v1/tickets/{suggestion_id}/review",
        json={
            "action": "reject",
            "agent_id": agent_id,
            "edited_reply": None
        }
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["id"] == suggestion_id
    assert data["status"] == "rejected"
    assert data["reviewed_by_agent_id"] == agent_id
    assert data["edited_reply"] is None
    assert data["reviewed_at"] is not None

def test_reject_ai_suggestion_with_edited_reply(
    client,
    created_ai_suggestion,
    create_support_agent,
    db_session
):

        suggestion_id = created_ai_suggestion.id
        agent_id = create_support_agent["id"]
    
        response = client.patch(
            f"/api/v1/tickets/{suggestion_id}/review",
            json={
                "action": "reject",
                "agent_id": agent_id,
                "edited_reply": "This is an edited reply"
            }
        )
    
        assert response.status_code == 422, response.text

        db_session.refresh(created_ai_suggestion)

        
        assert created_ai_suggestion.status == "pending"
        assert created_ai_suggestion.edited_reply is None
        assert created_ai_suggestion.reviewed_by_agent_id is None
        assert created_ai_suggestion.reviewed_at is None


def test_cannot_review_approved_suggestion_again(
    client,
    created_ai_suggestion,
    create_support_agent
):
    suggestion_id = created_ai_suggestion.id
    agent_id = create_support_agent["id"]

     
    first_response = client.patch(
        f"/api/v1/tickets/{suggestion_id}/review",
        json={
            "action": "approve",
            "agent_id": agent_id
        }
    )

    assert first_response.status_code == 200, first_response.text
    assert first_response.json()["status"] == "approved"

 
    second_response = client.patch(
        f"/api/v1/tickets/{suggestion_id}/review",
        json={
            "action": "reject",
            "agent_id": agent_id
        }
    )

    assert second_response.status_code == 409, second_response.text
    assert second_response.json()["detail"] == (
        "Suggestion has already been reviewed"
    )

def test_send_approved_ai_reply(
    client,
    created_ai_suggestion,
    create_support_agent,
    db_session
):
    suggestion_id = created_ai_suggestion.id
    agent_id = create_support_agent["id"]

    
    approve_response = client.patch(
        f"/api/v1/tickets/{suggestion_id}/review",
        json={
            "action": "approve",
            "agent_id": agent_id
        }
    )

    assert approve_response.status_code == 200, approve_response.text
    assert approve_response.json()["status"] == "approved"

    
    send_response = client.post(
        f"/api/v1/ai-suggestions/{suggestion_id}/send",
        json={
            "agent_id": agent_id
        }
    )

    assert send_response.status_code == 200, send_response.text

    data = send_response.json()

    
    assert data["suggestion_id"] == suggestion_id
    assert data["ticket_id"] == created_ai_suggestion.ticket_id
    assert data["status"] == "sent"
    assert data["sender_type"] == "AGENT"
    assert isinstance(data["message_id"], int)

    
    db_session.expire_all()

    from app.models.ai_reply_suggestion import AIReplySuggestion
    from app.models.ticket_message import TicketMessage

    suggestion = db_session.get(AIReplySuggestion, suggestion_id)
    message = db_session.get(TicketMessage, data["message_id"])

    assert suggestion.status == "sent"

    assert message is not None
    assert message.ticket_id == suggestion.ticket_id
    assert message.sender_type == "AGENT"
    assert message.content == suggestion.suggested_reply


def test_cannot_send_ai_reply_twice(
    client,
    created_ai_suggestion,
    create_support_agent,
    db_session
):
    suggestion_id = created_ai_suggestion.id
    ticket_id = created_ai_suggestion.ticket_id
    agent_id = create_support_agent["id"]

    
    approve_response = client.patch(
        f"/api/v1/tickets/{suggestion_id}/review",
        json={
            "action": "approve",
            "agent_id": agent_id
        }
    )

    assert approve_response.status_code == 200, approve_response.text

    
    first_response = client.post(
        f"/api/v1/ai-suggestions/{suggestion_id}/send",
        json={
            "agent_id": agent_id
        }
    )

    assert first_response.status_code == 200, first_response.text
    assert first_response.json()["status"] == "sent"

    message_id = first_response.json()["message_id"]

    
    db_session.expire_all()

    message_count_before = db_session.scalar(
        select(func.count(TicketMessage.id))
        .where(TicketMessage.ticket_id == ticket_id)
    )

    
    second_response = client.post(
        f"/api/v1/ai-suggestions/{suggestion_id}/send",
        json={
            "agent_id": agent_id
        }
    )


    assert second_response.status_code == 409, second_response.text

    assert second_response.json()["detail"] == (
        "Only approved suggestions can be sent"
    )

    
    db_session.expire_all()

    message_count_after = db_session.scalar(
        select(func.count(TicketMessage.id))
        .where(TicketMessage.ticket_id == ticket_id)
    )

    assert message_count_after == message_count_before

    
    message = db_session.get(TicketMessage, message_id)

    assert message is not None
        