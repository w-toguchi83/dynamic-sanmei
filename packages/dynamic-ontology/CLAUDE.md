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

```
just test-pkg dynamic-ontology
uv run --project packages/dynamic-ontology pytest packages/dynamic-ontology/tests -v
```

## 依存関係

- FastAPI, SQLAlchemy, Pydantic, Alembic, psycopg
- 他のパッケージ（sanmei-core 等）には依存しない

## DB マイグレーション

- Alembic を使用。テーブルプレフィックスは `do_`
- `alembic.ini` でDB接続設定
