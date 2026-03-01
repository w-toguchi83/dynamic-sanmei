# 命式完成モジュール設計

## 概要

生年月日から完全な命式（陽占・陰占）を生成する機能を `sanmei-core` に追加する。

### ゴール

西暦日時を入力とし、以下を含む `Meishiki` オブジェクトを出力する:

- **陰占**: 三柱（既存）+ 蔵干 + 天中殺
- **陽占**: 十大主星（人体図5位置）+ 十二大従星（3位置）
- **流派**: 複数流派対応（SchoolProtocol + SchoolRegistry）

### スコープ外

- 合・衝・刑・害の判定ロジック（次フェーズ）
- 大運・年運・月運（次フェーズ）
- 時柱（次フェーズ）
- 宿命中殺の判定（天中殺の種類算出のみ。三柱との交差判定は次フェーズ）

## アーキテクチャ

**アプローチ: Protocol-first + Bottom-up**

1. 全ての流派差異点を `SchoolProtocol` として定義
2. `SchoolRegistry` で流派の登録・取得
3. 基盤テーブル（五行・蔵干）→ 計算エンジン（星・天中殺）→ ファサード（Meishiki）の順に積み上げ

### 依存関係フロー

```
datetime
  → SanmeiCalendar.three_pillars()  [既存]  → ThreePillars
  → get_hidden_stems() (×3, school依存)     → HiddenStems
  → calculate_major_star_chart() (school依存) → MajorStarChart
  → calculate_subsidiary_star_chart() (school依存) → SubsidiaryStarChart
  → calculate_tenchuusatsu() (決定論的)      → Tenchuusatsu
  → Meishiki (統合)
```

## 1. ドメインモデル

### 1.1 五行・陰陽 (`domain/gogyo.py`)

```python
class GoGyo(IntEnum):
    WOOD = 0   # 木
    FIRE = 1   # 火
    EARTH = 2  # 土
    METAL = 3  # 金
    WATER = 4  # 水

class InYou(IntEnum):
    YOU = 0  # 陽
    IN = 1   # 陰
```

### 1.2 十大主星・十二大従星 (`domain/star.py`)

```python
class MajorStar(Enum):
    KANSAKU = "貫索星"   # 比劫・陽
    SEKIMON = "石門星"   # 比劫・陰
    HOUKAKU = "鳳閣星"   # 食傷・陽
    CHOUJYO = "調舒星"   # 食傷・陰
    ROKUZON = "禄存星"   # 財星・陽
    SHIROKU = "司禄星"   # 財星・陰
    SHAKI   = "車騎星"   # 官星・陽
    KENGYU  = "牽牛星"   # 官星・陰
    RYUKOU  = "龍高星"   # 印綬・陽
    GYOKUDO = "玉堂星"   # 印綬・陰

class SubsidiaryStar(Enum):
    TENPOU  = "天報星"   # 胎
    TENIN   = "天印星"   # 養
    TENKI   = "天貴星"   # 長生
    TENKOU  = "天恍星"   # 沐浴
    TENNAN  = "天南星"   # 冠帯
    TENROKU = "天禄星"   # 建禄
    TENSHOU = "天将星"   # 帝旺
    TENDOU  = "天堂星"   # 衰
    TENKO   = "天胡星"   # 病
    TENKYOKU = "天極星"  # 死
    TENKO2  = "天庫星"   # 墓
    TENCHI  = "天馳星"   # 絶
```

### 1.3 蔵干 (`domain/hidden_stems.py`)

```python
class HiddenStems(BaseModel, frozen=True):
    main: TenStem          # 本気（主）
    middle: TenStem | None # 中気（副）
    minor: TenStem | None  # 余気（従）
```

### 1.4 天中殺 (`domain/tenchuusatsu.py`)

```python
class TenchuusatsuType(Enum):
    NE_USHI     = "子丑天中殺"
    TORA_U      = "寅卯天中殺"
    TATSU_MI    = "辰巳天中殺"
    UMA_HITSUJI = "午未天中殺"
    SARU_TORI   = "申酉天中殺"
    INU_I       = "戌亥天中殺"

class Tenchuusatsu(BaseModel, frozen=True):
    type: TenchuusatsuType
    branches: tuple[TwelveBranch, TwelveBranch]
```

### 1.5 命式 (`domain/meishiki.py`)

```python
class MajorStarChart(BaseModel, frozen=True):
    """十大主星の人体図（5位置）."""
    north: MajorStar      # 北(頭) — 年干 vs 日干
    east: MajorStar       # 東(左手) — 月干 vs 日干
    center: MajorStar     # 中央(胸) — 日支蔵干主気 vs 日干
    west: MajorStar       # 西(右手) — 月支蔵干主気 vs 日干
    south: MajorStar      # 南(腹) — 年支蔵干主気 vs 日干

class SubsidiaryStarChart(BaseModel, frozen=True):
    """十二大従星（3位置）."""
    year: SubsidiaryStar   # 年支 vs 日干
    month: SubsidiaryStar  # 月支 vs 日干
    day: SubsidiaryStar    # 日支 vs 日干

class Meishiki(BaseModel, frozen=True):
    """完全な命式."""
    pillars: ThreePillars
    hidden_stems: dict[str, HiddenStems]  # "year"/"month"/"day" → 蔵干
    major_stars: MajorStarChart
    subsidiary_stars: SubsidiaryStarChart
    tenchuusatsu: Tenchuusatsu
```

## 2. 流派システム

### 2.1 流派差異点

| 差異点 | 具体例 | データ型 |
|--------|--------|----------|
| 蔵干テーブル | 子=[癸] vs 子=[壬,癸] | `dict[TwelveBranch, HiddenStems]` |
| 十大主星の陰陽判定 | 官星の陰陽判定方向 | 判定関数 |
| 土性帝旺支 | 戊→戌, 己→未(午) vs 両方→戌 | `dict[TenStem, TwelveBranch]` |
| 節入り日計算 | 天文計算 vs 固定テーブル | 既存 `SetsuiriProvider` |

### 2.2 SchoolProtocol (`protocols/school.py`)

```python
class SchoolProtocol(Protocol):
    @property
    def name(self) -> str: ...

    def get_hidden_stems(self, branch: TwelveBranch) -> HiddenStems: ...

    def determine_major_star(
        self, day_stem: TenStem, target_stem: TenStem
    ) -> MajorStar: ...

    def get_teiou_branch(self, stem: TenStem) -> TwelveBranch: ...

    def get_setsuiri_provider(self) -> SetsuiriProvider: ...
```

### 2.3 SchoolRegistry (`schools/registry.py`)

```python
class SchoolRegistry:
    def register(self, school: SchoolProtocol) -> None: ...
    def get(self, name: str) -> SchoolProtocol: ...
    def default(self) -> SchoolProtocol: ...
    def list_schools(self) -> list[str]: ...
```

### 2.4 標準流派 (`schools/standard.py`)

`StandardSchool` クラスが `SchoolProtocol` を満たす。

- **蔵干**: `docs/domain/02_Chapter2` のテーブル準拠
- **陰陽判定**: `docs/domain/04_Chapter4` のテーブル準拠
- **土性帝旺**: 戊→戌, 己→未 (docs/domain/05_Chapter5 準拠)
- **節入り**: `MeeusSetsuiriProvider` を内部使用

### 2.5 既存コードとの共存

- 既存の `SanmeiCalendar` は変更しない
- 新しい `MeishikiCalculator` は `SchoolProtocol` を受け取る
- `MeishikiCalculator` の内部で `SanmeiCalendar` を生成・使用

## 3. 計算モジュール

### 3.1 五行関係テーブル (`tables/gogyo.py`)

```python
STEM_TO_GOGYO: dict[TenStem, GoGyo]  # 甲→木, 乙→木, 丙→火, ...
STEM_TO_INYOU: dict[TenStem, InYou]  # 甲→陽, 乙→陰, ...

# 相生: 木→火→土→金→水→木
SOUGOU: dict[GoGyo, GoGyo]

# 相剋: 木→土→水→火→金→木
SOUKOKU: dict[GoGyo, GoGyo]

class GoGyoRelation(Enum):
    HIKAKU = "比劫"      # 同じ五行
    SHOKUSHOU = "食傷"   # 日干が生む
    ZAISEI = "財星"      # 日干が剋す
    KANSEI = "官星"      # 日干を剋す
    INJYU = "印綬"       # 日干を生む

def get_relation(day_stem: TenStem, target_stem: TenStem) -> GoGyoRelation: ...
def is_same_polarity(stem_a: TenStem, stem_b: TenStem) -> bool: ...
```

### 3.2 蔵干テーブル (`tables/hidden_stems.py`)

標準流派の蔵干テーブル（`docs/domain/02_Chapter2` 準拠）。

### 3.3 十大主星計算 (`calculators/major_star.py`)

```python
def calculate_major_star_chart(
    pillars: ThreePillars,
    hidden_stems: dict[str, HiddenStems],
    school: SchoolProtocol,
) -> MajorStarChart:
    day_stem = pillars.day.stem
    return MajorStarChart(
        north=school.determine_major_star(day_stem, pillars.year.stem),
        east=school.determine_major_star(day_stem, pillars.month.stem),
        center=school.determine_major_star(day_stem, hidden_stems["day"].main),
        west=school.determine_major_star(day_stem, hidden_stems["month"].main),
        south=school.determine_major_star(day_stem, hidden_stems["year"].main),
    )
```

### 3.4 十二大従星計算 (`calculators/subsidiary_star.py`)

```python
def calculate_subsidiary_star(
    day_stem: TenStem,
    target_branch: TwelveBranch,
    school: SchoolProtocol,
) -> SubsidiaryStar:
    teiou = school.get_teiou_branch(day_stem)
    # 帝旺支から対象地支までの距離 → 十二運テーブルで従星決定

JUUNIUN_ORDER: tuple[SubsidiaryStar, ...] = (
    # 帝旺→衰→病→死→墓→絶→胎→養→長生→沐浴→冠帯→建禄
    SubsidiaryStar.TENSHOU, SubsidiaryStar.TENDOU,
    SubsidiaryStar.TENKO, SubsidiaryStar.TENKYOKU,
    SubsidiaryStar.TENKO2, SubsidiaryStar.TENCHI,
    SubsidiaryStar.TENPOU, SubsidiaryStar.TENIN,
    SubsidiaryStar.TENKI, SubsidiaryStar.TENKOU,
    SubsidiaryStar.TENNAN, SubsidiaryStar.TENROKU,
)
```

### 3.5 天中殺計算 (`calculators/tenchuusatsu.py`)

日柱の六十干支から決定論的に算出。

```python
# 六十干支を10干ずつ6グループに分割
# グループ内で十二支が2つ欠ける → その2支が天中殺支
TENCHUUSATSU_MAP: dict[range, TenchuusatsuType] = {
    range(0, 10): TenchuusatsuType.INU_I,      # 甲子〜癸酉
    range(10, 20): TenchuusatsuType.SARU_TORI,  # ...
    # ...
}
```

### 3.6 Meishiki ファサード (`calculators/meishiki_calculator.py`)

```python
class MeishikiCalculator:
    def __init__(self, school: SchoolProtocol, *, tz: tzinfo | None = None):
        self._school = school
        self._calendar = SanmeiCalendar(
            school.get_setsuiri_provider(), tz=tz
        )

    def calculate(self, dt: datetime) -> Meishiki:
        pillars = self._calendar.three_pillars(dt)
        hidden = {
            "year": self._school.get_hidden_stems(pillars.year.branch),
            "month": self._school.get_hidden_stems(pillars.month.branch),
            "day": self._school.get_hidden_stems(pillars.day.branch),
        }
        major = calculate_major_star_chart(pillars, hidden, self._school)
        subsidiary = calculate_subsidiary_star_chart(
            pillars, pillars.day.stem, self._school
        )
        tenchuusatsu = calculate_tenchuusatsu(pillars.day)
        return Meishiki(
            pillars=pillars,
            hidden_stems=hidden,
            major_stars=major,
            subsidiary_stars=subsidiary,
            tenchuusatsu=tenchuusatsu,
        )
```

## 4. テスト戦略

| レイヤー | テスト内容 | 手法 |
|---------|-----------|------|
| 五行テーブル | 10干×10干 = 100組の関係判定 | パラメタライズドテスト |
| 蔵干テーブル | 12支すべての蔵干取得 | 標準流派テーブル照合 |
| 十大主星 | 日干×対象干 → 正しい星 | ドメイン知識の算出ルール表照合 |
| 十二大従星 | 日干(10干)×12支 → 正しい従星 | 帝旺支からの距離テーブル照合 |
| 天中殺 | 60干支 → 6種類の天中殺 | 全60パターン網羅 |
| SchoolRegistry | 登録・取得・デフォルト | 単体テスト |
| MeishikiCalculator | サンプル命式(Appendix A) | 既知の命式との統合テスト |

### 検証データ

- `docs/domain/Appendix_A` のサンプル命式 (1985-04-10)
- 算命学参考書の既知例

## 5. ファイル構成（新規追加分）

```
packages/sanmei-core/src/sanmei_core/
├── domain/
│   ├── gogyo.py            # NEW: 五行・陰陽 Enum
│   ├── star.py             # NEW: 十大主星・十二大従星 Enum
│   ├── hidden_stems.py     # NEW: 蔵干モデル
│   ├── tenchuusatsu.py     # NEW: 天中殺モデル
│   └── meishiki.py         # NEW: Meishiki 複合モデル
├── calculators/
│   ├── major_star.py       # NEW: 十大主星計算
│   ├── subsidiary_star.py  # NEW: 十二大従星計算
│   ├── tenchuusatsu.py     # NEW: 天中殺計算
│   └── meishiki_calculator.py  # NEW: 命式ファサード
├── tables/
│   ├── gogyo.py            # NEW: 五行関係テーブル
│   └── hidden_stems.py     # NEW: 蔵干テーブル(標準)
├── protocols/
│   └── school.py           # NEW: SchoolProtocol
└── schools/
    ├── registry.py         # NEW: SchoolRegistry
    └── standard.py         # NEW: 標準流派実装
```

### 既存ファイルの変更

- `__init__.py`: 新しい public API を追加
- 既存のクラス・関数は変更なし（後方互換）
