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
