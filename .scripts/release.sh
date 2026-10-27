#!/usr/bin/env bash
# Cuts a GitHub release of origin/main: tag vX.Y.Z, title vX.Y.Z, generated release notes,
# marked Latest -- the same as the "Draft a new release" web form. The tag push triggers
# docker-build-push-v2.yml, which builds and pushes eventcally/eventcally:X.Y.Z, X.Y and
# sha-<short>; --watch follows that run.
#
#   .scripts/release.sh [patch|minor|major|vX.Y.Z] [--dry-run] [--yes] [--watch]
#                       [--notes-file FILE]
#
#   patch|minor|major  bump the newest vX.Y.Z tag (default: patch)
#   vX.Y.Z             release exactly this version
#   --dry-run          run the checks, print the version and the generated notes, create nothing
#   --yes              skip the confirmation prompt
#   --watch            wait for the Docker build of the tag and fail if it fails
#   --notes-file FILE  use these notes instead of generating them
#
# Requires an authenticated gh. Refuses unless the working tree is clean, the current branch
# is main, it equals origin/main and no check run on that commit failed or is still running
# (CI runs on PRs; main only gets merges that passed, so this mostly catches CodeQL & co).
set -euo pipefail

DOCKER_WORKFLOW="docker-build-push-v2.yml"
SEMVER_TAG='^v([0-9]+)\.([0-9]+)\.([0-9]+)$'

die() {
    echo "release: $*" >&2
    exit 1
}

bump="patch"
dry_run=0
assume_yes=0
watch=0
notes_file=""

while [ $# -gt 0 ]; do
    case "$1" in
    patch | minor | major) bump="$1" ;;
    v*) bump="$1" ;;
    --dry-run) dry_run=1 ;;
    --yes | -y) assume_yes=1 ;;
    --watch) watch=1 ;;
    --notes-file)
        [ $# -ge 2 ] || die "--notes-file needs a path"
        notes_file="$2"
        shift
        ;;
    -h | --help)
        sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
        exit 0
        ;;
    *) die "unknown argument: $1 (see --help)" ;;
    esac
    shift
done

if [ -n "$notes_file" ] && [ ! -s "$notes_file" ]; then
    die "notes file is missing or empty: $notes_file"
fi

command -v gh >/dev/null || die "gh is not installed"
gh auth status >/dev/null 2>&1 || die "gh is not authenticated (run: gh auth login)"

cd "$(git rev-parse --show-toplevel)"

# --- repository state --------------------------------------------------------------------

[ -z "$(git status --porcelain)" ] || die "working tree is not clean"
[ "$(git branch --show-current)" = "main" ] || die "not on main"

git fetch --quiet --tags origin main
sha="$(git rev-parse HEAD)"
[ "$sha" = "$(git rev-parse origin/main)" ] || die "main is not equal to origin/main (pull or push first)"

# --- version -----------------------------------------------------------------------------

last_tag="$(git tag --list 'v*' --sort=-v:refname | grep -E "$SEMVER_TAG" | head -n 1 || true)"
[ -n "$last_tag" ] || die "no vX.Y.Z tag found"

if [[ "$bump" =~ $SEMVER_TAG ]]; then
    tag="$bump"
else
    [[ "$last_tag" =~ $SEMVER_TAG ]]
    major="${BASH_REMATCH[1]}"
    minor="${BASH_REMATCH[2]}"
    patch="${BASH_REMATCH[3]}"
    case "$bump" in
    major) tag="v$((major + 1)).0.0" ;;
    minor) tag="v${major}.$((minor + 1)).0" ;;
    patch) tag="v${major}.${minor}.$((patch + 1))" ;;
    *) die "not a version or bump: $bump" ;;
    esac
fi

if git rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
    die "tag $tag already exists"
fi
newest="$(printf '%s\n%s\n' "$last_tag" "$tag" | sort -V | tail -n 1)"
[ "$newest" = "$tag" ] || die "$tag is not newer than $last_tag"

commit_count="$(git rev-list --count "$last_tag..$sha")"
[ "$commit_count" -gt 0 ] || die "no commits since $last_tag"

# --- checks on the release commit --------------------------------------------------------

repo="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
bad_checks="$(gh api --paginate "repos/$repo/commits/$sha/check-runs" \
    --jq '.check_runs[]
          | select(.status != "completed"
                   or (.conclusion | IN("success", "neutral", "skipped") | not))
          | "\(.name): \(.conclusion // .status)"')"
[ -z "$bad_checks" ] || die "checks on ${sha:0:7} are not green:
$bad_checks"

# --- summary -----------------------------------------------------------------------------

echo "Repository:  $repo"
echo "Release:     $last_tag -> $tag"
echo "Commit:      ${sha:0:7} $(git log -1 --format=%s "$sha")"
echo "Commits:     $commit_count since $last_tag"
echo

if [ -n "$notes_file" ]; then
    echo "--- notes ($notes_file) ---"
    cat "$notes_file"
else
    echo "--- generated notes ---"
    gh api "repos/$repo/releases/generate-notes" \
        -f tag_name="$tag" -f target_commitish="$sha" -f previous_tag_name="$last_tag" \
        --jq .body
fi
echo "-----------------------"
echo

if [ "$dry_run" -eq 1 ]; then
    echo "Dry run: nothing created."
    exit 0
fi

if [ "$assume_yes" -ne 1 ]; then
    read -r -p "Create release $tag and trigger the Docker build? [y/N] " answer
    case "$answer" in
    y | Y | yes) ;;
    *) die "aborted" ;;
    esac
fi

# --- release -----------------------------------------------------------------------------

notes_args=(--generate-notes --notes-start-tag "$last_tag")
if [ -n "$notes_file" ]; then
    notes_args=(--notes-file "$notes_file")
fi

gh release create "$tag" --target "$sha" --title "$tag" --latest "${notes_args[@]}"
git fetch --quiet --tags origin

if [ "$watch" -ne 1 ]; then
    echo "Docker build: gh run list --workflow $DOCKER_WORKFLOW --branch $tag"
    exit 0
fi

# --- follow the Docker build -------------------------------------------------------------

run_id=""
for _ in $(seq 1 30); do
    run_id="$(gh run list --workflow "$DOCKER_WORKFLOW" --branch "$tag" --event push \
        --limit 1 --json databaseId --jq '.[0].databaseId // empty')"
    [ -n "$run_id" ] && break
    sleep 5
done
[ -n "$run_id" ] || die "no $DOCKER_WORKFLOW run for $tag appeared within 150s"

gh run watch "$run_id" --exit-status --interval 15
version="${tag#v}"
echo "Pushed eventcally/eventcally:$version, :${version%.*} and :sha-${sha:0:7}"
