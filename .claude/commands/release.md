---
description: Cut a GitHub release of main (tag, generated notes) and follow the Docker build
argument-hint: [patch|minor|major|vX.Y.Z]
---

# Release

**Version**: $ARGUMENTS (default: propose one from the changes since the last tag)

Everything goes through `.scripts/release.sh`; never create tags or releases by hand.

## Steps

1. **Check and preview**
   - `git checkout main && git pull` if the tree is clean and you are not on main; otherwise stop and report.
   - Run `.scripts/release.sh <bump> --dry-run` (use `patch` while the version is still undecided). Stop and report if it refuses (dirty tree, red or running checks, no commits since the last tag).

2. **Pick the version** (skip if `$ARGUMENTS` names one)
   - Read the merged PRs since the last tag: `git log --merges --format='%s%n%b' <last_tag>..origin/main` plus the generated notes from the dry run.
   - Propose `minor` when any PR adds or changes user-visible features, BFF/API behaviour, migrations or config/env vars; `patch` when it is only fixes, dependency bumps, CI, docs, tests or refactoring. Never propose `major` on your own.
   - List any change that needs attention at deploy time (Alembic migration, new or renamed env var, new Celery task, changed docker-compose service) — the deployment repo is updated by hand.

3. **Confirm**
   - Show the version, the commit, the generated notes and the deploy-time notes, then ask the user to confirm before creating anything. A release is public and triggers the Docker push.
   - If the user wants edited notes, write them to a file in the scratchpad and pass `--notes-file <path>`.

4. **Release**
   - `.scripts/release.sh <version> --yes --watch [--notes-file <path>]` (run in the background; the Docker build takes several minutes).

5. **Report**
   - The release URL (`gh release view <tag> --json url --jq .url`), the Docker run result and the pushed image tags, plus the deploy-time notes from step 2. If the Docker build failed, show the failing step (`gh run view <id> --log-failed`) and stop; do not delete the release or the tag.
