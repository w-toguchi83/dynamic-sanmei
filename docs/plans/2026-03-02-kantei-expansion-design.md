# 鑑定機能拡充モジュール設計

sanmei-core の鑑定機能を拡充する。宿命中殺・五行バランス・位相法（合冲刑害）・大運・年運の4モジュールを追加。

## アプローチ

**拡張 Meishiki + 独立 Fortune** — 命式の本質情報（宿命中殺、五行バランス）は Meishiki モデルを拡張して統合。時間軸の分析（大運・年運）は独立モジュールとして分離。位相法は両方から利用される共有モジュール。

## 実装順序

1. 宿命中殺 — 既存天中殺モジュールの拡張、小規模
2. 五行バランス分析 — 既存 GoGyo モジュールの拡張、中規模
3. 合・冲・刑・害（位相法） — 新規モジュール、大運の前提
4. 大運・年運 — 上記全てを活用する統合的な機能

## モジュール構造

```
packages/sanmei-core/src/sanmei_core/
├── domain/
│   ├── shukumei_chuusatsu.py  # 宿命中殺モデル（新規）
│   ├── gogyo_balance.py       # 五行バランスモデル（新規）
│   ├── isouhou.py             # 位相法モデル（新規）
│   ├── fortune.py             # 大運・年運モデル（新規）
│   └── meishiki.py            # 拡張（shukumei_chuusatsu, gogyo_balance 追加）
├── tables/
│   └── isouhou.py             # 合冲刑害ルックアップテーブル（新規）
├── calculators/
│   ├── shukumei_chuusatsu.py  # 宿命中殺算出（新規）
│   ├── gogyo_balance.py       # 五行バランス算出（新規）
│   ├── isouhou.py             # 位相法判定（新規）
│   ├── fortune.py             # 大運・年運算出（新規）
│   └── fortune_analyzer.py    # 命式×運勢の相互作用分析（新規）
└── protocols/
    └── school.py              # SchoolProtocol 拡張（大運端数処理追加）
```

---

## 1. 宿命中殺

命式の三柱と天中殺から、宿命中殺の有無と位置を判定する。

### ドメインモデル

```python
# domain/shukumei_chuusatsu.py
class ShukumeiChuusatsuPosition(Enum):
    """宿命中殺が当たる位置."""
    YEAR_BRANCH = "年支中殺"      # 年柱の地支が天中殺支
    MONTH_BRANCH = "月支中殺"     # 月柱の地支が天中殺支
    DAY_BRANCH = "日支中殺"       # 日柱の地支（配偶者宮）
    YEAR_STEM = "年干中殺"        # 年柱の天干（星の中殺）
    MONTH_STEM = "月干中殺"       # 月柱の天干（星の中殺）

class ShukumeiChuusatsu(BaseModel, frozen=True):
    position: ShukumeiChuusatsuPosition
```

### 算出ロジック

```python
# calculators/shukumei_chuusatsu.py
def calculate_shukumei_chuusatsu(
    pillars: ThreePillars,
    tenchuusatsu: Tenchuusatsu,
) -> list[ShukumeiChuusatsu]:
```

判定ルール:
- 年支/月支/日支が天中殺の2支に含まれれば → 支の中殺
- 年柱/月柱の地支が天中殺支であれば → その天干も中殺（天干中殺は支中殺が前提）

### Meishiki 拡張

```python
class Meishiki(BaseModel, frozen=True):
    ...  # 既存フィールド
    shukumei_chuusatsu: tuple[ShukumeiChuusatsu, ...]  # 追加（0〜5個）
```

---

## 2. 五行バランス分析

命式全体の五行の分布を分析する。

### ドメインモデル

```python
# domain/gogyo_balance.py
class GoGyoCount(BaseModel, frozen=True):
    """命式中の各五行の出現数."""
    wood: int = 0
    fire: int = 0
    earth: int = 0
    metal: int = 0
    water: int = 0

    def get(self, gogyo: GoGyo) -> int: ...

    @property
    def total(self) -> int: ...

class GoGyoBalance(BaseModel, frozen=True):
    """五行バランス分析結果."""
    stem_count: GoGyoCount       # 天干のみの五行カウント（3干）
    branch_count: GoGyoCount     # 蔵干展開した五行カウント
    total_count: GoGyoCount      # 合算
    dominant: GoGyo              # 最も多い五行
    lacking: tuple[GoGyo, ...]   # 不在の五行
    day_stem_gogyo: GoGyo        # 日干の五行（参照用）
```

### 算出ロジック

```python
# calculators/gogyo_balance.py
def calculate_gogyo_balance(
    pillars: ThreePillars,
    hidden_stems: dict[str, HiddenStems],
) -> GoGyoBalance:
```

カウント対象:
- 天干: 年干、月干、日干 → 各1カウント
- 蔵干: 各地支の蔵干（本気・中気・余気）→ 各1カウント（等重み、標準流派）

### Meishiki 拡張

```python
class Meishiki(BaseModel, frozen=True):
    ...  # 既存フィールド
    gogyo_balance: GoGyoBalance  # 追加
```

---

## 3. 合・冲・刑・害（位相法）

干支間の相互作用をテーブルベースで判定する。命式内の柱間および命式×運勢の相互作用に使う共有モジュール。

### ドメインモデル

```python
# domain/isouhou.py
class StemInteractionType(Enum):
    """十干の相互作用."""
    GOU = "合"

class BranchInteractionType(Enum):
    """十二支の相互作用."""
    RIKUGOU = "六合"
    SANGOU = "三合局"
    ROKUCHUU = "六冲"
    KEI = "刑"
    JIKEI = "自刑"
    RIKUGAI = "六害"

class StemInteraction(BaseModel, frozen=True):
    """十干の相互作用結果."""
    type: StemInteractionType
    stems: tuple[TenStem, TenStem]
    result_gogyo: GoGyo

class BranchInteraction(BaseModel, frozen=True):
    """十二支の相互作用結果."""
    type: BranchInteractionType
    branches: tuple[TwelveBranch, ...]  # 2支 or 3支
    result_gogyo: GoGyo | None          # 合の場合のみ

class IsouhouResult(BaseModel, frozen=True):
    """位相法の分析結果."""
    stem_interactions: tuple[StemInteraction, ...]
    branch_interactions: tuple[BranchInteraction, ...]
```

### テーブル

```python
# tables/isouhou.py
STEM_GOU: dict[frozenset[TenStem], GoGyo]          # 5組の十干合
RIKUGOU: dict[frozenset[TwelveBranch], GoGyo]       # 6組の六合
SANGOU: list[tuple[frozenset[TwelveBranch], GoGyo]] # 4組の三合局
ROKUCHUU: set[frozenset[TwelveBranch]]              # 6組の六冲
SANKEI: list[frozenset[TwelveBranch]]               # 三刑パターン
JIKEI: set[TwelveBranch]                            # 自刑の4支
RIKUGAI: set[frozenset[TwelveBranch]]               # 6組の六害
```

十干合テーブル（ドメイン知識 Ch.8 より）:

| 合 | 化合後の五行 |
|---|---|
| 甲・己 | 土 |
| 乙・庚 | 金 |
| 丙・辛 | 水 |
| 丁・壬 | 木 |
| 戊・癸 | 火 |

### 算出ロジック

```python
# calculators/isouhou.py
def analyze_stem_interactions(
    stems: Sequence[TenStem],
) -> list[StemInteraction]:
    """天干の組み合わせから合を検出."""

def analyze_branch_interactions(
    branches: Sequence[TwelveBranch],
) -> list[BranchInteraction]:
    """地支の組み合わせから六合・三合・冲・刑・害を検出."""

def analyze_isouhou(pillars: ThreePillars) -> IsouhouResult:
    """命式の三柱に対して位相法を適用.
    年-月、月-日、年-日 の3ペアを検査。
    三合局は3支全てで判定。
    """
```

`analyze_stem_interactions` / `analyze_branch_interactions` は大運・年運との相互作用分析でも再利用する。

---

## 4. 大運・年運

### 大運の算出アルゴリズム

```
入力: Meishiki, birth_datetime, gender
出力: TaiunChart

1. 日干の陰陽 × 性別 で順行/逆行を判定
   - 陽干＋男性 or 陰干＋女性 → 順行
   - 陰干＋男性 or 陽干＋女性 → 逆行
2. 誕生日から最寄りの節入り日までの日数を算出
   - 順行: 次の節入り日まで
   - 逆行: 前の節入り日まで
3. 日数 ÷ 3 = 大運起算年齢（端数処理は流派差 → SchoolProtocol）
4. 月柱から順行 or 逆行で六十干支を辿り、各10年の大運干支を算出
```

### ドメインモデル

```python
# domain/fortune.py
class Gender(Enum):
    MALE = "男"
    FEMALE = "女"

class Taiun(BaseModel, frozen=True):
    """大運の1期間（10年）."""
    kanshi: Kanshi
    start_age: int
    end_age: int

class TaiunChart(BaseModel, frozen=True):
    """大運表."""
    direction: Literal["順行", "逆行"]
    start_age: int
    periods: tuple[Taiun, ...]

class Nenun(BaseModel, frozen=True):
    """年運（1年分）."""
    year: int
    kanshi: Kanshi
    age: int

class FortuneInteraction(BaseModel, frozen=True):
    """運勢と命式の相互作用."""
    period_kanshi: Kanshi
    isouhou: IsouhouResult
    affected_stars: tuple[MajorStar, ...] | None
```

### 算出ロジック

```python
# calculators/fortune.py
def calculate_taiun(
    meishiki: Meishiki,
    birth_datetime: datetime,
    gender: Gender,
    setsuiri_provider: SetsuiriProvider,
    num_periods: int = 10,
) -> TaiunChart:
    """大運を算出."""

def calculate_nenun(
    birth_datetime: datetime,
    setsuiri_provider: SetsuiriProvider,
    year_range: tuple[int, int],
) -> list[Nenun]:
    """年運を算出. 年運の干支 = その年の年柱干支."""
```

### 命式×運勢の相互作用分析

```python
# calculators/fortune_analyzer.py
def analyze_fortune_interaction(
    meishiki: Meishiki,
    period_kanshi: Kanshi,
) -> FortuneInteraction:
    """大運/年運の干支と命式の相互作用を分析.
    位相法モジュールを使い、干支間の合冲刑害を検出。
    """
```

### SchoolProtocol 拡張

```python
class SchoolProtocol(Protocol):
    ...  # 既存メソッド

    def get_taiun_start_age_rounding(self) -> Literal["floor", "round"]:
        """大運起算年齢の端数処理方法.
        - floor: 切り捨て（標準流派デフォルト）
        - round: 四捨五入
        """
        ...
```

---

## 設計上の決定事項

| 項目 | 決定 |
|---|---|
| 宿命中殺の配置 | Meishiki に統合（命式の本質情報） |
| 五行バランスの配置 | Meishiki に統合（命式の本質情報） |
| 位相法の配置 | 独立モジュール（命式・大運の両方から利用） |
| 大運・年運の配置 | 独立モジュール（時間軸の分析） |
| Gender の扱い | Meishiki に含めず、大運計算の引数 |
| 蔵干の重み付け | 等重み（標準流派）。流派差は SchoolProtocol で対応可能 |
| 大運起算年齢の端数 | SchoolProtocol で流派差に対応 |
| 位相法の低レベル関数 | 公開 API として大運分析からも利用可能 |

## テスト戦略

- 各モジュールのユニットテスト（テーブル値検証、境界ケース）
- 宿命中殺: 天中殺の6パターン × 三柱の各位置
- 五行バランス: 既知の命式データで検証
- 位相法: Ch.8 のテーブル値全件をテスト
- 大運: 順行/逆行の判定、起算年齢の計算、干支の進行
- 年運: 立春境界の年干支
- 統合テスト: 既知の有名人の命式で全モジュールを通した検証
- カバレッジ 80%+ 維持
