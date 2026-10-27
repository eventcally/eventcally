---
description: Create a PR, monitor checks and findings, fix them if confident else ask
argument-hint: [extra notes for the PR description]
---

# Create PR and Monitor

**Notes**: $ARGUMENTS

## Your Mission

Open a pull request for the current branch against `main`, then watch it until it is green and free of findings.

## Steps

1. **Prepare**
   - `git branch --show-current` and `git status`. On `main`, create a branch first. Commit or stop if the tree is dirty with unrelated changes.
   - Push the branch (`git push -u origin <branch>`).

2. **Create the PR**
   - `gh pr create --base main` with a clear title and a body covering summary, notable changes, breaking changes and how it was tested.
   - Reference the linked issue with `Fixes #N` if the plan or branch names one.

3. **Monitor**
   - Watch checks with `gh pr checks <pr> --watch` (run in the background, not polling in a loop).
   - Read findings: review comments, bot comments (Playwright, CodeQL, Socket, coverage) via `gh pr view <pr> --comments` and `gh api repos/{owner}/{repo}/pulls/<pr>/comments`.

4. **Handle failures and findings**
   - Read the failing job log (`gh run view <run> --log-failed`) and find the root cause.
   - **Confident** (clear cause, small and local fix, no behavior or scope change): fix it, run the relevant checks locally, commit, push, and keep monitoring.
   - **Not confident** (ambiguous finding, design trade-off, flaky or unrelated failure, security or breaking-change implications): stop and ask the user, with the evidence and your recommendation.
   - Never skip, disable or weaken a check to get green.

5. **Finish**
   - When all checks pass, report the PR URL, check status, `mergeable` state, anything fixed along the way, and open questions.
