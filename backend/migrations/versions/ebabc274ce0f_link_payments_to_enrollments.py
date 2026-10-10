"""link payments to enrollments

Revision ID: ebabc274ce0f
Revises: 5c3df993ab3a
Create Date: 2026-10-05 17:04:01.091955

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ebabc274ce0f'
down_revision = '5c3df993ab3a'
branch_labels = None
depends_on = None


def upgrade():
    # Add the column as nullable first so existing payment records
    # are not broken.
    with op.batch_alter_table('payment', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'enrollment_id',
                sa.Integer(),
                nullable=True
            )
        )

        batch_op.create_foreign_key(
            'fk_payment_enrollment_id',
            'enrollment',
            ['enrollment_id'],
            ['id']
        )


def downgrade():
    with op.batch_alter_table('payment', schema=None) as batch_op:
        batch_op.drop_constraint(
            'fk_payment_enrollment_id',
            type_='foreignkey'
        )

        batch_op.drop_column('enrollment_id')