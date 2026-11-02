"""Create the initial legal document registry and section tables."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "legal_documents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("jurisdiction", sa.String(length=16)),
        sa.Column("country", sa.String(length=100)),
        sa.Column("domain", sa.String(length=100)),
        sa.Column("industry", sa.String(length=100)),
        sa.Column("authority", sa.String(length=250)),
        sa.Column("document_type", sa.String(length=80)),
        sa.Column("source_url", sa.Text()),
        sa.Column("version", sa.String(length=100)),
        sa.Column("publication_date", sa.Date()),
        sa.Column("effective_from", sa.Date()),
        sa.Column("effective_to", sa.Date()),
        sa.Column("document_status", sa.String(length=40), nullable=False),
        sa.Column("chunks_count", sa.Integer(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("content_hash"),
    )
    op.create_index("ix_legal_documents_title", "legal_documents", ["title"])
    op.create_index("ix_legal_documents_content_hash", "legal_documents", ["content_hash"])
    op.create_index("ix_legal_documents_jurisdiction", "legal_documents", ["jurisdiction"])
    op.create_index("ix_legal_documents_domain", "legal_documents", ["domain"])
    op.create_table(
        "legal_sections",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("section", sa.String(length=160)),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_legal_sections_document_id", "legal_sections", ["document_id"])
    op.create_index("ix_legal_sections_section", "legal_sections", ["section"])

def downgrade():
    op.drop_index("ix_legal_sections_section", table_name="legal_sections")
    op.drop_index("ix_legal_sections_document_id", table_name="legal_sections")
    op.drop_table("legal_sections")
    op.drop_index("ix_legal_documents_domain", table_name="legal_documents")
    op.drop_index("ix_legal_documents_jurisdiction", table_name="legal_documents")
    op.drop_index("ix_legal_documents_content_hash", table_name="legal_documents")
    op.drop_index("ix_legal_documents_title", table_name="legal_documents")
    op.drop_table("legal_documents")
