# Session Context

## User Prompts

### Prompt 1

sanmei-cli について使い方などを READMEを作成して記載してください。CLAUDE.md も60行以内で適切なものを作成してください。
apps/sanmei-cli/README.md,CLAUDE.md

### Prompt 2

[Request interrupted by user]

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

### Prompt 4

README に記載の通りにやったのですが、コマンドの実行ができません。
内容は正しいですか？

```
 $ sanmei meishiki 1983-01-26                                                                                     [main]
zsh: command not found: sanmei
```

