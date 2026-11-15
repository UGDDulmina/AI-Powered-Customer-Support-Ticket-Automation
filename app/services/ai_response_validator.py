from fastapi import HTTPException


UNSAFE_PHRASES = [
    "i have refunded",
    "your refund has been processed",
    "i have reset your password",
    "your account has been activated",
    "your issue has been resolved"
]


def validate_ai_reply(reply: str) -> dict:

    # Rule 1: Check empty reply
    if not reply or not reply.strip():
        return {
            "is_valid": False,
            "reason": "Reply is empty"
        }

    # Rule 2: Check minimum length
    if len(reply.strip()) < 20:
        return {
            "is_valid": False,
            "reason": "Reply is too short"
        }

    # Rule 3: Check unsafe phrases
    normalized_reply = reply.lower()

    for phrase in UNSAFE_PHRASES:
        if phrase in normalized_reply:
            return {
                "is_valid": False,
                "reason": "Reply contains an unsupported action claim"
            }

    # Rule 4: Return success
    return {
        "is_valid": True,
        "reason": "Reply passed validation"
    }