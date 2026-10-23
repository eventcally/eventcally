---
description: Merge the PR, switch to main, pull, delete the issue branch locally and remote
argument-hint: [pr-number]
---

# Merge PR and Clean Up

**PR**: $ARGUMENTS (default: the PR of the current branch)

## Steps

1. **Identify**
   - `git branch --show-current` and `gh pr view $ARGUMENTS --json number,headRefName,state,mergeable,statusCheckRollup`.
   - Stop and report if the PR is not open, not mergeable, or has failing checks. Do not merge past red checks.

2. **Merge**
   - `gh pr merge <number> --merge` (this repo's history uses merge commits). Do not pass `--delete-branch`; clean up explicitly below.

3. **Switch and pull**
   - `git checkout main && git pull`.

4. **Delete the issue branch**
   - Locally: `git branch -d <headRefName>`.
   - Remote: `git push origin --delete <headRefName>` (skip if GitHub already removed it).

5. **Report**
   - Confirm the merge, that `main` is up to date, both branch deletions, and any leftover untracked or dirty files.
