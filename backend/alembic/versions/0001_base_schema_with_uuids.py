"""Initial base schema for users, documents, and evaluations with UUIDs

Revision ID: 0001_base_schema_with_uuids
Revises: None
Create Date: 2025-06-05 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql # Import postgresql dialect for UUID type


# revision identifiers, used by Alembic.
revision: str = '0001_base_schema_with_uuids'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create initial tables with UUIDs."""
    # # Enable uuid-ossp extension if not already enabled in the database
    # op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";') # Commented out for local SQLite

    op.create_table('users',
    sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('full_name', sa.String(), nullable=True),
    sa.Column('role', sa.String(), nullable=False, server_default='grantee'),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
    sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    op.create_table('documents',
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('organization', sa.String(), nullable=False),
    sa.Column('filename', sa.String(), nullable=False),
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('grantee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
    sa.Column('assigned_reviewer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    op.create_index(op.f('ix_documents_title'), 'documents', ['title'], unique=False)

    op.create_table('evaluations',
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('document_id', sa.Integer(), sa.ForeignKey("documents.id"), nullable=False),
    sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
    sa.Column('comment', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluations_id'), 'evaluations', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema: Drop tables."""
    op.drop_index(op.f('ix_evaluations_id'), table_name='evaluations')
    op.drop_table('evaluations')
    op.drop_index(op.f('ix_documents_title'), table_name='documents')
    op.drop_index(op.f('ix_documents_id'), table_name='documents')
    op.drop_table('documents')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
