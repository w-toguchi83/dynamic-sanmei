# 算命歴変換モジュール設計

西暦日付から算命学の三柱干支（年柱・月柱・日柱）を算出するコアモジュールの設計。

## 要件

| 項目 | 決定 |
|---|---|
| 対象年代 | 1864〜2100年（甲子年〜） |
| 節入り日精度 | 時単位 |
| 節入り日データ | Protocol で注入可能。天文計算を1実装として提供 |
| スコープ | 三柱干支（年柱・月柱・日柱）のみ。蔵干・星は次フェーズ |
| 天文計算 | 純粋 Python（Meeus アルゴリズム）を基本 |
| タイムゾーン | 注入可能、デフォルト JST。流派で中国 TZ 等に差替可能 |

## アーキテクチャ

Protocol 中心設計を採用。節入り日の供給を `SetsuiriProvider` Protocol として抽象化し、
三柱計算は全てこの Provider に依存する。

```
SetsuiriProvider (Protocol)
├── MeeusSetsuiriProvider   ← 天文計算（デフォルト実装）
├── TableSetsuiriProvider   ← ルックアップテーブル（将来）
└── (流派ごとの実装)        ← SchoolRegistry 経由で切替

SanmeiCalendar (ファサード)
├── year_pillar(date) → Kanshi
├── month_pillar(date) → Kanshi
└── day_pillar(date) → Kanshi  ← 節入り不要、純粋計算
```

選択理由:
- 既存の SchoolRegistry パターンと自然に統合
- 日柱計算は Provider 不要で独立、関心分離が明確
- テスト時に Mock Provider 注入が容易
- 将来の蔵干・星算出への拡張パスが明確

## モジュール構造

```
packages/sanmei-core/src/sanmei_core/
├── domain/
│   ├── kanshi.py          # 干支・十干・十二支・六十干支
│   ├── pillar.py          # 三柱（年柱・月柱・日柱）
│   └── calendar.py        # 節入り日・二十四節気
├── calculators/
│   ├── pillar_calculator.py   # 三柱計算 + SanmeiCalendar ファサード
│   └── solar_longitude.py     # 太陽黄経計算（Meeus）+ MeeusSetsuiriProvider
├── tables/
│   ├── stems.py           # 十干マスターデータ
│   ├── branches.py        # 十二支マスターデータ
│   ├── kanshi_cycle.py    # 六十干支サイクル
│   └── month_stem.py      # 五虎遁年法テーブル
└── protocols/
    └── setsuiri.py        # SetsuiriProvider Protocol
```

## コアデータ型

### TenStem（十干）

```python
class TenStem(Enum):
    KINOE = 0       # 甲 木陽
    KINOTO = 1      # 乙 木陰
    HINOE = 2       # 丙 火陽
    HINOTO = 3      # 丁 火陰
    TSUCHINOE = 4   # 戊 土陽
    TSUCHINOTO = 5  # 己 土陰
    KANOE = 6       # 庚 金陽
    KANOTO = 7      # 辛 金陰
    MIZUNOE = 8     # 壬 水陽
    MIZUNOTO = 9    # 癸 水陰
```

Enum 値は 0 始まりの通し番号。mod 演算に直接使える。

### TwelveBranch（十二支）

```python
class TwelveBranch(Enum):
    NE = 0      # 子
    USHI = 1    # 丑
    TORA = 2    # 寅
    U = 3       # 卯
    TATSU = 4   # 辰
    MI = 5      # 巳
    UMA = 6     # 午
    HITSUJI = 7 # 未
    SARU = 8    # 申
    TORI = 9    # 酉
    INU = 10    # 戌
    I = 11      # 亥
```

### Kanshi（干支）

```python
class Kanshi(BaseModel):
    stem: TenStem
    branch: TwelveBranch
    index: int  # 六十干支の通し番号 (0-59)
```

`index` から stem/branch を逆算: `stem = index % 10`, `branch = index % 12`

### ThreePillars（三柱）

```python
class ThreePillars(BaseModel):
    year: Kanshi    # 年柱
    month: Kanshi   # 月柱
    day: Kanshi     # 日柱
```

### SetsuiriDate（節入り日）

```python
class SetsuiriDate(BaseModel):
    year: int
    month: int              # 算命学上の月 (1-12, 寅月=1)
    datetime_utc: datetime  # UTC での節入り時刻
    solar_term: SolarTerm   # 二十四節気のどれか
```

UTC で保持し、タイムゾーン変換は利用時に行う。

## SetsuiriProvider Protocol

```python
class SetsuiriProvider(Protocol):
    def get_setsuiri_dates(self, year: int) -> list[SetsuiriDate]:
        """指定年の12節入り日（節気のみ、中気は除く）を返す。
        立春〜小寒の12件。算命学の月境界となる節気のみ。
        """
        ...

    def get_risshun(self, year: int) -> SetsuiriDate:
        """指定年の立春（年の境界）を返す。"""
        ...
```

## 二十四節気と算命学月の対応

算命学では二十四節気のうち節気（12個）のみが月境界:

| 算命学月 | 節気 | 太陽黄経 | おおよその日付 |
|---|---|---|---|
| 1月（寅月） | 立春 | 315° | 2/4 |
| 2月（卯月） | 啓蟄 | 345° | 3/6 |
| 3月（辰月） | 清明 | 15° | 4/5 |
| 4月（巳月） | 立夏 | 45° | 5/6 |
| 5月（午月） | 芒種 | 75° | 6/6 |
| 6月（未月） | 小暑 | 105° | 7/7 |
| 7月（申月） | 立秋 | 135° | 8/7 |
| 8月（酉月） | 白露 | 165° | 9/8 |
| 9月（戌月） | 寒露 | 195° | 10/8 |
| 10月（亥月） | 立冬 | 225° | 11/7 |
| 11月（子月） | 大雪 | 255° | 12/7 |
| 12月（丑月） | 小寒 | 285° | 1/6 |

## 太陽黄経計算（MeeusSetsuiriProvider）

Jean Meeus『Astronomical Algorithms』(2nd ed.) Chapter 25 の太陽黄経計算を使用。

### solar_longitude(jde) → float

Julian Ephemeris Day から太陽黄経（度）を計算。
VSOP87 の簡略版（Meeus Table 25.C/D）を使用。
精度: ±0.01°（≒ ±15分の時間誤差）。時単位要件に十分。

### find_setsuiri(year, target_longitude) → datetime

指定年で太陽黄経が `target_longitude` に達する時刻を二分探索。
探索精度: 1分以内。

計算フロー:
1. 各節気の太陽黄経（315°, 345°, 15°, ...）をターゲットに設定
2. おおよその日付範囲で二分探索
3. `solar_longitude(jde)` が目標値を超えるポイントを特定
4. UTC datetime に変換して `SetsuiriDate` を生成

## 三柱計算アルゴリズム

### 年柱

```
入力: date (datetime), risshun (SetsuiriDate), tz (tzinfo, default=JST)
出力: Kanshi

1. date を tz でローカル時刻に変換
2. 立春の UTC 時刻も同じ tz に変換して比較
3. date < 立春 なら year = date.year - 1、そうでなければ year = date.year
4. 年干 = (year - 4) % 10 → TenStem
5. 年支 = (year - 4) % 12 → TwelveBranch
6. 六十干支 index = (year - 4) % 60
```

基準: 西暦4年 = 甲子。

### 月柱

```
入力: date (datetime), setsuiri_dates (list[SetsuiriDate]), tz (tzinfo, default=JST)
出力: Kanshi

1. setsuiri_dates（12件）を時系列ソート
2. date がどの節入り日の間に入るかを判定 → 算命学上の月 (1-12) を特定
3. 月支 = TwelveBranch((月番号 + 1) % 12)  # 寅(2)から開始
4. 年干から五虎遁年法で寅月の天干を取得
5. 月干 = TenStem((寅月天干.value + 月番号 - 1) % 10)
6. (月干, 月支) から六十干支 index を算出
```

五虎遁年法テーブル:

| 年干 | 寅月の天干 |
|---|---|
| 甲・己 | 丙 |
| 乙・庚 | 戊 |
| 丙・辛 | 庚 |
| 丁・壬 | 壬 |
| 戊・癸 | 甲 |

### 日柱

```
入力: date (datetime), tz (tzinfo, default=JST)
出力: Kanshi

1. date を tz でローカル日付に変換
2. 1900-01-01 との日数差 diff を計算
3. index = (10 + diff) % 60
4. stem = TenStem(index % 10)
5. branch = TwelveBranch(index % 12)
```

基準日: 1900-01-01 = 甲戌 (index 10)。SetsuiriProvider 不要。

## 統合 API

```python
class SanmeiCalendar:
    """西暦日付から三柱干支を算出する統合エントリポイント。"""

    def __init__(
        self,
        setsuiri_provider: SetsuiriProvider,
        tz: tzinfo = JST,
    ) -> None: ...

    def three_pillars(self, date: datetime) -> ThreePillars: ...
    def year_pillar(self, date: datetime) -> Kanshi: ...
    def month_pillar(self, date: datetime) -> Kanshi: ...
    def day_pillar(self, date: datetime) -> Kanshi: ...
```

個別の pillar 関数はモジュールレベルでも公開（単体テスト・単体利用向け）。

## エラーハンドリング

```python
class SanmeiError(Exception):
    """sanmei-core の基底例外"""

class DateOutOfRangeError(SanmeiError):
    """対象範囲外の日付 (1864-2100) が指定された"""

class SetsuiriNotFoundError(SanmeiError):
    """指定年の節入りデータが見つからない"""
```

- 範囲外の日付（1864未満・2100超過）は明示的にエラー
- 節入りデータの欠損は Provider 側で検出しエラー
- 日柱計算は範囲チェック以外エラーにならない（純粋算術）
- 入力バリデーションは pydantic モデルに委任

## テスト戦略

### 日柱計算

基準日と既知の干支で検証。外部サイトや暦書と照合可能。

```python
# 基準日
assert day_pillar(datetime(1900, 1, 1)) == Kanshi(KINOE, INU, 10)
# 60日後（一巡）
assert day_pillar(datetime(1900, 3, 2)).index == 10
# 既知の日付（暦書から）
```

### 年柱計算（立春境界）

```python
# 2024年の立春: 2/4 17:27 JST
# 2/4 17:26 → 2023年の干支（癸卯）
# 2/4 17:27 → 2024年の干支（甲辰）
```

### 月柱計算

- 五虎遁年法テーブル全5パターンを網羅
- 各節入り日の境界前後をテスト

### 太陽黄経計算

- 国立天文台の暦象年表（公開データ）と照合
- 1864〜2100 の範囲で数十件のサンプルをスポットチェック
- 許容誤差: ±1時間

### MockSetsuiriProvider

```python
class MockSetsuiriProvider:
    """テスト用。固定の節入り日データを返す。"""
    def __init__(self, data: dict[int, list[SetsuiriDate]]) -> None: ...
```

三柱計算のテストでは Mock Provider を使い、天文計算とは独立して検証。

### テストデータの調達

- 国立天文台の暦象年表（公開データ）から数十年分の節入り日を取得
- 既知の有名人の命式（算命学書籍掲載）で統合テスト
- 境界ケース: 立春当日の時刻前後、元旦付近、閏年
