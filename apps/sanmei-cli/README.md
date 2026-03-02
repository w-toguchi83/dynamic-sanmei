# sanmei-cli

算命学の命式計算・鑑定を行うコマンドラインツール。開発者向けの動作確認・デバッグ用途。

## セットアップ

プロジェクトルートから:

```bash
uv sync
```

すべてのコマンドは `uv run` 経由で実行する:

```bash
uv run sanmei --help
```

## 使い方

### 共通オプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--json` | JSON 形式で出力 | テキスト出力 |
| `--school TEXT` | 流派を指定 | `standard` |

### meishiki — 命式算出

生年月日から命式（三柱・十大主星・十二大従星・天中殺・宿命中殺・五行バランス）を算出する。

```bash
uv run sanmei meishiki 2000-01-15
uv run sanmei meishiki 2000-01-15 --time 14:30
uv run sanmei meishiki 2000-01-15 --json
```

| 引数/オプション | 説明 | 必須 |
|----------------|------|------|
| `BIRTHDATE` | 生年月日 (`YYYY-MM-DD`) | Yes |
| `--time TEXT` | 出生時刻 (`HH:MM`) | No (default: `00:00`) |

出力例:

```
=== 命式 ===
生年月日: 2000年1月15日 14:30 (JST)

【三柱】
        年柱        月柱        日柱
天干      己         丁         壬
地支      卯         丑         申

【十大主星】
        北: 車騎星
西: 車騎星  中: 玉堂星  東: 司禄星
        南: 調舒星

【十二大従星】
年: 天極星    月: 天堂星    日: 天貴星

【天中殺】 戌亥天中殺

【宿命中殺】 なし

【五行バランス】
木: 1  火: 1  土: 3  金: 2  水: 3
主: 土  欠: なし
日主五行: 水
```

### taiun — 大運算出

生年月日と性別から大運（10年ごとの運勢周期）を算出する。

```bash
uv run sanmei taiun 2000-01-15 --gender 男
uv run sanmei taiun 2000-01-15 --gender female --time 14:30
uv run sanmei taiun 2000-01-15 --gender m --periods 5 --json
```

| 引数/オプション | 説明 | 必須 |
|----------------|------|------|
| `BIRTHDATE` | 生年月日 (`YYYY-MM-DD`) | Yes |
| `--gender` | 性別（`男`/`male`/`m`, `女`/`female`/`f`） | Yes |
| `--time TEXT` | 出生時刻 (`HH:MM`) | No (default: `00:00`) |
| `--periods INT` | 大運の数 | No (default: `10`) |

### nenun — 年運算出

指定した年範囲の年運（年ごとの運勢）を算出する。

```bash
uv run sanmei nenun 2000-01-15 --from 2024 --to 2030
uv run sanmei nenun 2000-01-15 --from 2020 --to 2025 --json
```

| 引数/オプション | 説明 | 必須 |
|----------------|------|------|
| `BIRTHDATE` | 生年月日 (`YYYY-MM-DD`) | Yes |
| `--from INT` | 開始年（西暦） | Yes |
| `--to INT` | 終了年（西暦） | Yes |
| `--time TEXT` | 出生時刻 (`HH:MM`) | No (default: `00:00`) |

### isouhou — 位相法分析

命式内の天干の合・地支の関係（合・冲・刑・害）を分析する。

```bash
uv run sanmei isouhou 2000-01-15
uv run sanmei isouhou 2000-01-15 --time 14:30 --json
```

| 引数/オプション | 説明 | 必須 |
|----------------|------|------|
| `BIRTHDATE` | 生年月日 (`YYYY-MM-DD`) | Yes |
| `--time TEXT` | 出生時刻 (`HH:MM`) | No (default: `00:00`) |

## 出力形式

- **テキスト（デフォルト）**: 日本語の整形済みテキスト
- **JSON（`--json`）**: Pydantic モデルの JSON シリアライズ。日本語文字はそのまま保持される。

## 開発

```bash
# テスト実行
just test-pkg sanmei-cli

# リント
just lint

# 型チェック
just typecheck

# 全品質チェック
just check
```

## 依存パッケージ

- [click](https://click.palletsprojects.com/) — CLI フレームワーク
- [sanmei-core](../../packages/sanmei-core/) — 算命学コアロジック
