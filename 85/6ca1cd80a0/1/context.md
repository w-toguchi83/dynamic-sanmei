# Session Context

## User Prompts

### Prompt 1

質問: 蔵干の求め方について教えてください。
1988年11月01日生まれの人について、本に記載されている蔵干の期待値とこのプログラムでの出力が違いました。
原因を知りたいです。

書籍に記載されている期待値

初元 (年)乙, (月)辛, (日)戊
中元 (年)癸, (月)丁, (日)壬
本元 (年)戊, (月)戊, (日)庚

でした。

### Prompt 2

本元は一致していますね。ではここから星を出す時のロジックはどうなっていますか？　星も書籍とは異なっています。

### Prompt 3

Base directory for this skill: /Users/toguchi/.claude/skills/task-pdca

# Task PDCA

PDCAサイクルでタスクを実装・完成させるプロセススキル。

**コア原則:** Plan → Do → Check → Adjust のループで品質を担保し、振り返りで再発防止、Feedback でナレッジを永続化する。

## サブコマンド

| コマンド | 説明 |
|----------|------|
| `/task-pdca` | 新規PDCAサイクルを開始（タスク情報を入力） |
| `/task-pdca continue` | 中断したサイクルを再開 |
| `/task-pdca clean` | 完了済みサイクルの状態ファイルを削除 |

## いつ使うか

```dot
digraph when_to_use {
    "タスク実装の依頼?" [shape=diamond];
    "中断からの再開?" [shape=diamond];
    "完了済みの清掃?" [shape=...

