# Dynamic Sanmei - プロジェクト横断コマンド

# デフォルト: 利用可能なコマンド一覧
default:
    @just --list

# 全パッケージのテスト実行
test:
    uv run --project packages/dynamic-ontology pytest packages/dynamic-ontology/tests -v
    uv run --project packages/sanmei-core pytest packages/sanmei-core/tests -v
    uv run --project apps/sanmei-cli pytest apps/sanmei-cli/tests -v

# 特定パッケージのテスト実行
test-pkg pkg:
    uv run --project packages/{{pkg}} pytest packages/{{pkg}}/tests -v

# NOTE: services/ を追加する場合はパスに追記すること
# 全パッケージのリント
lint:
    uv run ruff check packages/ apps/
    uv run ruff format --check packages/ apps/

# リントの自動修正
lint-fix:
    uv run ruff check --fix packages/ apps/
    uv run ruff format packages/ apps/

# 全パッケージの型チェック
typecheck:
    uv run mypy packages/dynamic-ontology/src
    uv run mypy packages/sanmei-core/src
    uv run mypy apps/sanmei-cli/src

# 全品質チェック（リント + 型チェック + テスト）
check: lint typecheck test
