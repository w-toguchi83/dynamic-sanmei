# Dynamic Sanmei プロジェクトセットアップ設計

Date: 2026-03-01

## 概要

動的オントロジーを基盤とした算命学プラットフォームの開発環境・プロジェクト構造の設計。

## 要件

- 動的オントロジー（既存）+ 算命学コアロジック + 複数アプリケーション
- ハイブリッドAPI型：共通算命学API + アプリ固有サービス
- 流派切り替え対応（算命学の複数流派に柔軟対応）
- Python 統一（コア/API）、Next.js（フロントエンド、将来）
- uv workspace + 将来的に Turborepo
- 厳格運用：ruff strict, mypy strict, coverage 80%+, pre-commit, conventional commits
- Claude Code 中心 + Codex / Cursor 補助

## プロジェクト構造

```
dynamic-sanmei/
├── CLAUDE.md
├── README.md
├── pyproject.toml              # ルート (uv workspace定義)
├── .pre-commit-config.yaml
├── .commitlintrc.yaml
├── .cursorrules
├── Justfile
├── .gitignore
│
├── packages/
│   ├── dynamic-ontology/       # 動的オントロジーエンジン（既存コード移動）
│   │   ├── src/dynamic_ontology/
│   │   ├── tests/
│   │   ├── migrations/
│   │   └── pyproject.toml
│   │
│   └── sanmei-core/            # 算命学コアロジック（純粋計算ライブラリ）
│       ├── src/sanmei_core/
│       │   ├── domain/         # ドメインモデル
│       │   ├── calculators/    # 計算エンジン
│       │   ├── schools/        # 流派固有の実装
│       │   └── tables/         # 定数テーブル
│       ├── tests/
│       └── pyproject.toml
│
├── services/
│   └── sanmei-api/             # 共通算命学API（将来実装）
│
├── apps/                       # アプリケーション群（将来実装）
│   └── community/              # コミュニティアプリ（構想）
│       ├── server/
│       ├── web/
│       ├── admin-web/
│       ├── ios/
│       └── android/
│
└── docs/
    ├── plans/
    ├── domain/                 # 算命学ドメイン知識
    └── architecture/
```

## 依存関係

```
sanmei-api
├── depends on → sanmei-core          (計算機能を利用)
└── depends on → dynamic-ontology     (データ取得を利用)

sanmei-core          (依存なし、純粋計算ライブラリ)
dynamic-ontology     (依存なし、独立したデータ基盤)
```

- sanmei-core は I/O なし、外部依存最小限（pydantic のみ）
- dynamic-ontology は独立したデータ基盤
- sanmei-api が両方に依存して橋渡しする

## sanmei-core 内部構造

### ディレクトリ

```
src/sanmei_core/
├── domain/                 # ドメインモデル
│   ├── celestial_stem.py   # 十干
│   ├── earthly_branch.py   # 十二支
│   ├── pillar.py           # 柱（年柱・月柱・日柱・時柱）
│   ├── chart.py            # 命式
│   ├── star.py             # 十大主星・十二大従星
│   ├── phase.py            # 位相法
│   ├── guardian.py         # 守護神
│   └── fortune.py          # 大運・年運
│
├── calculators/            # 計算エンジン
│   ├── base.py             # Protocol 定義
│   ├── pillar.py           # 柱の算出
│   ├── star.py             # 星の算出
│   ├── phase.py            # 位相法の算出
│   ├── guardian.py         # 守護神の算出
│   └── fortune.py          # 運勢の算出
│
├── schools/                # 流派切り替え
│   ├── registry.py         # SchoolRegistry
│   └── default/            # デフォルト流派
│
└── tables/                 # 定数テーブル
    └── mappings.py
```

### 流派切り替え機構

- `calculators/base.py` で Protocol（インターフェース）を定義
- 各流派は Protocol を実装し、差分のみオーバーライド
- `SchoolRegistry` で流派を名前で登録・取得
- 共通ロジックは `calculators/` に直接実装

### 制約

- I/O なし（ファイル読み込み、DB アクセス、HTTP 通信を含めない）
- 依存は最小限（pydantic のみ）
- 入力 → 計算 → 出力で完結

## 開発ルール

### コーディング規約

- Python 3.14+、async-first（API層）
- ruff strict + mypy strict
- テストカバレッジ 80% 以上（パッケージ単位で計測）

### コミット規約

Conventional Commits 形式：

```
<type>(<scope>): <description>

type: feat, fix, docs, refactor, test, ci, chore, perf
scope: sanmei-core, dynamic-ontology, sanmei-api, アプリ名（省略可）
```

### Pre-commit Hooks

- ruff（リント + フォーマット）
- mypy（型チェック）
- conventional-pre-commit（コミットメッセージ検証）

### ブランチ

- main で直接開発・コミット
- 必要に応じて feature ブランチを切るのは自由
- チーム化時に戦略を再検討

## AIエージェント環境

### CLAUDE.md（ルート）

プロジェクト構造、依存関係、開発コマンド、コーディングルール、ドメイン知識の参照先を記載。

### パッケージ単位の CLAUDE.md

各パッケージ固有の情報（アーキテクチャ、テスト方法、規約）を記載。

### .cursorrules

CLAUDE.md の内容を Cursor 向けフォーマットで同期。

### docs/domain/

算命学ドメイン知識のリファレンス。AIエージェントはここを参照して開発。

## 初期セットアップで生成するもの

### 新規作成

- `.gitignore` — Python + Node.js 用
- `README.md` — プロジェクト概要
- `CLAUDE.md` — AIエージェント開発ガイド
- `pyproject.toml` — ルート（uv workspace）
- `.pre-commit-config.yaml`
- `.commitlintrc.yaml`
- `Justfile`
- `.cursorrules`
- `packages/sanmei-core/pyproject.toml`
- `packages/sanmei-core/src/sanmei_core/__init__.py`
- `packages/sanmei-core/CLAUDE.md`
- `packages/dynamic-ontology/CLAUDE.md`
- `services/.gitkeep`
- `apps/.gitkeep`
- `docs/` 配下のディレクトリ構造

### 既存コードの移動

- `dynamic-ontology/` → `packages/dynamic-ontology/`

### 今回は作らないもの

- `services/sanmei-api/` — sanmei-core 完成後
- `apps/` 配下のアプリケーション — 構想段階
- CI/CD パイプライン — ローカル品質管理で十分
- `docs/domain/` の中身 — ユーザーが別途まとめる

## モノレポ管理

- Python 側: uv workspace
- フロントエンド側（将来）: Turborepo + pnpm
- プロジェクト横断コマンド: Justfile
