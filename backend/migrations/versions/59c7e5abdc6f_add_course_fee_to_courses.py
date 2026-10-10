"""add course fee to courses

Revision ID: 59c7e5abdc6f
Revises: ebabc274ce0f
Create Date: 2026-10-05 17:15:58.275867

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '59c7e5abdc6f'
down_revision = 'ebabc274ce0f'
branch_labels = None
depends_on = None


def upgrade():
    # Add course_fee with a database default of 0 so
    # existing courses can be updated safely.
    with op.batch_alter_table('course', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'course_fee',
                sa.Float(),
                nullable=False,
                server_default='0'
            )
        )


def downgrade():
    with op.batch_alter_table('course', schema=None) as batch_op:
        batch_op.drop_column('course_fee')