from unittest.mock import patch

def test_create_ticket(client, created_customer):

    customer_id = created_customer["id"]

    ticket_data = {
        "customer_id": customer_id,
        "subject": "Unable to log in",
        "description": "I cannot access my account.",
        "priority": "medium"
    }

    with patch(
        "app.api.tickets.generate_ai_suggestion_for_ticket"
    )as mock_ai_worker:

        response = client.post(
            "/api/v1/tickets",
            json=ticket_data
        )

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == customer_id
    assert data["subject"] == ticket_data["subject"]
    assert data["description"] == ticket_data["description"]
    assert "id" in data

    mock_ai_worker.assert_called_once()


def test_get_ticket_by_id(client, created_ticket):

    ticket_id = created_ticket["id"]

    response = client.get(
        f"/api/v1/tickets/{ticket_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == ticket_id
    assert data["subject"] == created_ticket["subject"]
    assert data["customer_id"] == created_ticket["customer_id"]

def test_get_nonexistent_ticket(client):

    response = client.get(
        "/api/v1/tickets/999999999"
    )

    assert response.status_code == 404

def test_update_ticket_status(client, created_ticket):

    ticket_id = created_ticket["id"]

    response = client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        json={"status": "in_progress"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "in_progress"

def test_update_ticket_priority(client, created_ticket):

    ticket_id = created_ticket["id"]

    response = client.patch(
        f"/api/v1/tickets/{ticket_id}/priority",
        json={"priority": "high"}
    )

    assert response.status_code == 200
    
    data = response.json()

    assert data["priority"] == "high"

def test_invalid_ticket_status(client, created_ticket):

    response = client.patch(
        f"/api/v1/tickets/{created_ticket['id']}/status",
        json={"status": "waiting_forever"}
    )

    assert response.status_code in (400, 422)


def test_invalid_ticket_status_transition(client, created_ticket):

    ticket_id = created_ticket["id"]

   
    first_response = client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        json={"status": "in_progress"}
    )

    assert first_response.status_code == 200

   
    second_response = client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        json={"status": "resolved"}
    )

    assert second_response.status_code == 200

   
    third_response = client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        json={"status": "closed"}
    )

    assert third_response.status_code == 200

   
    fourth_response = client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        json={"status": "in_progress"}
    )

    assert fourth_response.status_code in (400, 409)

   
    get_response = client.get(
        f"/api/v1/tickets/{ticket_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["status"] == "closed"