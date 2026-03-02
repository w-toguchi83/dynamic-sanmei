# sanmei-cli

算命学 CLI ツール。開発者向け動作確認用。

## パッケージ構造

```
src/sanmei_cli/
  main.py           — Click グループ（エントリポイント: cli()）
  types.py          — GenderType（男/male/m, 女/female/f を受理）
  commands/
    meishiki.py     — 命式算出
    taiun.py        — 大運算出（性別必須）
    nenun.py        — 年運算出（年範囲必須）
    isouhou.py      — 位相法分析
  formatters/
    text.py         — テキスト整形（全コマンド分）
    json_fmt.py     — Pydantic → JSON 変換
```

## エントリポイント

`pyproject.toml` の `[project.scripts]` で `sanmei = "sanmei_cli.main:cli"` として登録。

## 設計パターン

- **共通オプション**: `--json` と `--school` は Click グループレベルで定義し `ctx.obj` 経由で各コマンドに伝播
- **フォーマッタ分離**: コマンドはロジックのみ。出力整形は formatters/ に集約
- **流派切り替え**: `SchoolRegistry` で流派を取得し、コマンドに渡す
- **カスタム型**: `GenderType` で日本語/英語の性別入力を統一的に処理
- **エラー処理**: `SanmeiError` を catch して stderr 出力 + exit(1)

## 依存関係

- click >= 8.1.0
- sanmei-core（workspace 依存）
- sanmei-core の I/O 禁止制約は CLI 側で吸収（datetime 生成等）

## 開発コマンド

```bash
just test-pkg sanmei-cli   # テスト（カバレッジ付き）
just lint                  # リント
just typecheck             # 型チェック
just check                 # 全品質チェック
```

## テスト

- 61 テスト / カバレッジ 90%
- `tests/conftest.py` に共通フィクスチャ（school, meishiki, taiun_chart 等）
- Click の `CliRunner` でコマンド統合テスト

## コーディングルール

- 新コマンド追加時: `commands/` にコマンド、`formatters/text.py` にテキスト整形、`main.py` に import 追加
- テスト: コマンドテスト + フォーマッタテスト を分離して作成
- JSON 出力: Pydantic の `model_dump(mode="json")` を使用、`ensure_ascii=False`
