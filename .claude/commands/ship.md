---
description: Plan (Opus), implement (Sonnet), open the PR and merge — with a review gate after the plan and before the merge
argument-hint: <issue number(s) | issue URL | free text | path/to/prd.md> [--issue]
---

# Ship: Plan → Implement → PR → Merge

**Input**: $ARGUMENTS

## Objective

Take one task from input to merged PR. The phases are the existing commands; this command
only chains them. Don't repeat their instructions here — change the commands instead.

| Phase | Runs as | Model |
| ------- | -------- | ------- |
| Plan | `planner` agent (`.claude/commands/plan.md`) | Opus |
| Implement | `implementer` agent (`.claude/commands/implement.md`) | Sonnet |
| PR | `/pr` in this session | session model |
| Merge | `/merge` in this session | session model |

---

## Step 0: Parse the Input

| Input | Treat as |
| ------- | -------- |
| `123`, `#123`, `#12,#13`, issue URL | GitHub issue(s) |
| Issue reference followed by text (`#123 also handle mobile`) | Issue(s) plus extra notes |
| Path to a `.md` / `.prd.md` file | Plan input file |
| Anything else | Free-text feature description |
| Blank | Stop: "Usage: /ship <issue | text | prd.md> [--issue]" |

`--issue` (free text only): create an issue first with
`gh issue create --title "<short title>" --body "<the text>"` and continue with its number,
so the branch and the PR are linked to it. Without the flag, free text runs without an
issue.

Check the git state: on `main` with a dirty tree, stop ("Stash or commit changes first").

## Step 1: Plan

Call the Agent tool with `subagent_type: planner` and the input from Step 0 (issue
reference(s) plus notes, file path, or the text) as the prompt.

## Step 2: Gate 1 — Plan Review

Show the user the plan path, the summary and the planner's assumptions and open questions.
Then ask (AskUserQuestion):

- **Implement** (recommended when there are no open questions)
- **Change the plan** — apply the user's changes to the plan file yourself, show the
  changes, and ask again
- **Stop** — print `/implement <plan path>` so the user can continue later

## Step 3: Implement

Call the Agent tool with `subagent_type: implementer` and the plan path as the prompt.

- **COMPLETE**: show the status, test tiers and deviations, then continue.
- **BLOCKED**: show the question, the evidence and the recommendation and ask the user.
  Then either resume with SendMessage to the same implementer (answer included) or stop.

## Step 4: PR

Run `/pr` (Skill tool, skill `pr`). It commits, pushes, opens the PR with `Fixes #N` when an
issue is linked, and watches the checks until they are green, asking when not confident.

## Step 5: Gate 2 — Merge

When the PR is green, show its URL, check status and anything `/pr` fixed. Ask
(AskUserQuestion): **Merge now** or **Stop** (the PR stays open; `/merge` later).

On **Merge now**, run `/merge` (Skill tool, skill `merge`).

## Output

```markdown
## Shipped

| Phase | Result |
| ------- | -------- |
| Plan | `{plan path}` |
| Implement | {COMPLETE, report path, tiers run} |
| PR | {URL, checks} |
| Merge | {merged / left open} |

**Issue**: {#N, closes on merge / none}
```
