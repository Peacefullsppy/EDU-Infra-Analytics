"""Schema inicial sem qualquer dado inserido.

Revision ID: 0001_empty
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_empty"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(100), nullable=False),
                    sa.Column("email", sa.String(180), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False),
                    sa.Column("role", sa.String(15), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False),
                    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("laboratories", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(100), nullable=False),
                    sa.Column("location", sa.String(160), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False),
                    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("computers", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("hostname", sa.String(100), nullable=False),
                    sa.Column("ip_address", sa.String(45), nullable=True), sa.Column("laboratory_id", sa.Integer(),
                        sa.ForeignKey("laboratories.id", ondelete="RESTRICT"), nullable=False),
                    sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
                    sa.Column("cpu_percent", sa.Integer(), nullable=True), sa.Column("ram_percent", sa.Integer(), nullable=True),
                    sa.Column("disk_percent", sa.Integer(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_computers_hostname", "computers", ["hostname"], unique=True)
    op.create_index("ix_computers_laboratory_id", "computers", ["laboratory_id"])
    op.create_table("audit_logs", sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
                    sa.Column("action", sa.String(60), nullable=False), sa.Column("entity", sa.String(60), nullable=False),
                    sa.Column("entity_id", sa.Integer(), nullable=True), sa.Column("detail", sa.Text(), nullable=True),
                    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))


def downgrade():
    op.drop_table("audit_logs")
    op.drop_index("ix_computers_laboratory_id", table_name="computers")
    op.drop_index("ix_computers_hostname", table_name="computers")
    op.drop_table("computers")
    op.drop_table("laboratories")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
