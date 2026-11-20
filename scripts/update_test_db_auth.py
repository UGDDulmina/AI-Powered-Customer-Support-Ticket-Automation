
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is not configured")

engine = create_engine(TEST_DATABASE_URL)

if engine.url.database != "ai_support_test_db":
    raise RuntimeError(
        "Refusing to modify a database other than ai_support_test_db"
    )

with engine.begin() as connection:
    inspector = inspect(connection)

    columns = {
        column["name"]
        for column in inspector.get_columns("support_agents")
    }

    if "password_hash" not in columns:
        connection.execute(
            text(
                "ALTER TABLE support_agents "
                "ADD COLUMN password_hash VARCHAR(255)"
            )
        )
        print("Added password_hash column")

    if "role" not in columns:
        connection.execute(
            text(
                "ALTER TABLE support_agents "
                "ADD COLUMN role VARCHAR(20) "
                "NOT NULL DEFAULT 'agent'"
            )
        )
        print("Added role column")

print("Test database authentication columns are ready")
