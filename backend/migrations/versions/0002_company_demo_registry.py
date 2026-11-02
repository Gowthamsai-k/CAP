"""Add an isolated G Inc demo company document registry."""
from alembic import op
import sqlalchemy as sa

revision = "0002_company_demo"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "company_documents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("company_id", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("document_type", sa.String(length=80), nullable=False),
        sa.Column("chunks_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_company_documents_company_id", "company_documents", ["company_id"])
    op.create_index("ix_company_documents_title", "company_documents", ["title"])
    op.create_index("ix_company_documents_content_hash", "company_documents", ["content_hash"])
    op.create_table(
        "company_sections",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("company_document_id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=80), nullable=False),
        sa.Column("section", sa.String(length=160)),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_company_sections_company_document_id", "company_sections", ["company_document_id"])
    op.create_index("ix_company_sections_company_id", "company_sections", ["company_id"])
    op.create_index("ix_company_sections_section", "company_sections", ["section"])

def downgrade():
    op.drop_index("ix_company_sections_section", table_name="company_sections")
    op.drop_index("ix_company_sections_company_id", table_name="company_sections")
    op.drop_index("ix_company_sections_company_document_id", table_name="company_sections")
    op.drop_table("company_sections")
    op.drop_index("ix_company_documents_content_hash", table_name="company_documents")
    op.drop_index("ix_company_documents_title", table_name="company_documents")
    op.drop_index("ix_company_documents_company_id", table_name="company_documents")
    op.drop_table("company_documents")
