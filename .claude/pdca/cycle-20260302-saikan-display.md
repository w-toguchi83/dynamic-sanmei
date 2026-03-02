# PDCA Cycle: 蔵干特定表示 + CLI 表示修正

- Status: completed
- Created: 2026-03-02T18:00:00+09:00
- Updated: 2026-03-02T21:00:00+09:00

## Task: CLI 蔵干表示の列ズレ修正 + デバッグ数字削除
- ID: task-1
- Status: completed
- Dependencies: none
- Iteration: 1

### Plan
- DoD:
  - 干支・蔵干セクションのヘッダー（日/月/年）とデータ行が揃っている
  - 蔵干のデバッグ数字 (N) が非表示
  - 蔵干セクションから地支行を削除
  - 既存テスト全合格
  - `just check` 合格
- Steps:
  1. `_cjk_ljust(text, width)` ヘルパーを text.py に追加
  2. 干支・蔵干セクションで `_cjk_ljust` 使用
  3. `_stem_debug`/`_branch_debug` 削除、`_stem_or_dash` 追加
  4. 蔵干セクションから「地支」行を削除
  5. テスト更新

### Check Log
#### Iteration 1
- Tests: PASS (73 passed)
- Lint: PASS
- DoD: all items checked
- Result: PASS

### Retrospective
- Worktree エージェントで正しく完了。CJK幅計算のアプローチは堅実。

---

## Task: 蔵干特定テーブル・ドメインモデル・算出ロジック (sanmei-core)
- ID: task-2
- Status: completed
- Dependencies: none
- Iteration: 2

### Plan
（略: 上記参照）

### Do Log
#### Iteration 1
- Worktree エージェントが全ファイルを作成したが、old field names (main/middle/minor) を使用
- 辰・未・戌のテスト値が pre-swap で不正確
- コミットなしで worktree に放置

#### Iteration 2
- メインブランチに手動で正しいファイルを適用
- HiddenStems の hongen/chuugen/shogen フィールド名を使用
- 既存テストヘルパー (test_fortune.py, test_fortune_analyzer.py) に ZoukanTokutei ダミー追加
- test_meishiki_calculator.py に統合テスト追加（書籍例 1988-11-01）

### Check Log
#### Iteration 2
- Tests: PASS (664 passed in sanmei-core)
- Lint: PASS
- Type check: PASS
- DoD: all items checked
- Result: PASS

### Adjust Log
#### Iteration 1
- Failure: Worktree エージェントが old field names を使用
- Root Cause: Worktree は古いコミットベースで、rename 後のフィールド名を持っていなかった
- Plan Changes: メインブランチに直接適用する方式に切り替え

### Retrospective
- Worktree は HEAD 時点のコードを持つが、未コミットの変更がないため古いフィールド名が残る
- HiddenStems のリネーム後は、worktree エージェントにリネーム情報を明示的に渡す必要あり
- 辰・未・戌の swap は特に見落としやすい — テスト値は手計算で確認必須

---

## Task: 蔵干特定の CLI 表示 + ドメインドキュメント更新
- ID: task-3
- Status: completed
- Dependencies: task-1, task-2
- Iteration: 1

### Plan
- DoD:
  - 蔵干セクションに蔵干特定値（日数）と選択された干を表示
  - docs/domain/02_Chapter2 に蔵干特定の説明追加
  - CLI テスト更新
  - `just check` 合格

### Do Log
#### Iteration 1
- text.py: `_append_hidden_stems()` に `zoukan_tokutei` 引数追加
- ヘッダー: `【蔵干】(節入り日からN日目)` 表示
- 蔵干特定行: `蔵干特定  庚(本元)  戊(本元)  戊(本元)` 表示
- ラベル列幅を 8→10 に拡張（蔵干特定=4CJK=8幅、パディング確保のため）
- docs/domain/02_Chapter2 に §2.5 蔵干特定 セクション追加
- CLI テスト: 2件追加 (zoukan_tokutei_days_shown, zoukan_tokutei_row_shown)

### Check Log
#### Iteration 1
- Tests: PASS (1286 total: 549 + 664 + 73)
- Lint: PASS
- Type check: PASS (3 packages clean)
- DoD: all items checked
- Result: PASS

### Retrospective
### 成功
- CJK幅計算 + 可変ラベル幅で綺麗なアライメント達成
- ドメインモデル → テーブル → 算出 → 統合 → CLI の一貫したパイプライン

### 失敗と再発防止
| 失敗 | 根本原因 | 再発防止策 |
|------|----------|------------|
| Worktree エージェントが古いフィールド名使用 | Worktree は HEAD ベースで未コミット変更なし | リネーム後はエージェントに変更情報を明示伝達 |
| 蔵干特定ラベル(8幅)がパディング不足 | CJK 4文字=8幅でぴったり | ラベル列幅は最長ラベル+2以上に設定 |

### 学び
- ruff format は `just check` で自動検出されるので手動実行不要（ただし修正は必要）
- Meishiki へのフィールド追加時は全テストヘルパーの更新が必要（grep Meishiki( で洗い出し）
