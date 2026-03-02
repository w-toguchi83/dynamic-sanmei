# PDCA Cycle: sanmei-cli README.md + CLAUDE.md 作成

- Status: completed
- Created: 2026-03-02T23:00:00+09:00
- Updated: 2026-03-02T23:05:00+09:00

## Task: README.md と CLAUDE.md の作成
- ID: task-1
- Status: completed
- Dependencies: none
- Iteration: 1

### Plan
- DoD:
  1. apps/sanmei-cli/README.md が存在し、以下を含む:
     - プロジェクト概要
     - インストール方法
     - 全コマンドの使い方（meishiki, taiun, nenun, isouhou）
     - 各オプションの説明
     - 出力例（テキスト/JSON）
     - 開発コマンド
  2. apps/sanmei-cli/CLAUDE.md が存在し、60行以内で以下を含む:
     - パッケージ構造
     - 開発コマンド
     - コーディングルール/設計パターン
  3. 内容がソースコードと整合している

- Steps:
  1. README.md を作成（使い方中心のドキュメント）
  2. CLAUDE.md を作成（60行以内、開発者/AI向け情報）
  3. 内容の正確性を目視確認

- Test Strategy: ドキュメントのためテスト不要。内容の正確性をソースコードと照合して検証。
