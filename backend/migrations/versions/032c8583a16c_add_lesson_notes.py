"""add lesson notes

Revision ID: 032c8583a16c
Revises: d6d733d28027
Create Date: 2026-10-09 13:47:43.294723

"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = "032c8583a16c"
down_revision = "d6d733d28027"
branch_labels = None
depends_on = None


def upgrade():
    # Create the lesson_note table.
    op.create_table(
        "lesson_note",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "learner_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "lesson_id",
            sa.String(length=80),
            nullable=False
        ),

        sa.Column(
            "content",
            sa.Text(),
            nullable=False
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False
        ),

        sa.ForeignKeyConstraint(
            ["learner_id"],
            ["learner.id"]
        ),

        sa.ForeignKeyConstraint(
            ["lesson_id"],
            ["lesson.id"]
        ),

        sa.PrimaryKeyConstraint("id"),

        sa.UniqueConstraint(
            "learner_id",
            "lesson_id",
            name="uq_lesson_note"
        )
    )

    # Index for retrieving a learner's notes.
    op.create_index(
        "ix_lesson_note_learner_id",
        "lesson_note",
        ["learner_id"],
        unique=False
    )

    # Index for retrieving notes for a lesson.
    op.create_index(
        "ix_lesson_note_lesson_id",
        "lesson_note",
        ["lesson_id"],
        unique=False
    )


def downgrade():
    # Remove the indexes created by this migration.
    op.drop_index(
        "ix_lesson_note_lesson_id",
        table_name="lesson_note"
    )

    op.drop_index(
        "ix_lesson_note_learner_id",
        table_name="lesson_note"
    )

    # Remove the lesson_note table.
    op.drop_table("lesson_note")