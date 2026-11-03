"""Impede cadastro repetido do mesmo laboratório e localização.

Revision ID: 0002_unique_labs
Revises: 0001_empty
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_unique_labs"
down_revision = "0001_empty"
branch_labels = None
depends_on = None


def upgrade():
    # lower() funciona em PostgreSQL e SQLite e impede duplicação por diferença de caixa.
    # Uma base existente com duplicatas precisa ser corrigida antes de aplicar esta mudança.
    op.create_index(
        "uq_laboratories_name_location_ci", "laboratories",
        [sa.text("lower(name)"), sa.text("lower(location)")], unique=True,
    )


def downgrade():
    op.drop_index("uq_laboratories_name_location_ci", table_name="laboratories")
