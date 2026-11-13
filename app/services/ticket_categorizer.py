CATEGORY_KEYWORDS = {
    "billing": [
        "payment",
        "invoice",
        "charged",
        "billing",
        "credit card"
    ],
    "technical": [
        "error",
        "bug",
        "crash",
        "server",
        "not working"
    ],
    "account": [
        "login",
        "password",
        "account",
        "sign in",
        "reset password"
    ],
    "shipping": [
        "delivery",
        "shipping",
        "tracking",
        "package",
        "shipment"
    ],
    "refund": [
        "refund",
        "return",
        "money back",
        "cancel order"
    ]
}

def categorize_ticket(subject: str, description: str) -> str:

    text = f"{subject} {description}".lower()

    category_scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(
            keyword in text 
            for keyword in keywords
            )

        category_scores[category] = score

    best_category = max(
        category_scores,
        key=category_scores.get
    )

    highest_score = category_scores[best_category]

    if highest_score == 0:
     return "general"

    return best_category
            
        