# PDCA Cycle: 大運表示改善

- Status: completed
- Created: 2026-03-04T00:00:00+09:00
- Updated: 2026-03-04T00:01:00+09:00

## Task: 大運CLI表示改善
- ID: task-1
- Status: completed
- Dependencies: none
- Iteration: 1

### Plan
- DoD:
  1. 期間列が「第1句」「第2句」...の形式で表示される
  2. 最初のデータ行に月干支が表示され、年齢が `0-(start_age-1)歳` (start_age>=2) または `0歳` (start_age==1) となる
  3. ヘッダー列名が「期間」→適切な名称に更新されている
  4. 既存テスト + 新規テストが全て合格
  5. `just check` (lint + typecheck + test) が合格

- Steps:
  1. `format_taiun` のシグネチャに月干支 (Kanshi) パラメータを追加
  2. フォーマッタ内でヘッダー列「期間」の幅を「第10句」に合わせて調整
  3. 月干支を最初のデータ行として追加（年齢は start_age に応じて算出）
  4. 各大運期間の表示を「第N句」に変更
  5. taiun コマンドで `format_taiun` 呼び出し時に月干支を渡す
  6. テストを更新: conftest にフィクスチャ追加、既存テスト修正、新規テスト追加

- Test Strategy: 既存テスト修正 + 月干支行・第N句表示の新規テスト追加

### Do Log
#### Iteration 1
- `format_taiun` に `month_kanshi_kanji: str` パラメータ追加
- ヘッダー列を CJK 幅対応に変更、「開始年齢」→「立運」
- 月干支行を最初のデータ行に追加（start_age に応じた年齢表示）
- 各期間の表示を `第N句` に変更
- taiun コマンドで `meishiki.pillars.month.kanji` を渡すよう修正
- conftest に `month_kanshi_kanji` フィクスチャ追加
- テスト: 既存5件修正 + 新規3件追加（第N句、月干支行、月干支年齢）

### Check Log
#### Iteration 1
- Tests: PASS (76 passed)
- Lint: PASS
- Typecheck: PASS
- DoD:
  - [x] 期間列が「第1句」「第2句」...の形式で表示される
  - [x] 最初のデータ行に月干支が表示され年齢が正しい
  - [x] ヘッダー列名が更新されている
  - [x] 既存テスト + 新規テストが全て合格
  - [x] `just check` が合格
- Result: PASS

### Retrospective
#### 成功
- フォーマッタ変更のみで完了（core の API/モデル変更不要）
- CJK 幅対応の `_cjk_ljust` を再利用して列揃え

#### 学び
- フォーマッタへの追加パラメータは最小限（kanji 文字列のみ）にすることで結合を低く保てた
