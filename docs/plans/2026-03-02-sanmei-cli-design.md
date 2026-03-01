# Sanmei CLI Design

開発者向け算命学CLI。sanmei-core の全機能を動作確認・検証するためのツール。

## パッケージ

- 場所: `apps/sanmei-cli/`
- 依存: `click`, `sanmei-core`（ワークスペース内パス依存）
- エントリポイント: `sanmei` コマンド（`pyproject.toml` の `[project.scripts]`）
- uv workspace メンバーとして登録

## 構造

```
apps/sanmei-cli/
├── pyproject.toml
├── src/
│   └── sanmei_cli/
│       ├── __init__.py
│       ├── main.py            # click グループ & エントリポイント
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── meishiki.py    # meishiki サブコマンド
│       │   ├── taiun.py       # taiun サブコマンド
│       │   ├── nenun.py       # nenun サブコマンド
│       │   └── isouhou.py     # isouhou サブコマンド
│       └── formatters/
│           ├── __init__.py
│           ├── text.py        # 日本語テーブル表示
│           └── json.py        # JSON 出力
└── tests/
    └── ...
```

## コマンドインターフェース

### 共通オプション

- `--json` — JSON出力に切替（デフォルト: テキスト）
- `--school TEXT` — 流派指定（デフォルト: "standard"）

### Gender 入力

click カスタム型で以下を大文字小文字区別なく受け付ける:

- 男性: `男`, `male`, `m`
- 女性: `女`, `female`, `f`

### `sanmei meishiki BIRTHDATE`

```
sanmei meishiki 2000-01-15 [--time 14:30] [--gender 男] [--json] [--school standard]
```

テキスト出力:
```
=== 命式 ===
生年月日: 2000年1月15日 14:30 (JST)

【三柱】
        年柱      月柱      日柱
天干    己        丁        壬
地支    卯        丑        午

【十大主星】
        北: 龍高星
西: 車騎星  中: 禄存星  東: 鳳閣星
        南: 石門星

【十二大従星】
年: 天南星    月: 天将星    日: 天庫星

【天中殺】 戌亥天中殺

【宿命中殺】 なし

【五行バランス】
木: 2  火: 3  土: 4  金: 0  水: 1
主: 土  欠: 金
日主五行: 水
```

### `sanmei taiun BIRTHDATE --gender GENDER`

```
sanmei taiun 2000-01-15 --gender 男 [--time 14:30] [--periods 10] [--json]
```

テキスト出力:
```
=== 大運 ===
方向: 順行  開始年齢: 3歳

 期間    干支    年齢
 1       丙子    3-12歳
 2       乙亥    13-22歳
 ...
```

### `sanmei nenun BIRTHDATE`

```
sanmei nenun 2000-01-15 [--time 14:30] --from 2020 --to 2030 [--json]
```

テキスト出力:
```
=== 年運 ===
 年      干支    年齢
 2020    庚子    20歳
 2021    辛丑    21歳
 ...
```

### `sanmei isouhou BIRTHDATE`

```
sanmei isouhou 2000-01-15 [--time 14:30] [--json]
```

テキスト出力:
```
=== 位相法（命式内） ===
【天干の合】
丁-壬 合 → 木

【地支の関係】
卯-午 刑
...
```

## データフロー

```
CLI Input (click)
    ↓
main.py: @cli.group() + 共通オプション
    ↓
commands/*.py: サブコマンドごとのロジック
    ├── 引数パース & バリデーション
    ├── SchoolRegistry → SchoolProtocol 取得
    ├── MeishikiCalculator.calculate(dt) → Meishiki
    ├── (taiun) calculate_taiun(meishiki, dt, gender, ...)
    ├── (nenun) calculate_nenun(dt, ..., year_range)
    ├── (isouhou) analyze_isouhou(meishiki.pillars)
    └── formatter に渡す
        ↓
formatters/text.py or formatters/json.py
    ↓
click.echo() で出力
```

## エラーハンドリング

- `DateOutOfRangeError` → 「対応範囲外の年です (1864-2100)」
- `SetsuiriNotFoundError` → 「節入りデータが見つかりません」
- 不正な日付形式 → click の型バリデーションで捕捉
- 不正な性別値 → カスタム型でエラーメッセージ

## JSON 出力

- Pydantic モデルの `.model_dump()` を活用
- `json.dumps(data, ensure_ascii=False, indent=2)` で日本語をそのまま出力
- Enum 値は `.value`（漢字表記）で出力

## テスト戦略

- `formatters/` — 既知データに対する出力文字列の検証
- `commands/` — click `CliRunner` による統合テスト（正常系 + 異常系）
- Gender パーサー — 全エイリアスの変換テスト
- カバレッジ 80%+ 維持
- sanmei-core の計算正確性はテストしない（core 側で検証済み）
