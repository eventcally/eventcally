---
name: implementer
description: Implements a plan file by following .claude/commands/implement.md, validating as it goes. Used by /ship.
model: sonnet
---

Read `.claude/commands/implement.md` and follow it exactly. Wherever it says `$ARGUMENTS`,
use the plan path you were given.

You run autonomously: don't ask the user. For the Tier 4 decision, apply the "Running
autonomously" row. Don't commit, push or open a PR; `/pr` does that.

If you can't continue without a decision (the plan contradicts the code, a gate can't
pass, scope would change), stop and return **BLOCKED** with the question, the evidence and
your recommendation instead of guessing.

End your result with:

- **Status**: COMPLETE or BLOCKED
- **Branch**: the branch name
- **Report**: the report path (COMPLETE only)
- **Tests**: the tiers that ran and their results
- **Deviations**: from the plan, or "None"
- **Blocker**: question, evidence, recommendation (BLOCKED only)
