from app.services.ticket_categorizer import categorize_ticket

tests = [
    (
        "Payment failed",
        "My payment was charged twice and the invoice is missing",
        "billing"
    ),
    (
        "Login problem",
        "I forgot my password",
        "account"
    ),
    (
        "Application crash",
        "The server shows an error",
        "technical"
    ),
    (
        "Delivery delayed",
        "My package tracking is not updating",
        "shipping"
    ),
    (
        "Return request",
        "I want a refund and my money back",
        "refund"
    ),
    (
        "General question",
        "I need more information",
        "general"
    )
]

for subject, description, expected in tests:

    actual = categorize_ticket(subject, description)

    assert actual == expected, (
        f"Expected {expected}, but got {actual}"
    )

print("All categorization tests passed!")