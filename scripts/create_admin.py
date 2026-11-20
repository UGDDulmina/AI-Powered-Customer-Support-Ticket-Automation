import getpass

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.support_agent import SupportAgent
from app.core.security import hash_password


def main():
    with SessionLocal() as db:
        existing_admin = db.scalar(
            select(SupportAgent).where(
                SupportAgent.role == "admin"
            )
        )

        if existing_admin:
            print("An administrator already exists.")
            return

        name = input("Admin name: ").strip()
        email = input("Admin email: ").strip().lower()
        password = getpass.getpass("Admin password: ")

        if len(name) < 2:
            raise ValueError("Name must contain at least 2 characters")

        if len(password) < 12:
            raise ValueError("Password must contain at least 12 characters")

        existing_email = db.scalar(
            select(SupportAgent).where(
                SupportAgent.email == email
            )
        )

        if existing_email:
            raise ValueError("Email already exists")

        admin = SupportAgent(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )

        db.add(admin)
        db.commit()

        print("Administrator created successfully")


if __name__ == "__main__":
    main()