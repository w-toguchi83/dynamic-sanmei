# PDCA Cycle: sanmei-cli meishiki 表示変更

- Status: in_progress
- Created: 2026-03-02T20:00:00+09:00
- Updated: 2026-03-02T20:00:00+09:00

## Task: meishiki 表示変更
- ID: task-1
- Status: completed
- Dependencies: none
- Iteration: 1 (no adjust needed)

### Plan

#### DoD（完了条件）
1. 命式テキスト出力の列順が「日、月、年」（左から右）に変更されている
2. セクションヘッダー「三柱」→「干支」に変更されている
3. 列ヘッダー「年柱」「月柱」「日柱」→「日」「月」「年」に変更されている
4. 蔵干セクションにデバッグ情報（地支名+enum値、各蔵干のenum値）が表示されている
5. 十二大従星の表示順が「日→月→年」に変更されている
6. sanmei-core の pillar.py docstring から四柱推命由来の「柱」表現を修正している
7. 全テスト合格
8. `just check` 合格（lint + typecheck + test）

#### Steps

**Step 1: text.py — 干支セクション修正**
- 【三柱】→【干支】
- ヘッダー列順: `日  月  年` （左から右）
- 天干行: day.stem → month.stem → year.stem
- 地支行: day.branch → month.branch → year.branch

**Step 2: text.py — 蔵干セクション修正**
- ヘッダー列順: `日  月  年` （左から右）
- 列ヘッダー: 「日」「月」「年」
- デバッグ情報追加:
  - 「地支」行を追加: 各地支の漢字と enum 値を表示（例: `申(8)`）
  - 各蔵干の表示に enum 値を併記（例: `庚(6)` / `-(None)`）

**Step 3: text.py — 十二大従星表示順修正**
- `年: X  月: Y  日: Z` → `日: Z  月: Y  年: X`

**Step 4: テスト修正 — test_text_formatter.py**
- 「三柱」→「干支」のアサーション修正
- 「年柱」「月柱」「日柱」→ 新ヘッダーに修正
- 列順テスト追加（日が月より左にあることを検証）

**Step 5: sanmei-core — pillar.py docstring 修正**
- モジュール docstring: 「三柱（年柱・月柱・日柱）」→「年月日の干支」等
- ThreePillars docstring: 「三柱」→ 適切な算命学用語に修正

**Step 6: Check — `just check` 実行**

#### Test Strategy
- 既存テストを修正して新しい表示形式を検証
- 列順テスト: `result.index("日")` < `result.index("月")` < `result.index("年")` で検証
- デバッグ情報テスト: enum 値（数字）が蔵干セクションに含まれることを検証

### Do Log
#### Iteration 1
- text.py: 【三柱】→【干支】、列順 日/月/年、蔵干デバッグ数値追加、十二大従星順序変更
- test_text_formatter.py: アサーション修正、列順テスト追加、デバッグ情報テスト追加
- pillar.py: docstring 修正（三柱→年月日干支）
- 未使用 _stem_or_dash 関数削除、_stem_debug / _branch_debug 新規追加

### Check Log
#### Iteration 1
- Lint: PASS（ruff format 要修正 → 修正後 PASS）
- Typecheck: PASS（mypy 全3パッケージ OK）
- Tests: PASS（sanmei-cli 70テスト、sanmei-core 356テスト、dynamic-ontology 全 PASS）
- DoD:
  - [x] 列順が「日、月、年」に変更
  - [x] 「三柱」→「干支」
  - [x] 「年柱」「月柱」「日柱」→「日」「月」「年」
  - [x] 蔵干デバッグ情報（地支enum値、蔵干enum値）表示
  - [x] 十二大従星の表示順「日→月→年」
  - [x] pillar.py docstring 修正
  - [x] 全テスト合格
  - [x] `just check` 合格
- Result: PASS

### Adjust Log
（不要 — 1回で合格）

### Retrospective
#### 成功
- Plan 通りに全ステップを1イテレーションで完了
- 変更箇所が text.py + テスト + docstring に限定され、影響範囲が小さかった
- ruff format のみ要修正だったが、実質的な問題なし

#### 失敗と再発防止
| 失敗 | 根本原因 | 再発防止策 |
|------|----------|------------|
| ruff format check 失敗 | テストファイル内の長い assert 文の改行 | 実装後に `ruff format` を先に実行する |

#### 学び
- 表示変更は CLI フォーマッタに閉じており、core の API/モデル変更は不要だった
- `_append_hidden_stems` に branches パラメータを追加した際、呼び出し元の修正を忘れないこと（型チェックで捕捉可能）
- 蔵干のデバッグ表示は地支→初元→中元→本元の行構成で、各値に (enum値) を付与する形式が見やすい
