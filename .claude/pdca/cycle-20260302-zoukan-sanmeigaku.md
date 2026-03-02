# PDCA Cycle: 蔵干を算命学の体系（初元/中元/本元）に修正

- Status: completed
- Created: 2026-03-02T22:00:00+09:00
- Updated: 2026-03-02T22:30:00+09:00

## 背景

現在の蔵干実装は四柱推命の体系（本気/中気/余気）に基づいている。
算命学では初元/中元/本元という体系を使い、順序（辰・未・戌で中元と初元が入れ替わり）も異なる。

参考: https://sanmeigaku-academy.online/2017/10/13/蔵干の計算と節入り時刻について/

### 算命学の正しい二十八元表

| 十二支 | 初元 | 中元 | 本元 |
|--------|------|------|------|
| 子 | — | — | 癸 |
| 丑 | 癸 | 辛 | 己 |
| 寅 | 戊 | 丙 | 甲 |
| 卯 | — | — | 乙 |
| 辰 | 乙 | 癸 | 戊 |
| 巳 | 戊 | 庚 | 丙 |
| 午 | 己 | — | 丁 |
| 未 | 丁 | 乙 | 己 |
| 申 | 戊 | 壬 | 庚 |
| 酉 | — | — | 辛 |
| 戌 | 辛 | 丁 | 戊 |
| 亥 | — | 甲 | 壬 |

中元は三合会局に基づく: 火局(寅午戌)→丙/丁, 水局(申子辰)→壬/癸, 金局(巳酉丑)→庚/辛, 木局(亥卯未)→甲/乙

### 四柱推命との違い（辰・未・戌）

| 支 | 旧 middle | 旧 minor | 算命学 初元 | 算命学 中元 |
|----|-----------|-----------|-----------|-----------|
| 辰 | 乙(=初元) | 癸(=中元) | 乙 | 癸 |
| 未 | 丁(=初元) | 乙(=中元) | 丁 | 乙 |
| 戌 | 辛(=初元) | 丁(=中元) | 辛 | 丁 |

→ 辰・未・戌の chuugen/shogen を swap した

---

## Task 1: HiddenStems モデルのフィールド名変更
- ID: task-1
- Status: completed
- Dependencies: none
- Iteration: 1

### Plan

**DoD:**
- [x] HiddenStems のフィールドが `hongen`, `chuugen`, `shogen` に変更されている
- [x] 全ての参照箇所が更新されている
- [x] `just check` 合格

### Do Log
#### Iteration 1
- `domain/hidden_stems.py`: main→hongen, middle→chuugen, minor→shogen + docstring更新
- `tables/hidden_stems.py`: 全フィールド名更新
- `calculators/major_star.py`: .main→.hongen
- `calculators/gogyo_balance.py`: .main/.middle/.minor→.hongen/.chuugen/.shogen
- テスト14ファイル更新: domain, tables, schools, protocol, calculators (gogyo_balance, meishiki_calculator, fortune, fortune_analyzer)
- CLI: formatters/text.py, test_text_formatter.py

### Check Log
#### Iteration 1
- Tests: PASS (352 sanmei-core + 65 sanmei-cli = 417 passed)
- Lint: PASS (ruff check + format)
- Typecheck: PASS (mypy strict on 3 packages)
- DoD: 全項目 PASS
- Result: PASS

---

## Task 2: 蔵干テーブルの値修正（辰・未・戌の swap + 午の修正）
- ID: task-2
- Status: completed
- Dependencies: task-1
- Iteration: 1

### Plan

**DoD:**
- [x] 辰・未・戌の chuugen/shogen が算命学の二十八元表と一致
- [x] 午の蔵干が chuugen=None, shogen=己 に修正されている
- [x] テーブルテストが新しい値で通る
- [x] `just check` 合格

### Do Log
#### Iteration 1
Task 1 と同時に実施。tables/hidden_stems.py で以下を変更:
- 辰: chuugen=癸, shogen=乙 (旧: middle=乙, minor=癸)
- 未: chuugen=乙, shogen=丁 (旧: middle=丁, minor=乙)
- 戌: chuugen=丁, shogen=辛 (旧: middle=辛, minor=丁)
- 午: shogen=己, chuugen=None (旧: middle=己 → 算命学では中元なし、初元のみ)

### Check Log
#### Iteration 1
- Tests: PASS
- 1988-11-01 の出力が書籍の期待値と完全一致
- Result: PASS

---

## Task 3: CLI 表示の修正（用語 + 表示順）
- ID: task-3
- Status: completed
- Dependencies: task-1
- Iteration: 1

### Do Log
#### Iteration 1
- formatters/text.py: 表示順を 初元→中元→本元 に変更、用語も更新
- test_text_formatter.py: 「本気」→「本元」、.main→.hongen 等

### Check Log
#### Iteration 1
- Tests: PASS (65 passed)
- Result: PASS

---

## Task 4: ドキュメント更新
- ID: task-4
- Status: completed
- Dependencies: task-2
- Iteration: 1

### Do Log
#### Iteration 1
- docs/domain/02_Chapter2_Basics_of_Kanshi.md Section 2.4 更新:
  - セクション名に「二十八元」追加
  - 初元/中元/本元の定義説明追加（三合会局の説明含む）
  - テーブルを算命学の順序（初元→中元→本元）に変更
  - 辰・未・戌・午のテーブル値を算命学に合わせて修正
  - 四柱推命との違いに関する注記を追加

### Check Log
#### Iteration 1
- Result: PASS

---

## Retrospective

### 成功
- 事前の調査（Web検索）で算命学と四柱推命の違いを正確に把握できた
- 三合会局の原理を理解することで、中元の決定ロジックを論理的に検証できた
- 全参照箇所を grep で漏れなく特定し、一括更新できた

### 失敗と再発防止

| 失敗 | 根本原因 | 再発防止策 |
|------|----------|------------|
| 初回の grep で test_fortune.py, test_fortune_analyzer.py を見落とした | `HiddenStems(main=` というパターンでの検索が不十分 | replace_all 後に `grep HiddenStems\(main=` で残存確認を必ず行う |
| 初期のドメインドキュメントが四柱推命の体系だった | ドキュメント作成時のソース検証不足 | 算命学の用語・テーブルは複数の算命学専門ソースで裏取りする |

### 学び
- 算命学の蔵干（二十八元）は四柱推命の蔵干（本気/中気/余気）と含まれる干のセットは同じだが、名称と順序が異なる
- 算命学の中元は三合会局で決定される: 火局→丙/丁、水局→壬/癸、金局→庚/辛、木局→甲/乙
- 辰・未・戌（四庫の3支）と午で四柱推命と算命学の順序が入れ替わる
- 午は算命学では中元なし（初元=己、本元=丁のみ）、亥は初元なし（中元=甲、本元=壬のみ）
