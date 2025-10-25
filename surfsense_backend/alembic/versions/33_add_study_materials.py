"""Add study_materials table

Revision ID: 33
Revises: 32
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "33"
down_revision: str | None = "32"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - add study_materials table."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS study_materials (
            id SERIAL PRIMARY KEY,
            search_space_id INTEGER NOT NULL REFERENCES search_spaces(id) ON DELETE CASCADE,
            document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,

            material_type VARCHAR(20) NOT NULL,
            question TEXT NOT NULL,
            answer TEXT,
            options JSONB,

            times_attempted INTEGER DEFAULT 0,
            times_correct INTEGER DEFAULT 0,
            last_attempted_at TIMESTAMP,

            created_at TIMESTAMP DEFAULT NOW()
        )
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_study_materials_space
        ON study_materials(search_space_id, material_type)
        """
    )


def downgrade() -> None:
    """Downgrade schema - drop study_materials table."""
    op.execute("DROP TABLE IF EXISTS study_materials CASCADE;")
