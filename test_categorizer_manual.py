from app.services.ticket_priprity_predictor import predict_ticket_priority

tests = [
    (
        "Production server down",
        "The entire system is unavailable",
        "urgent"
    ),
    (
        "Payment failed",
        "Customers cannot pay",
        "high"
    ),
    (
        "Login issue",
        "I need a password reset",
        "medium"
    ),
    (
        "Profile picture",
        "I want to change my profile picture",
        "low"
    ),
    (
        "Customer question",
        "I would like to know more about your services",
        "medium"
    )
]

for subject, description, expected in tests:
    actual = predict_ticket_priority(subject, description)

    assert actual == expected, (
        f"Expected {expected}, but got {actual}"
    )

print("All priority prediction tests passed!")