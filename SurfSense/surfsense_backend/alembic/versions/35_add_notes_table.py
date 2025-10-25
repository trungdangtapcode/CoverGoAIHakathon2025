"""Add notes table

Revision ID: 35
Revises: 34
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "35"
down_revision: str | None = "34"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - add notes table."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            search_space_id INTEGER NOT NULL REFERENCES search_spaces(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

            title VARCHAR(500) NOT NULL,
            content TEXT NOT NULL,

            source_chat_id INTEGER REFERENCES chats(id) ON DELETE SET NULL,

            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS notes_search_idx
        ON notes USING gin(to_tsvector('english', title || ' ' || content));

        CREATE INDEX IF NOT EXISTS idx_notes_space
        ON notes(search_space_id);

        CREATE INDEX IF NOT EXISTS idx_notes_user
        ON notes(user_id);
        """
    )


def downgrade() -> None:
    """Downgrade schema - drop notes table."""
    op.execute("DROP TABLE IF EXISTS notes CASCADE;")
