"""add mixed exams question bank and invites

Revision ID: 049ca4ab2045
Revises: 59c7e5abdc6f
Create Date: 2026-10-06 19:57:21.243960

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '049ca4ab2045'
down_revision = '59c7e5abdc6f'
branch_labels = None
depends_on = None


def upgrade():
    # ========================================================
    # QUESTION BANK
    # ========================================================

    op.create_table(
        'question_bank',

        sa.Column(
            'id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'trainer_id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'title',
            sa.String(length=200),
            nullable=False
        ),

        sa.Column(
            'description',
            sa.Text(),
            nullable=True
        ),

        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=True
        ),

        sa.ForeignKeyConstraint(
            ['trainer_id'],
            ['trainer.id']
        ),

        sa.PrimaryKeyConstraint('id')
    )


    # ========================================================
    # MIXED EXAM
    # ========================================================

    op.create_table(
        'mixed_exam',

        sa.Column(
            'id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'title',
            sa.String(length=200),
            nullable=False
        ),

        sa.Column(
            'description',
            sa.Text(),
            nullable=True
        ),

        sa.Column(
            'course_id',
            sa.String(length=80),
            nullable=False
        ),

        sa.Column(
            'trainer_id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'duration_minutes',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'total_marks',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'status',
            sa.String(length=20),
            nullable=False
        ),

        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=True
        ),

        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=True
        ),

        sa.ForeignKeyConstraint(
            ['course_id'],
            ['course.id']
        ),

        sa.ForeignKeyConstraint(
            ['trainer_id'],
            ['trainer.id']
        ),

        sa.PrimaryKeyConstraint('id')
    )


    # ========================================================
    # QUESTION BANK ITEM
    # ========================================================

    op.create_table(
        'question_bank_item',

        sa.Column(
            'id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'bank_id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'question_type',
            sa.String(length=20),
            nullable=False
        ),

        sa.Column(
            'question_text',
            sa.Text(),
            nullable=False
        ),

        sa.Column(
            'option_a',
            sa.String(length=500),
            nullable=True
        ),

        sa.Column(
            'option_b',
            sa.String(length=500),
            nullable=True
        ),

        sa.Column(
            'option_c',
            sa.String(length=500),
            nullable=True
        ),

        sa.Column(
            'option_d',
            sa.String(length=500),
            nullable=True
        ),

        sa.Column(
            'correct_answer',
            sa.String(length=10),
            nullable=True
        ),

        sa.Column(
            'coding_description',
            sa.Text(),
            nullable=True
        ),

        sa.Column(
            'starter_code',
            sa.Text(),
            nullable=True
        ),

        sa.Column(
            'language',
            sa.String(length=30),
            nullable=True
        ),

        sa.Column(
            'difficulty',
            sa.String(length=20),
            nullable=True
        ),

        sa.Column(
            'marks',
            sa.Integer(),
            nullable=True
        ),

        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=True
        ),

        sa.ForeignKeyConstraint(
            ['bank_id'],
            ['question_bank.id']
        ),

        sa.PrimaryKeyConstraint('id')
    )


    # ========================================================
    # MIXED EXAM INVITE
    # ========================================================

    op.create_table(
        'mixed_exam_invite',

        sa.Column(
            'id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'exam_id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'invite_code',
            sa.String(length=80),
            nullable=False
        ),

        sa.Column(
            'candidate_name',
            sa.String(length=200),
            nullable=True
        ),

        sa.Column(
            'candidate_email',
            sa.String(length=255),
            nullable=True
        ),

        sa.Column(
            'expires_at',
            sa.DateTime(),
            nullable=True
        ),

        sa.Column(
            'max_attempts',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False
        ),

        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=True
        ),

        sa.ForeignKeyConstraint(
            ['exam_id'],
            ['mixed_exam.id']
        ),

        sa.PrimaryKeyConstraint('id')
    )


    op.create_index(
        'ix_mixed_exam_invite_invite_code',
        'mixed_exam_invite',
        ['invite_code'],
        unique=True
    )


    # ========================================================
    # MIXED EXAM SECTION
    # ========================================================

    op.create_table(
        'mixed_exam_section',

        sa.Column(
            'id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'exam_id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'title',
            sa.String(length=200),
            nullable=False
        ),

        sa.Column(
            'section_type',
            sa.String(length=20),
            nullable=False
        ),

        sa.Column(
            'order_index',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'marks',
            sa.Integer(),
            nullable=False
        ),

        sa.ForeignKeyConstraint(
            ['exam_id'],
            ['mixed_exam.id']
        ),

        sa.PrimaryKeyConstraint('id')
    )


    # ========================================================
    # MIXED EXAM QUESTION
    # ========================================================

    op.create_table(
        'mixed_exam_question',

        sa.Column(
            'id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'section_id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'question_type',
            sa.String(length=20),
            nullable=False
        ),

        sa.Column(
            'question_bank_item_id',
            sa.Integer(),
            nullable=True
        ),

        sa.Column(
            'question_text',
            sa.Text(),
            nullable=False
        ),

        sa.Column(
            'option_a',
            sa.String(length=500),
            nullable=True
        ),

        sa.Column(
            'option_b',
            sa.String(length=500),
            nullable=True
        ),

        sa.Column(
            'option_c',
            sa.String(length=500),
            nullable=True
        ),

        sa.Column(
            'option_d',
            sa.String(length=500),
            nullable=True
        ),

        sa.Column(
            'correct_answer',
            sa.String(length=10),
            nullable=True
        ),

        sa.Column(
            'coding_description',
            sa.Text(),
            nullable=True
        ),

        sa.Column(
            'starter_code',
            sa.Text(),
            nullable=True
        ),

        sa.Column(
            'language',
            sa.String(length=30),
            nullable=True
        ),

        sa.Column(
            'marks',
            sa.Integer(),
            nullable=True
        ),

        sa.Column(
            'order_index',
            sa.Integer(),
            nullable=True
        ),

        sa.ForeignKeyConstraint(
            ['question_bank_item_id'],
            ['question_bank_item.id']
        ),

        sa.ForeignKeyConstraint(
            ['section_id'],
            ['mixed_exam_section.id']
        ),

        sa.PrimaryKeyConstraint('id')
    )


def downgrade():

    # ========================================================
    # REMOVE MIXED EXAM QUESTION
    # ========================================================

    op.drop_table(
        'mixed_exam_question'
    )


    # ========================================================
    # REMOVE MIXED EXAM SECTION
    # ========================================================

    op.drop_table(
        'mixed_exam_section'
    )


    # ========================================================
    # REMOVE INVITE INDEX
    # ========================================================

    op.drop_index(
        'ix_mixed_exam_invite_invite_code',
        table_name='mixed_exam_invite'
    )


    # ========================================================
    # REMOVE INVITES
    # ========================================================

    op.drop_table(
        'mixed_exam_invite'
    )


    # ========================================================
    # REMOVE QUESTION BANK ITEMS
    # ========================================================

    op.drop_table(
        'question_bank_item'
    )


    # ========================================================
    # REMOVE MIXED EXAMS
    # ========================================================

    op.drop_table(
        'mixed_exam'
    )


    # ========================================================
    # REMOVE QUESTION BANKS
    # ========================================================

    op.drop_table(
        'question_bank'
    )