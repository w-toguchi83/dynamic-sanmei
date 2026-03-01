"""PostgresSchemaVersionRepository の統合テスト."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text

from dynamic_ontology.adapters.persistence.postgresql.database import DatabaseSessionManager
from dynamic_ontology.adapters.persistence.postgresql.schema_version_repository import (
    PostgresSchemaVersionRepository,
)
from dynamic_ontology.domain.models.schema_version import (
    CompatibilityLevel,
    SchemaVersion,
    TypeKind,
)


@pytest.fixture
async def cleanup_schema_versions(db_manager: DatabaseSessionManager):
    """テスト後に do_schema_versions を削除するフィクスチャ.

    previous_version_id の自己参照 FK を考慮して、
    まず FK を NULL にしてから削除する。
    """
    created_ids: list[str] = []
    yield created_ids
    if not created_ids:
        return
    async with db_manager.session() as session:
        # FK 制約を回避するため、まず previous_version_id を NULL にする
        for sv_id in created_ids:
            await session.execute(
                text("UPDATE do_schema_versions SET previous_version_id = NULL WHERE id = :id"),
                {"id": sv_id},
            )
        # 全レコードを削除
        for sv_id in created_ids:
            await session.execute(
                text("DELETE FROM do_schema_versions WHERE id = :id"),
                {"id": sv_id},
            )


def _make_schema_version(
    *,
    type_id: str | None = None,
    version: int = 1,
    type_kind: TypeKind = TypeKind.ENTITY_TYPE,
    previous_version_id: str | None = None,
    compatibility: CompatibilityLevel | None = None,
    change_summary: dict[str, object] | None = None,
    created_by: str | None = "test-user",
    namespace_id: str,
) -> SchemaVersion:
    """テスト用の SchemaVersion を生成するヘルパー."""
    return SchemaVersion(
        id=uuid4(),
        type_kind=type_kind,
        type_id=uuid4() if type_id is None else type_id,  # type: ignore[arg-type]
        version=version,
        schema_definition={
            "properties": {
                "title": {"type": "string", "required": True, "indexed": True},
            }
        },
        previous_version_id=previous_version_id,  # type: ignore[arg-type]
        compatibility=compatibility,
        change_summary=change_summary,
        created_at=datetime.now(UTC),
        created_by=created_by,
        namespace_id=namespace_id,
    )


@pytest.mark.asyncio
async def test_create_schema_version(
    db_manager: DatabaseSessionManager,
    cleanup_schema_versions: list[str],
    test_namespace_id: str,
) -> None:
    """スキーマバージョンを作成し、全フィールドが正しく保存されること."""
    sv = _make_schema_version(
        compatibility=CompatibilityLevel.FULL,
        change_summary={"added_fields": ["title"], "removed_fields": []},
        namespace_id=test_namespace_id,
    )

    async with db_manager.session() as session:
        repo = PostgresSchemaVersionRepository(session, test_namespace_id)
        result = await repo.create(sv)
        cleanup_schema_versions.append(str(result.id))

    assert result.id == sv.id
    assert result.type_kind == TypeKind.ENTITY_TYPE
    assert result.type_id == sv.type_id
    assert result.version == 1
    assert result.schema_definition == sv.schema_definition
    assert result.previous_version_id is None
    assert result.compatibility == CompatibilityLevel.FULL
    assert result.change_summary == {
        "added_fields": ["title"],
        "removed_fields": [],
    }
    assert result.created_by == "test-user"
    assert str(result.namespace_id) == test_namespace_id
    assert result.created_at is not None


@pytest.mark.asyncio
async def test_list_by_type_id_returns_versions_in_order(
    db_manager: DatabaseSessionManager,
    cleanup_schema_versions: list[str],
    test_namespace_id: str,
) -> None:
    """指定タイプの全バージョンがバージョン昇順で取得できること."""
    type_id = uuid4()
    versions: list[SchemaVersion] = []

    for i in range(1, 4):
        sv = SchemaVersion(
            id=uuid4(),
            type_kind=TypeKind.ENTITY_TYPE,
            type_id=type_id,
            version=i,
            schema_definition={
                "properties": {
                    "field": {"type": "string", "required": True},
                }
            },
            previous_version_id=versions[-1].id if versions else None,
            compatibility=CompatibilityLevel.BACKWARD if i > 1 else None,
            change_summary=None,
            created_at=datetime.now(UTC),
            created_by="test-user",
            namespace_id=test_namespace_id,
        )
        versions.append(sv)

    # バージョン順（1, 2, 3）で挿入（previous_version_id FK 制約のため）
    async with db_manager.session() as session:
        repo = PostgresSchemaVersionRepository(session, test_namespace_id)
        for sv in versions:
            created = await repo.create(sv)
            cleanup_schema_versions.append(str(created.id))

    async with db_manager.session() as session:
        repo = PostgresSchemaVersionRepository(session, test_namespace_id)
        result = await repo.list_by_type_id(str(type_id), TypeKind.ENTITY_TYPE)

    assert len(result) == 3
    assert [r.version for r in result] == [1, 2, 3]
    assert result[0].previous_version_id is None
    assert result[1].previous_version_id == versions[0].id
    assert result[2].previous_version_id == versions[1].id


@pytest.mark.asyncio
async def test_get_by_version(
    db_manager: DatabaseSessionManager,
    cleanup_schema_versions: list[str],
    test_namespace_id: str,
) -> None:
    """特定バージョン番号でスキーマバージョンを取得できること."""
    type_id = uuid4()

    sv1 = SchemaVersion(
        id=uuid4(),
        type_kind=TypeKind.ENTITY_TYPE,
        type_id=type_id,
        version=1,
        schema_definition={"properties": {"name": {"type": "string"}}},
        created_at=datetime.now(UTC),
        created_by="test-user",
        namespace_id=test_namespace_id,
    )
    sv2 = SchemaVersion(
        id=uuid4(),
        type_kind=TypeKind.ENTITY_TYPE,
        type_id=type_id,
        version=2,
        schema_definition={
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            }
        },
        previous_version_id=sv1.id,
        compatibility=CompatibilityLevel.BACKWARD,
        created_at=datetime.now(UTC),
        created_by="test-user",
        namespace_id=test_namespace_id,
    )

    async with db_manager.session() as session:
        repo = PostgresSchemaVersionRepository(session, test_namespace_id)
        await repo.create(sv1)
        cleanup_schema_versions.append(str(sv1.id))
        await repo.create(sv2)
        cleanup_schema_versions.append(str(sv2.id))

    async with db_manager.session() as session:
        repo = PostgresSchemaVersionRepository(session, test_namespace_id)

        result_v1 = await repo.get_by_version(str(type_id), 1)
        assert result_v1 is not None
        assert result_v1.version == 1
        assert result_v1.id == sv1.id

        result_v2 = await repo.get_by_version(str(type_id), 2)
        assert result_v2 is not None
        assert result_v2.version == 2
        assert result_v2.id == sv2.id
        assert result_v2.compatibility == CompatibilityLevel.BACKWARD


@pytest.mark.asyncio
async def test_get_latest_version(
    db_manager: DatabaseSessionManager,
    cleanup_schema_versions: list[str],
    test_namespace_id: str,
) -> None:
    """最新バージョンを取得できること."""
    type_id = uuid4()

    for v in range(1, 4):
        sv = SchemaVersion(
            id=uuid4(),
            type_kind=TypeKind.ENTITY_TYPE,
            type_id=type_id,
            version=v,
            schema_definition={
                "properties": {"f": {"type": "string"}},
                "version_tag": v,
            },
            created_at=datetime.now(UTC),
            created_by="test-user",
            namespace_id=test_namespace_id,
        )
        async with db_manager.session() as session:
            repo = PostgresSchemaVersionRepository(session, test_namespace_id)
            created = await repo.create(sv)
            cleanup_schema_versions.append(str(created.id))

    async with db_manager.session() as session:
        repo = PostgresSchemaVersionRepository(session, test_namespace_id)
        result = await repo.get_latest_version(str(type_id))

    assert result is not None
    assert result.version == 3


@pytest.mark.asyncio
async def test_get_by_version_returns_none_for_nonexistent_version(
    db_manager: DatabaseSessionManager,
    cleanup_schema_versions: list[str],
    test_namespace_id: str,
) -> None:
    """存在しないバージョン番号を指定すると None が返ること."""
    type_id = uuid4()
    sv = _make_schema_version(type_id=type_id, namespace_id=test_namespace_id)  # type: ignore[arg-type]

    async with db_manager.session() as session:
        repo = PostgresSchemaVersionRepository(session, test_namespace_id)
        created = await repo.create(sv)
        cleanup_schema_versions.append(str(created.id))

    async with db_manager.session() as session:
        repo = PostgresSchemaVersionRepository(session, test_namespace_id)
        result = await repo.get_by_version(str(type_id), 999)

    assert result is None


@pytest.mark.asyncio
async def test_get_latest_version_returns_none_for_nonexistent_type(
    db_manager: DatabaseSessionManager,
    test_namespace_id: str,
) -> None:
    """存在しない type_id を指定すると None が返ること."""
    async with db_manager.session() as session:
        repo = PostgresSchemaVersionRepository(session, test_namespace_id)
        result = await repo.get_latest_version(str(uuid4()))

    assert result is None


@pytest.mark.asyncio
async def test_namespace_isolation(
    db_manager: DatabaseSessionManager,
    cleanup_schema_versions: list[str],
    test_namespace_id: str,
) -> None:
    """異なるネームスペースのスキーマバージョンが参照できないこと."""
    type_id = uuid4()
    other_namespace_id = str(uuid4())

    sv = SchemaVersion(
        id=uuid4(),
        type_kind=TypeKind.ENTITY_TYPE,
        type_id=type_id,
        version=1,
        schema_definition={"properties": {"x": {"type": "string"}}},
        created_at=datetime.now(UTC),
        created_by="test-user",
        namespace_id=test_namespace_id,
    )

    # test_namespace_id でスキーマバージョンを作成
    async with db_manager.session() as session:
        repo = PostgresSchemaVersionRepository(session, test_namespace_id)
        created = await repo.create(sv)
        cleanup_schema_versions.append(str(created.id))

    # 別ネームスペースからは取得できない
    async with db_manager.session() as session:
        repo = PostgresSchemaVersionRepository(session, other_namespace_id)

        result_latest = await repo.get_latest_version(str(type_id))
        assert result_latest is None

        result_list = await repo.list_by_type_id(str(type_id), TypeKind.ENTITY_TYPE)
        assert result_list == []

        result_version = await repo.get_by_version(str(type_id), 1)
        assert result_version is None

    # test_namespace_id からは取得できる
    async with db_manager.session() as session:
        repo = PostgresSchemaVersionRepository(session, test_namespace_id)
        result = await repo.get_latest_version(str(type_id))
        assert result is not None
        assert result.id == sv.id
