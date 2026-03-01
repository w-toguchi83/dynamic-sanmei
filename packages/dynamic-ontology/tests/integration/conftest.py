"""Integration test fixtures -- DB migration at session scope."""

import os
import subprocess
from uuid import uuid4

import pytest


@pytest.fixture
def test_namespace_id() -> str:
    """テスト用の namespace_id を返す.

    integration/ 直下のテストファイル（test_query_engine*.py など）で使用。
    persistence/ や api/ のテストはサブディレクトリの conftest.py で提供される。
    """
    return str(uuid4())


@pytest.fixture(scope="session", autouse=True)
def _run_migrations() -> None:
    """テストセッション開始時にテスト用DBにマイグレーションを適用する."""
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/dynamic_ontology_test",
    )
    assert "dynamic_ontology_test" in database_url, (
        f"テストは dynamic_ontology_test DB で実行してください: {database_url}"
    )

    # new-product/dynamic-ontology/ ディレクトリを cwd に指定して alembic.ini を確実に見つける
    package_dir = os.path.join(os.path.dirname(__file__), "..", "..")
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        cwd=package_dir,
    )
    if result.returncode != 0:
        pytest.fail(f"マイグレーション失敗:\n{result.stderr}")
