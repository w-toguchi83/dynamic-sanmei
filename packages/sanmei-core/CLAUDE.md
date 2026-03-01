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

```
just test-pkg sanmei-core
uv run --project packages/sanmei-core pytest packages/sanmei-core/tests -v
```

## 依存関係

- pydantic のみ。他のパッケージには依存しない。
- dynamic-ontology には依存しない。

## ドメイン知識

算命学の用語・算出ルールは `docs/domain/` を参照。
