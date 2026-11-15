from app.services.ai_response_service import generate_ticket_reply

test_cases = [
    {
        "subject": "Login problem",
        "description": "I cannot access my account after resetting my password."
    },
    {
        "subject": "Double payment",
        "description": "My card was charged twice for the same subscription."
    },
    {
        "subject": "Delivery delayed",
        "description": "My package has not arrived after the expected delivery date."
    }
]

for ticket in test_cases:
    reply = generate_ticket_reply(
        subject=ticket["subject"],
        description=ticket["description"]
    )

    print("\nTicket:", ticket["subject"])
    print("AI Reply:", reply)

    assert isinstance(reply, str)
    assert reply.strip()