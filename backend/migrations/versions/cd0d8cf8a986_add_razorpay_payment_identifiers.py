"""add Razorpay payment identifiers

Revision ID: cd0d8cf8a986
Revises: 032c8583a16c
Create Date: 2026-10-10 18:43:07.690283

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "cd0d8cf8a986"
down_revision = "032c8583a16c"
branch_labels = None
depends_on = None


def upgrade():
    # Add Razorpay order and payment identifiers.
    op.add_column(
        "payment",
        sa.Column(
            "razorpay_order_id",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "payment",
        sa.Column(
            "razorpay_payment_id",
            sa.String(length=100),
            nullable=True,
        ),
    )

    # Create unique indexes to prevent duplicate identifiers.
    op.create_index(
        "ix_payment_razorpay_order_id",
        "payment",
        ["razorpay_order_id"],
        unique=True,
    )

    op.create_index(
        "ix_payment_razorpay_payment_id",
        "payment",
        ["razorpay_payment_id"],
        unique=True,
    )


def downgrade():
    # Remove the Razorpay indexes and columns.
    op.drop_index(
        "ix_payment_razorpay_payment_id",
        table_name="payment",
    )

    op.drop_index(
        "ix_payment_razorpay_order_id",
        table_name="payment",
    )

    op.drop_column(
        "payment",
        "razorpay_payment_id",
    )

    op.drop_column(
        "payment",
        "razorpay_order_id",
    )