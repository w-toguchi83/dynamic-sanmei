"""テスト環境設定."""

import os


def pytest_configure(config):
    """テスト環境変数を設定."""
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/dynamic_ontology_test",
    )
