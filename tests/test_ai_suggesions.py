from unittest.mock import patch


def test_generate_ai_suggestion(client, created_ticket):

    ticket_id = created_ticket["id"]

    fake_reply = (
        "Thank you for contacting support. "
        "Please try resetting your password."
    )

    with patch(
        "app.api.tickets.generate_ticket_reply",
        return_value=fake_reply
    ) as mock_generate:
        

        response = client.post(
            f"/api/v1/tickets/{ticket_id}/suggest-reply"
        )

        print("STATUS:", response.status_code)
        print("BODY:", response.text)

        assert response.status_code == 200

        data = response.json()

        assert data["ticket_id"] == ticket_id
        assert data["status"] == "pending"
        assert data["suggested_reply"] == fake_reply

        mock_generate.assert_called_once()



    