from fastapi import HTTPException


UNSAFE_PHRASES = [
    "i have refunded",
    "your refund has been processed",
    "i have reset your password",
    "your account has been activated",
    "your issue has been resolved"
]


def validate_ai_reply(reply: str) -> dict:

    
    if not reply or not reply.strip():
        return {
            "is_valid": False,
            "reason": "Reply is empty"
        }

    
    if len(reply.strip()) < 20:
        return {
            "is_valid": False,
            "reason": "Reply is too short"
        }

    
    normalized_reply = reply.lower()

    for phrase in UNSAFE_PHRASES:
        if phrase in normalized_reply:
            return {
                "is_valid": False,
                "reason": "Reply contains an unsupported action claim"
            }

    
    return {
        "is_valid": True,
        "reason": "Reply passed validation"
    }