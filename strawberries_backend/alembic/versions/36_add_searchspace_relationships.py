"""Add SearchSpace to SearchSpace relationships (Obsidian-like graph)

Revision ID: '36'
Revises: '35'
Create Date: 2025-01-25 12:00:00.000000

This migration adds support for SearchSpaces to reference other SearchSpaces,
enabling an Obsidian-like graph structure where information can flow between spaces.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "36"
down_revision: str | None = "35"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Create a many-to-many relationship table for SearchSpace references.
    
    This allows SearchSpaces to link to other SearchSpaces, creating a graph
    structure similar to Obsidian where spaces can pull information from
    their linked spaces.
    """
    # Create the association table for SearchSpace relationships
    op.create_table(
        "searchspace_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "source_space_id",
            sa.Integer(),
            nullable=False,
            comment="The SearchSpace that references another",
        ),
        sa.Column(
            "target_space_id",
            sa.Integer(),
            nullable=False,
            comment="The SearchSpace being referenced",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # Primary key
        sa.PrimaryKeyConstraint("id"),
        # Foreign keys
        sa.ForeignKeyConstraint(
            ["source_space_id"],
            ["searchspaces.id"],
            name="fk_searchspace_links_source",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_space_id"],
            ["searchspaces.id"],
            name="fk_searchspace_links_target",
            ondelete="CASCADE",
        ),
        # Unique constraint to prevent duplicate links
        sa.UniqueConstraint(
            "source_space_id",
            "target_space_id",
            name="uq_searchspace_links_source_target",
        ),
        # Check constraint to prevent self-referencing
        sa.CheckConstraint(
            "source_space_id != target_space_id",
            name="chk_searchspace_no_self_reference",
        ),
    )
    
    # Create indexes for efficient querying
    op.create_index(
        "ix_searchspace_links_source_space_id",
        "searchspace_links",
        ["source_space_id"],
    )
    op.create_index(
        "ix_searchspace_links_target_space_id",
        "searchspace_links",
        ["target_space_id"],
    )


def downgrade() -> None:
    """Remove SearchSpace relationship table."""
    # Drop indexes
    op.drop_index("ix_searchspace_links_target_space_id", table_name="searchspace_links")
    op.drop_index("ix_searchspace_links_source_space_id", table_name="searchspace_links")
    
    # Drop table
    op.drop_table("searchspace_links")
