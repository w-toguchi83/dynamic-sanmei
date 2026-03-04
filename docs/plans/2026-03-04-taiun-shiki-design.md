# 大運四季表（Taiun Shiki Chart）設計

## 概要

sanmei-cli に大運四季表を出力する新規サブコマンド `sanmei taiun-shiki` を追加する。
大運四季表は、各大運期間の季節・星・サイクルを一覧表示し、一生の運気の流れを俯瞰する鑑定ツール。

## 要件

### 表示列（左から順に）

| 列 | 説明 | データソース |
|----|------|-------------|
| 季節 | 春/夏/秋/冬 | 大運地支→四季マッピング |
| 年齢 | 開始-終了歳 | TaiunChart から |
| 大運 | 月干支 or 第N句 | 行ラベル |
| 干支 | 大運の干支（漢字） | TaiunChart.periods[].kanshi |
| 蔵干 | 全蔵干を列挙 | STANDARD_HIDDEN_STEMS[branch] |
| 十大主星 | 日干×大運天干 | school.determine_major_star() |
| 十二大従星 | 日干×大運地支 | calculate_subsidiary_star() |
| サイクル | 人生段階キーワード | 十二大従星→LifeCycleマッピング |

### 先頭行

月干支行を含める。大運列には「月干支」と表示。年齢は 0-(立運-1)歳。

### CLIコマンド

新規サブコマンド `sanmei taiun-shiki`。既存の `sanmei taiun` は変更しない。
オプションは `taiun` と同一: birthdate, --time, --gender, --periods。

## アーキテクチャ

アプローチA: sanmei-core にドメインモデルと計算ロジックを追加。CLI はフォーマットのみ。

### レイヤー構成

```
sanmei-core (計算)
├── domain/taiun_shiki.py     — Season, LifeCycle, TaiunShikiEntry, TaiunShikiChart
├── tables/taiun_shiki.py     — BRANCH_TO_SEASON, SUBSIDIARY_STAR_TO_LIFE_CYCLE
└── calculators/taiun_shiki.py — calculate_taiun_shiki()

sanmei-cli (表示)
├── commands/taiun_shiki.py   — click サブコマンド
└── formatters/text.py        — format_taiun_shiki() 追加
```

## ドメインモデル

### `domain/taiun_shiki.py`

```python
class Season(Enum):
    """四季."""
    SPRING = "春"   # 寅・卯・辰
    SUMMER = "夏"   # 巳・午・未
    AUTUMN = "秋"   # 申・酉・戌
    WINTER = "冬"   # 亥・子・丑

class LifeCycle(Enum):
    """一生の運気サイクル（十二大従星に対応）."""
    TAIJI = "胎児"      # 天報星
    AKAGO = "赤子"      # 天印星
    JIDOU = "児童"      # 天貴星
    SEISHONEN = "青少年" # 天恍星
    SEINEN = "青年"      # 天南星
    SOUNEN = "壮年"      # 天禄星
    KACHOU = "家長"      # 天将星
    ROUJIN = "老人"      # 天堂星
    BYOUNIN = "病人"     # 天胡星
    SHININ = "死人"      # 天極星
    NYUUBO = "入墓"      # 天庫星
    ANOYO = "あの世"     # 天馳星

class TaiunShikiEntry(BaseModel, frozen=True):
    """大運四季表の1行."""
    label: str                          # "月干支" or "第N句"
    kanshi: Kanshi                      # 干支
    start_age: int                      # 開始年齢
    end_age: int                        # 終了年齢
    season: Season                      # 季節
    hidden_stems: HiddenStems           # 蔵干（全蔵干）
    major_star: MajorStar               # 十大主星（日干×大運天干）
    subsidiary_star: SubsidiaryStar     # 十二大従星（日干×大運地支）
    life_cycle: LifeCycle               # サイクル

class TaiunShikiChart(BaseModel, frozen=True):
    """大運四季表."""
    direction: Literal["順行", "逆行"]
    start_age: int
    entries: tuple[TaiunShikiEntry, ...]
```

## マッピングテーブル

### `tables/taiun_shiki.py`

```python
BRANCH_TO_SEASON: dict[TwelveBranch, Season] = {
    TwelveBranch.TORA: Season.SPRING,
    TwelveBranch.U: Season.SPRING,
    TwelveBranch.TATSU: Season.SPRING,
    TwelveBranch.MI: Season.SUMMER,
    TwelveBranch.UMA: Season.SUMMER,
    TwelveBranch.HITSUJI: Season.SUMMER,
    TwelveBranch.SARU: Season.AUTUMN,
    TwelveBranch.TORI: Season.AUTUMN,
    TwelveBranch.INU: Season.AUTUMN,
    TwelveBranch.I: Season.WINTER,
    TwelveBranch.NE: Season.WINTER,
    TwelveBranch.USHI: Season.WINTER,
}

SUBSIDIARY_STAR_TO_LIFE_CYCLE: dict[SubsidiaryStar, LifeCycle] = {
    SubsidiaryStar.TENPOU: LifeCycle.TAIJI,
    SubsidiaryStar.TENIN: LifeCycle.AKAGO,
    SubsidiaryStar.TENKI: LifeCycle.JIDOU,
    SubsidiaryStar.TENKOU: LifeCycle.SEISHONEN,
    SubsidiaryStar.TENNAN: LifeCycle.SEINEN,
    SubsidiaryStar.TENROKU: LifeCycle.SOUNEN,
    SubsidiaryStar.TENSHOU: LifeCycle.KACHOU,
    SubsidiaryStar.TENDOU: LifeCycle.ROUJIN,
    SubsidiaryStar.TENKO: LifeCycle.BYOUNIN,
    SubsidiaryStar.TENKYOKU: LifeCycle.SHININ,
    SubsidiaryStar.TENKU: LifeCycle.NYUUBO,
    SubsidiaryStar.TENCHI: LifeCycle.ANOYO,
}
```

## 計算ロジック

### `calculators/taiun_shiki.py`

```python
def calculate_taiun_shiki(
    meishiki: Meishiki,
    taiun_chart: TaiunChart,
    school: SchoolProtocol,
) -> TaiunShikiChart:
```

**処理:**

1. 月干支行を生成:
   - kanshi = meishiki.pillars.month.kanshi
   - season = BRANCH_TO_SEASON[month_branch]
   - hidden_stems = STANDARD_HIDDEN_STEMS[month_branch]
   - major_star = school.determine_major_star(day_stem, month_stem)
   - subsidiary_star = calculate_subsidiary_star(day_stem, month_branch, school)
   - life_cycle = SUBSIDIARY_STAR_TO_LIFE_CYCLE[subsidiary_star]
   - label = "月干支", start_age = 0, end_age = taiun_chart.start_age - 1

2. 各大運期間 (taiun_chart.periods) について同様に算出:
   - label = f"第{i+1}句"

3. TaiunShikiChart(direction, start_age, entries) を返す

## CLI

### `commands/taiun_shiki.py`

`sanmei taiun-shiki` サブコマンド。既存 `taiun` と同じ引数・オプション。

### `formatters/text.py` に `format_taiun_shiki()` 追加

表示フォーマット:

```
=== 大運四季表 ===
方向: 順行  立運: 5歳

季節  年齢      大運      干支    蔵干        十大主星  十二大従星  サイクル
春    0-4歳     月干支    甲寅    甲・丙・戊  貫索星    天南星      青年
春    5-14歳    第1句     乙卯    乙          石門星    天禄星      壮年
春    15-24歳   第2句     丙辰    戊・癸・乙  鳳閣星    天庫星      入墓
夏    25-34歳   第3句     丁巳    丙・庚・戊  調舒星    天胡星      病人
...
```

蔵干は hongen・chuugen・shogen の順に「・」区切り。None のものは省略。

## テスト方針

- `tables/taiun_shiki.py`: 全12支の季節マッピング、全12星のサイクルマッピング
- `calculators/taiun_shiki.py`: 具体的な命式から大運四季表を算出し、各項目を検証
- `commands/taiun_shiki.py`: CLI統合テスト（正常系、JSON出力、エラーケース）
- `formatters/text.py`: フォーマット出力の検証

## 影響範囲

- sanmei-core: 新規ファイル3つ（domain, tables, calculators）。`__init__.py` にexport追加。
- sanmei-cli: 新規コマンドファイル1つ。formatters/text.py に関数追加。
- 既存テスト: 変更なし（新規モデルのため）
