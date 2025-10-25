"""Add tasks table for work mode

Revision ID: 34
Revises: 33
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "34"
down_revision: str | None = "33"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - add tasks table."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            search_space_id INTEGER NOT NULL REFERENCES search_spaces(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,

            title VARCHAR(500) NOT NULL,
            description TEXT,

            source_type VARCHAR(50),
            external_id VARCHAR(255),
            external_url TEXT,
            external_metadata JSONB,

            status VARCHAR(20) DEFAULT 'UNDONE',
            priority VARCHAR(20),

            due_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            completed_at TIMESTAMP,

            linked_chat_ids INTEGER[],
            linked_document_ids INTEGER[]
        )
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS idx_tasks_space_status ON tasks(search_space_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date) WHERE due_date IS NOT NULL")
    op.execute("CREATE INDEX IF NOT EXISTS idx_tasks_external ON tasks(source_type, external_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id)")


def downgrade() -> None:
    """Downgrade schema - drop tasks table."""
    op.execute("DROP TABLE IF EXISTS tasks CASCADE;")
