"""add authentication fields to support agents

Revision ID: fe437640329f
Revises: 11172d7e285b
Create Date: 2026-11-20 07:27:44.940866

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe437640329f'
down_revision: Union[str, Sequence[str], None] = '11172d7e285b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "support_agents",
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=True
        )
    )

    op.add_column(
        "support_agents",
        sa.Column(
            "role",
            sa.String(length=20),
            server_default="agent",
            nullable=False
        )
    )

    op.create_check_constraint(
        "ck_support_agents_role",
        "support_agents",
        "role IN ('admin', 'agent')"
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_support_agents_role",
        "support_agents",
        type_="check"
    )

    op.drop_column("support_agents", "role")
    op.drop_column("support_agents", "password_hash")
