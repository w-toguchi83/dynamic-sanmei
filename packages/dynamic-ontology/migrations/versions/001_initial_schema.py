"""動的オントロジーエンジン 初期スキーマ.

Revision ID: 001
Revises:
Create Date: 2026-03-01

全テーブルに do_ プレフィックスを付与し、namespace_id でマルチテナント分離。
core/ の 001〜013, 030 マイグレーションを統合した初期スキーマ。

9 テーブル:
  - do_entity_types
  - do_entities
  - do_entity_history
  - do_relationship_types
  - do_relationships
  - do_relationship_history
  - do_indexed_properties
  - do_schema_versions
  - do_schema_proposals
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """初期スキーマを作成する."""

    # =========================================================================
    # 1. do_entity_types -- エンティティタイプ定義（メタスキーマ）
    # =========================================================================
    op.create_table(
        "do_entity_types",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("namespace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("schema_definition", postgresql.JSONB, nullable=False),
        sa.Column("display_property", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "idx_do_entity_types_namespace_id",
        "do_entity_types",
        ["namespace_id"],
    )
    op.create_unique_constraint(
        "uq_do_entity_types_namespace_name",
        "do_entity_types",
        ["namespace_id", "name"],
    )

    # =========================================================================
    # 2. do_relationship_types -- リレーションシップタイプ定義
    # =========================================================================
    op.create_table(
        "do_relationship_types",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("namespace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("schema_definition", postgresql.JSONB, nullable=False),
        sa.Column(
            "directional",
            sa.Boolean,
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "allowed_source_types",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "allowed_target_types",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "allow_duplicates",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "idx_do_relationship_types_namespace_id",
        "do_relationship_types",
        ["namespace_id"],
    )
    op.create_unique_constraint(
        "uq_do_relationship_types_namespace_name",
        "do_relationship_types",
        ["namespace_id", "name"],
    )

    # =========================================================================
    # 3. do_entities -- エンティティデータ
    # =========================================================================
    op.create_table(
        "do_entities",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("namespace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "properties",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("search_vector", postgresql.TSVECTOR, nullable=True),
        sa.Column("changed_by", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["type_id"],
            ["do_entity_types.id"],
            name="fk_do_entities_type_id",
        ),
        sa.CheckConstraint("version > 0", name="do_entities_version_check"),
    )
    op.create_index(
        "idx_do_entities_namespace_id",
        "do_entities",
        ["namespace_id"],
    )
    op.create_index(
        "idx_do_entities_search_vector",
        "do_entities",
        ["search_vector"],
        postgresql_using="gin",
    )
    # カーソルベースページネーション用の複合インデックス
    op.create_index(
        "idx_do_entities_type_created_id",
        "do_entities",
        ["type_id", sa.text("created_at DESC"), sa.text("id DESC")],
    )

    # =========================================================================
    # 4. do_indexed_properties -- 高速クエリ用インデックステーブル
    # =========================================================================
    op.create_table(
        "do_indexed_properties",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("namespace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("property_name", sa.String(255), nullable=False),
        sa.Column("string_value", sa.String(500)),
        sa.Column("int_value", sa.BigInteger),
        sa.Column("date_value", sa.TIMESTAMP(timezone=True)),
        sa.Column("bool_value", sa.Boolean),
        sa.Column("float_value", sa.Double),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["entity_id"],
            ["do_entities.id"],
            name="fk_do_indexed_properties_entity_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "(string_value IS NOT NULL)::int + "
            "(int_value IS NOT NULL)::int + "
            "(date_value IS NOT NULL)::int + "
            "(bool_value IS NOT NULL)::int + "
            "(float_value IS NOT NULL)::int = 1",
            name="do_indexed_properties_one_value_only",
        ),
    )
    op.create_index(
        "idx_do_indexed_props_namespace_id",
        "do_indexed_properties",
        ["namespace_id"],
    )
    op.create_index(
        "idx_do_indexed_props_entity",
        "do_indexed_properties",
        ["entity_id"],
    )
    op.create_index(
        "idx_do_indexed_props_name",
        "do_indexed_properties",
        ["property_name"],
    )
    op.create_index(
        "idx_do_indexed_props_string",
        "do_indexed_properties",
        ["string_value"],
        postgresql_where=sa.text("string_value IS NOT NULL"),
    )
    op.create_index(
        "idx_do_indexed_props_int",
        "do_indexed_properties",
        ["int_value"],
        postgresql_where=sa.text("int_value IS NOT NULL"),
    )
    op.create_index(
        "idx_do_indexed_props_date",
        "do_indexed_properties",
        ["date_value"],
        postgresql_where=sa.text("date_value IS NOT NULL"),
    )
    op.create_index(
        "idx_do_indexed_props_bool",
        "do_indexed_properties",
        ["bool_value"],
        postgresql_where=sa.text("bool_value IS NOT NULL"),
    )
    op.create_index(
        "idx_do_indexed_props_float",
        "do_indexed_properties",
        ["float_value"],
        postgresql_where=sa.text("float_value IS NOT NULL"),
    )

    # =========================================================================
    # 5. do_relationships -- リレーションシップデータ
    # =========================================================================
    op.create_table(
        "do_relationships",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("namespace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "properties",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("changed_by", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["type_id"],
            ["do_relationship_types.id"],
            name="fk_do_relationships_type_id",
        ),
        sa.ForeignKeyConstraint(
            ["from_entity_id"],
            ["do_entities.id"],
            name="fk_do_relationships_from_entity_id",
        ),
        sa.ForeignKeyConstraint(
            ["to_entity_id"],
            ["do_entities.id"],
            name="fk_do_relationships_to_entity_id",
        ),
    )
    op.create_index(
        "idx_do_relationships_namespace_id",
        "do_relationships",
        ["namespace_id"],
    )
    # カーソルベースページネーション用の複合インデックス
    op.create_index(
        "idx_do_relationships_from_created_id",
        "do_relationships",
        ["from_entity_id", sa.text("created_at DESC"), sa.text("id DESC")],
    )
    op.create_index(
        "idx_do_relationships_to_created_id",
        "do_relationships",
        ["to_entity_id", sa.text("created_at DESC"), sa.text("id DESC")],
    )

    # =========================================================================
    # 6. do_entity_history -- エンティティ変更履歴（タイムトラベル）
    # =========================================================================
    op.create_table(
        "do_entity_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("namespace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("properties", postgresql.JSONB, nullable=False),
        sa.Column("valid_from", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("valid_to", sa.TIMESTAMP(timezone=True)),
        sa.Column("operation", sa.String(20), nullable=False),
        sa.Column("changed_by", sa.String(255)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["entity_id"],
            ["do_entities.id"],
            name="fk_do_entity_history_entity_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["type_id"],
            ["do_entity_types.id"],
            name="fk_do_entity_history_type_id",
        ),
    )
    op.create_index(
        "idx_do_entity_history_namespace_id",
        "do_entity_history",
        ["namespace_id"],
    )
    op.create_index(
        "idx_do_entity_history_entity_id",
        "do_entity_history",
        ["entity_id"],
    )
    op.create_index(
        "idx_do_entity_history_valid_period",
        "do_entity_history",
        ["entity_id", "valid_from", "valid_to"],
    )

    # =========================================================================
    # 7. do_relationship_history -- リレーションシップ変更履歴（タイムトラベル）
    # =========================================================================
    op.create_table(
        "do_relationship_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("namespace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("properties", postgresql.JSONB, nullable=False),
        sa.Column("valid_from", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("valid_to", sa.TIMESTAMP(timezone=True)),
        sa.Column("operation", sa.String(20), nullable=False),
        sa.Column("changed_by", sa.String(255)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["relationship_id"],
            ["do_relationships.id"],
            name="fk_do_relationship_history_rel_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["type_id"],
            ["do_relationship_types.id"],
            name="fk_do_relationship_history_type_id",
        ),
    )
    op.create_index(
        "idx_do_relationship_history_namespace_id",
        "do_relationship_history",
        ["namespace_id"],
    )
    op.create_index(
        "idx_do_relationship_history_id",
        "do_relationship_history",
        ["relationship_id"],
    )
    op.create_index(
        "idx_do_relationship_history_valid_period",
        "do_relationship_history",
        ["relationship_id", "valid_from", "valid_to"],
    )

    # =========================================================================
    # 8. do_schema_versions -- スキーマバージョン履歴
    # =========================================================================
    op.create_table(
        "do_schema_versions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("namespace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type_kind", sa.String(20), nullable=False),
        sa.Column("type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("schema_definition", postgresql.JSONB, nullable=False),
        sa.Column(
            "previous_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("do_schema_versions.id"),
            nullable=True,
        ),
        sa.Column("compatibility", sa.String(20), nullable=True),
        sa.Column("change_summary", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.UniqueConstraint(
            "type_id",
            "version",
            name="uq_do_schema_versions_type_version",
        ),
    )
    op.create_index(
        "idx_do_schema_versions_type",
        "do_schema_versions",
        ["type_id", "version"],
    )
    op.create_index(
        "idx_do_schema_versions_namespace",
        "do_schema_versions",
        ["namespace_id"],
    )

    # =========================================================================
    # 9. do_schema_proposals -- スキーマ変更提案
    # =========================================================================
    op.create_table(
        "do_schema_proposals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("namespace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'draft'"),
        ),
        sa.Column("target_type_kind", sa.String(20), nullable=False),
        sa.Column(
            "target_type_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("operation", sa.String(20), nullable=False),
        sa.Column("proposed_schema", postgresql.JSONB),
        sa.Column("existing_schema", postgresql.JSONB),
        sa.Column("diff_summary", postgresql.JSONB),
        sa.Column("compatibility_level", sa.String(20)),
        sa.Column(
            "required_approvals",
            sa.Integer,
            nullable=False,
            server_default="1",
        ),
        sa.Column("scheduled_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("applied_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "idx_do_schema_proposals_namespace",
        "do_schema_proposals",
        ["namespace_id", "status"],
    )
    op.create_index(
        "idx_do_schema_proposals_target",
        "do_schema_proposals",
        ["target_type_id"],
        postgresql_where=sa.text("target_type_id IS NOT NULL"),
    )
    op.create_index(
        "idx_do_schema_proposals_scheduled",
        "do_schema_proposals",
        ["scheduled_at"],
        postgresql_where=sa.text("status = 'scheduled' AND scheduled_at IS NOT NULL"),
    )


def downgrade() -> None:
    """全テーブルを削除する."""
    op.drop_table("do_schema_proposals")
    op.drop_table("do_schema_versions")
    op.drop_table("do_relationship_history")
    op.drop_table("do_entity_history")
    op.drop_table("do_relationships")
    op.drop_table("do_indexed_properties")
    op.drop_table("do_entities")
    op.drop_table("do_relationship_types")
    op.drop_table("do_entity_types")
