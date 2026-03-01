# Dynamic Sanmei プロジェクト初期セットアップ 実装計画

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 動的オントロジーを基盤とした算命学プラットフォームのモノレポ構造を構築し、開発環境を整備する。

**Architecture:** uv workspace によるPythonモノレポ。`packages/` に再利用ライブラリ（dynamic-ontology, sanmei-core）、`services/` に共通API、`apps/` にアプリケーションを配置。既存の `dynamic-ontology/` を `packages/` 配下に移動する。

**Tech Stack:** Python 3.14+, uv, hatchling, ruff, mypy, pytest, pre-commit, just

**Design doc:** `docs/plans/2026-03-01-project-setup-design.md`

---

### Task 1: Git リポジトリ初期化と .gitignore 作成

**Files:**
- Create: `.gitignore`

**Step 1: git init**

Run: `git init`

**Step 2: .gitignore を作成**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
*.egg-info/
*.egg
dist/
build/
.eggs/

# Virtual environments
.venv/
venv/
ENV/

# Testing
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Node.js (将来のフロントエンド用)
node_modules/
.next/
.turbo/

# Environment
.env
.env.local
.env.*.local

# uv
*.lock
!uv.lock
```

**Step 3: 初期コミット**

```bash
git add .gitignore
git commit -m "chore: initialize repository with .gitignore"
```

---

### Task 2: 既存 dynamic-ontology を packages/ に移動

**Files:**
- Move: `dynamic-ontology/` → `packages/dynamic-ontology/`

**Step 1: packages ディレクトリ作成と移動**

```bash
mkdir -p packages
```

移動前に `.venv/` と `.pytest_cache/` を除外する（環境固有ファイルは移動しない）。

```bash
rm -rf dynamic-ontology/.venv dynamic-ontology/.pytest_cache
mv dynamic-ontology packages/dynamic-ontology
```

**Step 2: 移動後の動作確認**

```bash
cd packages/dynamic-ontology
uv sync
uv run pytest tests/ -x -q --tb=short
cd ../..
```

Expected: テストが既存と同様にパスする。

**Step 3: コミット**

```bash
git add packages/dynamic-ontology
git commit -m "chore: move dynamic-ontology to packages/"
```

---

### Task 3: ルート pyproject.toml（uv workspace）作成

**Files:**
- Create: `pyproject.toml`

**Step 1: ルート pyproject.toml を作成**

```toml
[project]
name = "dynamic-sanmei"
version = "0.1.0"
description = "動的オントロジーを基盤とした算命学プラットフォーム"
requires-python = ">=3.14"

[tool.uv.workspace]
members = [
    "packages/*",
    "services/*",
]

[tool.ruff]
target-version = "py314"
line-length = 120
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "ANN", "S", "B"]
ignore = ["ANN101", "ANN102", "S101"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["ANN", "S"]

[tool.mypy]
python_version = "3.14"
strict = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

**Step 2: uv workspace の動作確認**

```bash
uv sync
```

Expected: workspace members として `packages/dynamic-ontology` が認識される。

**Step 3: コミット**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add root pyproject.toml with uv workspace"
```

---

### Task 4: sanmei-core パッケージのスキャフォールド作成

**Files:**
- Create: `packages/sanmei-core/pyproject.toml`
- Create: `packages/sanmei-core/src/sanmei_core/__init__.py`
- Create: `packages/sanmei-core/src/sanmei_core/domain/__init__.py`
- Create: `packages/sanmei-core/src/sanmei_core/calculators/__init__.py`
- Create: `packages/sanmei-core/src/sanmei_core/schools/__init__.py`
- Create: `packages/sanmei-core/src/sanmei_core/tables/__init__.py`
- Create: `packages/sanmei-core/tests/__init__.py`
- Create: `packages/sanmei-core/tests/unit/__init__.py`

**Step 1: pyproject.toml を作成**

```toml
[project]
name = "sanmei-core"
version = "0.1.0"
description = "算命学コアロジック - 純粋計算ライブラリ"
requires-python = ">=3.14"
dependencies = [
    "pydantic>=2.10.0",
]

[dependency-groups]
dev = [
    "pytest>=8.3.0",
    "pytest-cov>=6.0.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/sanmei_core"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

**Step 2: ディレクトリ構造とパッケージ初期化ファイルを作成**

```bash
mkdir -p packages/sanmei-core/src/sanmei_core/{domain,calculators,schools,tables}
mkdir -p packages/sanmei-core/tests/unit
```

`packages/sanmei-core/src/sanmei_core/__init__.py`:
```python
"""算命学コアロジック - 純粋計算ライブラリ."""
```

各サブパッケージの `__init__.py` は空ファイルで作成。

**Step 3: uv sync で確認**

```bash
uv sync
```

Expected: `sanmei-core` が workspace member として認識される。

**Step 4: smoke test を作成して実行**

`packages/sanmei-core/tests/unit/test_smoke.py`:
```python
def test_import_sanmei_core():
    import sanmei_core
    assert sanmei_core is not None
```

Run: `uv run --project packages/sanmei-core pytest packages/sanmei-core/tests -v`
Expected: PASS

**Step 5: コミット**

```bash
git add packages/sanmei-core
git commit -m "chore(sanmei-core): scaffold package structure"
```

---

### Task 5: Justfile 作成

**Files:**
- Create: `Justfile`

**Step 1: just をインストール（未インストールの場合）**

```bash
brew install just
```

**Step 2: Justfile を作成**

```just
# Dynamic Sanmei - プロジェクト横断コマンド

# デフォルト: 利用可能なコマンド一覧
default:
    @just --list

# 全パッケージのテスト実行
test:
    uv run --project packages/dynamic-ontology pytest packages/dynamic-ontology/tests -v
    uv run --project packages/sanmei-core pytest packages/sanmei-core/tests -v

# 特定パッケージのテスト実行
test-pkg pkg:
    uv run --project packages/{{pkg}} pytest packages/{{pkg}}/tests -v

# 全パッケージのリント
lint:
    uv run ruff check packages/ services/
    uv run ruff format --check packages/ services/

# リントの自動修正
lint-fix:
    uv run ruff check --fix packages/ services/
    uv run ruff format packages/ services/

# 全パッケージの型チェック
typecheck:
    uv run mypy packages/dynamic-ontology/src
    uv run mypy packages/sanmei-core/src

# 全品質チェック（リント + 型チェック + テスト）
check: lint typecheck test
```

**Step 3: 動作確認**

```bash
just --list
just test
```

Expected: コマンド一覧が表示され、テストが全パスする。

**Step 4: コミット**

```bash
git add Justfile
git commit -m "chore: add Justfile for project-wide commands"
```

---

### Task 6: Pre-commit hooks と Conventional Commits 設定

**Files:**
- Create: `.pre-commit-config.yaml`
- Create: `.commitlintrc.yaml`

**Step 1: pre-commit をインストール**

```bash
uv tool install pre-commit
```

**Step 2: .pre-commit-config.yaml を作成**

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.15.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.10.0
          - sqlalchemy>=2.0.36
          - fastapi>=0.115.0

  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v4.0.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args: [feat, fix, docs, refactor, test, ci, chore, perf]
```

注意: `rev` の値は実行時に最新バージョンを確認して設定すること。

**Step 3: .commitlintrc.yaml を作成**

```yaml
rules:
  type-enum:
    - 2
    - always
    - - feat
      - fix
      - docs
      - refactor
      - test
      - ci
      - chore
      - perf
  scope-enum:
    - 1
    - always
    - - sanmei-core
      - dynamic-ontology
      - sanmei-api
  subject-max-length:
    - 2
    - always
    - 100
```

**Step 4: pre-commit install**

```bash
pre-commit install
pre-commit install --hook-type commit-msg
```

**Step 5: 動作確認**

```bash
pre-commit run --all-files
```

Expected: ruff と ruff-format がパスする（mypy は初回で警告が出る場合あり、修正して対応）。

**Step 6: コミット**

```bash
git add .pre-commit-config.yaml .commitlintrc.yaml
git commit -m "ci: add pre-commit hooks and conventional commits config"
```

---

### Task 7: CLAUDE.md 作成（ルート + 各パッケージ）

**Files:**
- Create: `CLAUDE.md`
- Create: `packages/dynamic-ontology/CLAUDE.md`
- Create: `packages/sanmei-core/CLAUDE.md`

**Step 1: ルート CLAUDE.md を作成**

```markdown
# Dynamic Sanmei

動的オントロジーを基盤とした算命学プラットフォーム。

## プロジェクト構造

- `packages/dynamic-ontology/` — 動的オントロジーエンジン（データ基盤）
- `packages/sanmei-core/` — 算命学コアロジック（純粋計算ライブラリ）
- `services/` — 共通API群（将来実装）
- `apps/` — アプリケーション群（将来実装）
- `docs/domain/` — 算命学ドメイン知識
- `docs/plans/` — 設計・実装計画ドキュメント

## 依存関係

- sanmei-core: 外部依存なし（純粋計算）。I/O禁止。
- dynamic-ontology: 独立したデータ基盤。
- sanmei-api（将来）: 上記両方に依存して橋渡し。
- sanmei-core と dynamic-ontology は互いに依存しない。

## 開発コマンド

- `just test` — 全パッケージのテスト実行
- `just test-pkg <pkg>` — 特定パッケージのテスト
- `just lint` — リント
- `just lint-fix` — リント自動修正
- `just typecheck` — 型チェック
- `just check` — 全品質チェック（lint + typecheck + test）

## コーディングルール

- Python 3.14+
- ruff strict + mypy strict
- テストカバレッジ 80% 以上（パッケージ単位）
- Conventional Commits 形式でコミット: `<type>(<scope>): <description>`
  - type: feat, fix, docs, refactor, test, ci, chore, perf
  - scope: sanmei-core, dynamic-ontology, sanmei-api（省略可）

## 算命学ドメイン知識

- `docs/domain/` 配下のドキュメントを必ず参照すること
- 流派によって計算方法が異なる。流派固有ロジックは `packages/sanmei-core/src/sanmei_core/schools/` に配置

## パッケージ管理

- uv workspace でモノレポ管理
- 各パッケージの CLAUDE.md にパッケージ固有情報あり
```

**Step 2: packages/dynamic-ontology/CLAUDE.md を作成**

```markdown
# Dynamic Ontology

動的オントロジーエンジン — スキーマ定義をデータとして管理する。

## アーキテクチャ

クリーンアーキテクチャ（3層構成）:

- `src/dynamic_ontology/domain/` — ドメイン層（モデル、サービス、ポート）
- `src/dynamic_ontology/application/` — アプリケーション層（ユースケース）
- `src/dynamic_ontology/adapters/` — アダプター層（API, PostgreSQL永続化）

## 主要機能

- Query DSL（フィルタ、トラバーサル、集約、時間旅行）
- スキーマバージョニング（互換性レベル管理）
- 時間旅行クエリ（EntitySnapshot）
- バッチ操作（all-or-nothing トランザクション）
- カーソルベースページネーション

## 開発コマンド

```bash
just test-pkg dynamic-ontology
uv run --project packages/dynamic-ontology pytest packages/dynamic-ontology/tests -v
```

## 依存関係

- FastAPI, SQLAlchemy, Pydantic, Alembic, psycopg
- 他のパッケージ（sanmei-core 等）には依存しない

## DB マイグレーション

- Alembic を使用。テーブルプレフィックスは `do_`
- `alembic.ini` でDB接続設定
```

**Step 3: packages/sanmei-core/CLAUDE.md を作成**

```markdown
# Sanmei Core

算命学コアロジック — 純粋計算ライブラリ。

## 設計原則

- I/O なし（ファイル読み込み、DB アクセス、HTTP 通信を含めない）
- 依存は最小限（pydantic のみ）
- 入力 → 計算 → 出力で完結

## ディレクトリ構造

- `src/sanmei_core/domain/` — ドメインモデル（十干、十二支、柱、命式、星など）
- `src/sanmei_core/calculators/` — 計算エンジン（Protocol + 共通ロジック）
- `src/sanmei_core/schools/` — 流派固有の実装
- `src/sanmei_core/tables/` — 定数テーブル（マッピングデータ）

## 流派切り替え

- `calculators/base.py` で Protocol（インターフェース）を定義
- 各流派は Protocol を実装し、差分のみオーバーライド
- `schools/registry.py` の SchoolRegistry で流派を名前で登録・取得
- 共通ロジックは `calculators/` に直接実装

## 開発コマンド

```bash
just test-pkg sanmei-core
uv run --project packages/sanmei-core pytest packages/sanmei-core/tests -v
```

## 依存関係

- pydantic のみ。他のパッケージには依存しない。
- dynamic-ontology には依存しない。

## ドメイン知識

算命学の用語・算出ルールは `docs/domain/` を参照。
```

**Step 4: コミット**

```bash
git add CLAUDE.md packages/dynamic-ontology/CLAUDE.md packages/sanmei-core/CLAUDE.md
git commit -m "docs: add CLAUDE.md for root and each package"
```

---

### Task 8: README.md と .cursorrules 作成

**Files:**
- Create: `README.md`
- Create: `.cursorrules`

**Step 1: README.md を作成**

```markdown
# Dynamic Sanmei

動的オントロジーを基盤とした算命学プラットフォーム。

## プロジェクト構造

| ディレクトリ | 説明 |
|---|---|
| `packages/dynamic-ontology` | 動的オントロジーエンジン（データ基盤） |
| `packages/sanmei-core` | 算命学コアロジック（純粋計算ライブラリ） |
| `services/` | 共通API群（将来実装） |
| `apps/` | アプリケーション群（将来実装） |
| `docs/` | ドキュメント |

## セットアップ

```bash
# 依存関係のインストール
uv sync

# pre-commit hooks のインストール
pre-commit install
pre-commit install --hook-type commit-msg

# 全テスト実行
just test

# 全品質チェック
just check
```

## 開発コマンド

```bash
just test           # 全テスト
just test-pkg <pkg> # 特定パッケージのテスト
just lint           # リント
just lint-fix       # リント自動修正
just typecheck      # 型チェック
just check          # 全品質チェック
```
```

**Step 2: .cursorrules を作成**

```
# Dynamic Sanmei - Cursor Rules

## Project Structure
- packages/dynamic-ontology/ — Dynamic ontology engine (data foundation)
- packages/sanmei-core/ — Sanmei core logic (pure calculation library, no I/O)
- services/ — Shared API services (future)
- apps/ — Applications (future)
- docs/domain/ — Sanmei domain knowledge reference

## Dependencies
- sanmei-core has NO dependency on dynamic-ontology
- dynamic-ontology has NO dependency on sanmei-core
- sanmei-api (future) depends on both

## Coding Rules
- Python 3.14+
- ruff strict + mypy strict
- Test coverage >= 80%
- Conventional Commits: <type>(<scope>): <description>
- sanmei-core: NO I/O (no file reads, no DB, no HTTP)

## Domain Knowledge
- Refer to docs/domain/ for Sanmei terminology and rules
- Multiple schools (流派) exist with different calculation methods
- School-specific logic goes in packages/sanmei-core/src/sanmei_core/schools/

## Commands
- just test — Run all tests
- just lint — Lint
- just typecheck — Type check
- just check — All quality checks
```

**Step 3: コミット**

```bash
git add README.md .cursorrules
git commit -m "docs: add README.md and .cursorrules"
```

---

### Task 9: プレースホルダーディレクトリとドキュメント構造の作成

**Files:**
- Create: `services/.gitkeep`
- Create: `apps/.gitkeep`
- Create: `docs/domain/.gitkeep`
- Create: `docs/architecture/.gitkeep`

**Step 1: ディレクトリとプレースホルダー作成**

```bash
mkdir -p services apps docs/domain docs/architecture
touch services/.gitkeep apps/.gitkeep docs/domain/.gitkeep docs/architecture/.gitkeep
```

**Step 2: コミット**

```bash
git add services/.gitkeep apps/.gitkeep docs/domain/.gitkeep docs/architecture/.gitkeep
git commit -m "chore: add placeholder directories for services, apps, and docs"
```

---

### Task 10: 最終検証

**Step 1: uv sync で全体の依存解決を確認**

```bash
uv sync
```

Expected: エラーなし。

**Step 2: just check で全品質チェック**

```bash
just check
```

Expected: lint, typecheck, test すべてパス。

**Step 3: pre-commit の動作確認**

```bash
pre-commit run --all-files
```

Expected: すべてのフックがパス。

**Step 4: ディレクトリ構造の最終確認**

```bash
find . -not -path './.git/*' -not -path './.venv/*' -not -path '*/node_modules/*' -not -path '*/__pycache__/*' | head -60
```

Expected: 設計ドキュメントに記載したディレクトリ構造と一致。

**Step 5: 問題があれば修正してコミット**

```bash
git add -A
git commit -m "chore: fix issues found during final verification"
```

問題がなければこのステップはスキップ。
