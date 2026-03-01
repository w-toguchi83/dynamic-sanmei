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
