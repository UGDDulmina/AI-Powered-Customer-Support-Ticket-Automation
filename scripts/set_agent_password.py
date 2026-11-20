
import getpass

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.support_agent import SupportAgent
from app.core.security import hash_password


def main():
    email = input("Agent email: ").strip().lower()
    password = getpass.getpass("New password: ")

    if len(password) < 12:
        raise ValueError(
            "Password must contain at least 12 characters"
        )

    with SessionLocal() as db:
        agent = db.scalar(
            select(SupportAgent).where(
                SupportAgent.email == email
            )
        )

        if agent is None:
            raise ValueError("Agent not found")

        agent.password_hash = hash_password(password)

        db.commit()

        print("Agent password configured successfully")


if __name__ == "__main__":
    main()
