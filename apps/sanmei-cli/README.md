# sanmei-cli

算命学の命式計算・鑑定を行うコマンドラインツール。開発者向けの動作確認・デバッグ用途。

## インストール

プロジェクトルートから:

```bash
uv sync
```

`sanmei` コマンドが利用可能になる。

## 使い方

### 共通オプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--json` | JSON 形式で出力 | テキスト出力 |
| `--school TEXT` | 流派を指定 | `standard` |

### meishiki — 命式算出

生年月日から命式（三柱・十大主星・十二大従星・天中殺・宿命中殺・五行バランス）を算出する。

```bash
sanmei meishiki 2000-01-15
sanmei meishiki 2000-01-15 --time 14:30
sanmei meishiki 2000-01-15 --json
```

| 引数/オプション | 説明 | 必須 |
|----------------|------|------|
| `BIRTHDATE` | 生年月日 (`YYYY-MM-DD`) | Yes |
| `--time TEXT` | 出生時刻 (`HH:MM`) | No (default: `00:00`) |

出力例:

```
=== 命式 ===
生年月日: 2000年01月15日 14:30 (JST)

【三柱】
        年柱        月柱        日柱
天干      庚          丁          丁
地支      辰          丑          卯

【十大主星】
        北: 石門星
西: 貫索星   中: 司禄星   東: 鳳閣星
        南: 禄存星

【十二大従星】
年: 天庫星   月: 天印星   日: 天胡星

【天中殺】 午未天中殺

【宿命中殺】 なし

【五行バランス】
木: 3  火: 3  土: 3  金: 1  水: 0
主: 木,火,土  欠: 水
日主五行: 火
```

### taiun — 大運算出

生年月日と性別から大運（10年ごとの運勢周期）を算出する。

```bash
sanmei taiun 2000-01-15 --gender 男
sanmei taiun 2000-01-15 --gender female --time 14:30
sanmei taiun 2000-01-15 --gender m --periods 5 --json
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
sanmei nenun 2000-01-15 --from 2024 --to 2030
sanmei nenun 2000-01-15 --from 2020 --to 2025 --json
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
sanmei isouhou 2000-01-15
sanmei isouhou 2000-01-15 --time 14:30 --json
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
