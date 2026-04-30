"""Add UserDocument and vector extension

Revision ID: 7d1f6f6dde12
Revises: 
Create Date: 2026-04-30 15:20:38.872116
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '7d1f6f6dde12'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        
        op.create_table('user_documents',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('embedding', sa.String(), nullable=True),  # using sa.String to bypass SA reflection issues, vector extension will handle it if we used raw SQL, but we'll use sa.String for SQLite fallback. Wait, actually, let's just use sa.String for the migration definition. The model handles the vector cast.
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        if conn.dialect.name == "postgresql":
            op.execute("ALTER TABLE user_documents ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector;")
        op.create_index(op.f('ix_user_documents_user_id'), 'user_documents', ['user_id'], unique=False)
    else:
        op.create_table('user_documents',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('embedding', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_user_documents_user_id'), 'user_documents', ['user_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_user_documents_user_id'), table_name='user_documents')
    op.drop_table('user_documents')
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("DROP EXTENSION IF EXISTS vector")
