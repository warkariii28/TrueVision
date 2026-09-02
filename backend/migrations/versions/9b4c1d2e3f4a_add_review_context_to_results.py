"""add review context to results

Revision ID: 9b4c1d2e3f4a
Revises: 70142068f85c
Create Date: 2026-09-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b4c1d2e3f4a'
down_revision = '70142068f85c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('result', sa.Column('review_purpose', sa.String(length=50), nullable=True))
    op.add_column('result', sa.Column('review_strictness', sa.String(length=30), nullable=True))
    op.add_column('result', sa.Column('recommendation_reason', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('result', 'recommendation_reason')
    op.drop_column('result', 'review_strictness')
    op.drop_column('result', 'review_purpose')