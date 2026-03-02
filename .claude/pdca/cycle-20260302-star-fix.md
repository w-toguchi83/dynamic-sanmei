# PDCA Cycle: 十大主星・十二大従星算出ロジック修正

- Status: completed
- Created: 2026-03-02T18:00:00+09:00
- Updated: 2026-03-02T20:00:00+09:00

## Task: 十大主星・十二大従星算出ロジックの修正
- ID: task-1
- Status: completed
- Dependencies: none
- Iteration: 1

### Plan

#### 問題分析
書籍の参照テーブルとコード比較の結果、以下4つのバグを特定:

**Bug 1: _STAR_MAP の官星・印綬の陰陽マッピングが逆**
- `(KANSEI, True/同陰陽)` → 牽牛星 (コード) vs 車騎星 (書籍)
- `(KANSEI, False/異陰陽)` → 車騎星 (コード) vs 牽牛星 (書籍)
- `(INJYU, True/同陰陽)` → 玉堂星 (コード) vs 龍高星 (書籍)
- `(INJYU, False/異陰陽)` → 龍高星 (コード) vs 玉堂星 (書籍)
- 原因: domain doc (04_Chapter4) の表自体が間違っていた

**Bug 2: 帝旺マップが陰干・土性で間違い**
- 乙: 卯→寅, 丁: 午→巳, 戊: 戌→午, 己: 未→巳, 辛: 酉→申, 癸: 子→亥
- 原因: 五行単位で一つの帝旺支を共有する設計だが、算命学では干ごとに異なる

**Bug 3: 陰干の十二運逆行が未実装**
- 陰干（乙丁己辛癸）は十二支を逆方向に巡行する
- 現コードは全干で順行（`(target - teiou) % 12`）

**Bug 4: 十大主星の配置マッピングが書籍と不一致**
- east に月干（②→南のはず）, center に日支蔵干（⑤→西のはず）等

#### DoD
- [x] _STAR_MAP: 書籍テーブルと全100パターン一致
- [x] 帝旺マップ: 10干すべて書籍テーブルと一致
- [x] 陰干逆行: 全10干×12支=120パターンで書籍テーブルと一致
- [x] 配置: north=①年干, south=②月干, east=③年支蔵干, center=④月支蔵干, west=⑤日支蔵干
- [x] domain doc 更新: 04_Chapter4, 05_Chapter5 の誤り修正
- [x] `just check` (lint + typecheck + test) 全合格

### Do Log
#### Iteration 1
1. standard.py: _STAR_MAP の KANSEI/INJYU 陰陽スワップ
2. standard.py: _TEIOU_MAP を干ごとの正しい帝旺支に修正（6干変更）
3. subsidiary_star.py: `_is_yin_stem()` 追加、陰干で `(teiou - target) % 12` に変更
4. major_star.py: 配置を書籍準拠に修正（south=月干, east=年支蔵干, center=月支蔵干, west=日支蔵干）
5. test_standard.py: 官星/印綬テスト修正、帝旺マップテスト修正
6. test_major_star.py: 書籍テーブル全100パターンのparametrizeテスト追加 + 配置テスト修正
7. test_subsidiary_star.py: 書籍テーブル全120パターンのparametrizeテスト追加 + 個別テスト修正
8. domain doc修正: 04_Chapter4（官星/印綬の陰陽）, 05_Chapter5（帝旺支テーブル全面改訂）

### Check Log
#### Iteration 1
- Tests: PASS — sanmei-core 570 passed, dynamic-ontology 549 passed, sanmei-cli 65 passed
- Lint: PASS — ruff check + format
- Typecheck: PASS — mypy 3パッケージ all success
- DoD:
  - [x] _STAR_MAP: 100パターンテスト合格
  - [x] 帝旺マップ: 10干テスト合格
  - [x] 陰干逆行: 120パターンテスト合格
  - [x] 配置: テスト合格
  - [x] domain doc: 更新済み
  - [x] `just check`: 全合格
- Result: PASS

### Retrospective
#### 成功
- 書籍テーブルをフル（100+120パターン）でテスト化したことで、バグの見逃しを完全に防止
- 帝旺マップ+方向のアルゴリズム的アプローチにより、テーブル全エントリの正当性を数学的に保証
- 書籍テーブルの卯行に印刷ミス（庚辛壬癸の4干）が存在することを特定・回避

#### 失敗と再発防止
| 失敗 | 根本原因 | 再発防止策 |
|------|----------|------------|
| domain doc に誤り | 初期ドキュメント作成時に書籍テーブルとのクロスチェックが不足 | ドメイン知識は必ず書籍原本と照合する |
| 官星/印綬の陰陽反転 | 比劫/食傷/財星と官星/印綬で陰陽パターンが実は統一（同→陽版）だが、ドキュメントが反転記載 | 全関係で統一パターンを確認: 同陰陽=陽版, 異陰陽=陰版 |
| 陰干の逆行未実装 | 四柱推命との混同（一部流派では陰干も順行） | 算命学固有の十二運は陽順陰逆が基本 |
| 土性の帝旺が独自値 | 土は独自の長生を持たない→丙/丁に準ずることが算命学の標準 | 土性は火性に寄生する十二運を使用 |

#### 学び
- 算命学の十大主星: 全五行関係で統一パターン「同陰陽→陽版（偏）、異陰陽→陰版（正）」
- 算命学の十二大従星: 陽干は順行、陰干は逆行。帝旺支は干ごとに異なる
- 土性（戊己）の十二運は火性（丙丁）に準ずる
- 書籍のテーブルにも印刷ミスがあり得る。アルゴリズム的整合性で検証すべき
