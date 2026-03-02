# PDCA Cycle: 蔵干テキスト表示追加

- Status: completed
- Created: 2026-03-02T23:00:00+09:00
- Updated: 2026-03-02T23:10:00+09:00

## Task: format_meishiki に蔵干セクションを追加
- ID: task-1
- Status: completed
- Dependencies: none
- Iteration: 1

### Plan
- DoD:
  1. format_meishiki に【蔵干】セクションが表示される
  2. 年柱・月柱・日柱の本気・中気・余気が漢字で表示される
  3. 中気・余気が None の場合は「-」表示
  4. テストで蔵干セクションの存在と内容を検証
  5. just test-pkg sanmei-cli 合格
  6. just lint && just typecheck 合格
- Steps:
  1. テスト作成（TDD: red → green）
  2. format_meishiki に蔵干セクション追加（三柱の直後に配置）
  3. Check: テスト・リント・型チェック実行
- Test Strategy: 既存パターンに合わせ TestFormatMeishiki に蔵干テストを追加

### Do Log
#### Iteration 1
- 4テスト追加: hidden_stems_section, all_pillars, main_always_present, none_shown_as_dash
- Red 確認後、`_append_hidden_stems` ヘルパー関数と `_stem_or_dash` 関数を追加
- 三柱セクションの直後に蔵干セクションを配置

### Check Log
#### Iteration 1
- Tests: PASS (65 passed)
- Lint: PASS (ruff clean)
- Typecheck: PASS (text.py clean)
- DoD: 全6項目 PASS
- Result: PASS

### Retrospective
#### 成功
- TDD で Red→Green を1イテレーションで完了
- 既存パターン（_append_gogyo_balance）に倣ったヘルパー関数で一貫性を維持

#### 学び
- 小規模変更でも TDD の Red→Green サイクルが確実
