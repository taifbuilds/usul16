#!/usr/bin/env bash
#
# Publish commentary rows to production as a delta.
#
# Run from a developer machine, from the repository root. Code deploys itself
# when main is pushed (.github/workflows/deploy.yml); the database does not,
# and this is the missing half.
#
#   ./infra/deploy/deploy-db.sh mirat-al-uqul
#   ./infra/deploy/deploy-db.sh sharh-al-mazandarani --dry-run
#
# It never replaces the production database. The research copy is ~3 GB and
# almost all of it is unrelated to commentary; shipping the file would both
# waste the upload and overwrite whatever else production has. Only rows whose
# content differs travel, and they travel keyed by public_id — production is a
# separate copy of the corpus and its hadiths.id values are not guaranteed to
# match, so a raw hadith_id would attach commentary to the wrong report.
#
# Order matters. Everything that can fail without touching production happens
# first: fingerprint the target, export the delta, ship it, migrate, validate
# every public_id, and only then write — inside one transaction, after a backup.

set -euo pipefail

SOURCE_KEY="${1:-}"
DRY_RUN=""
[[ "${2:-}" == "--dry-run" ]] && DRY_RUN="--dry-run"

if [[ -z "$SOURCE_KEY" ]]; then
  echo "usage: $0 <source-key> [--dry-run]" >&2
  echo "  e.g. $0 mirat-al-uqul" >&2
  exit 2
fi

HOST="${USUL16_HOST:-deploy@91.98.192.21}"
REMOTE_APP="${USUL16_REMOTE_APP:-/home/deploy/app/eshia-research}"
REMOTE_INCOMING="${USUL16_REMOTE_INCOMING:-/home/deploy/incoming}"
LOCAL_DB="${DATABASE_FILE:-eshia-research/eshia_research.db}"
# Prefer the project venv. A virtualenv puts its interpreter in bin/ on POSIX
# and Scripts/ on Windows, so both are tried before falling back to PATH —
# otherwise Git Bash silently runs whatever `python` happens to be there, which
# will not have this project installed.
if [[ -z "${PYTHON:-}" ]]; then
  for candidate in \
    eshia-research/.venv/bin/python \
    eshia-research/.venv/Scripts/python.exe \
    python3 \
    python; do
    if command -v "$candidate" >/dev/null 2>&1 || [[ -x "$candidate" ]]; then
      PYTHON="$candidate"
      break
    fi
  done
fi
if ! "$PYTHON" -c "import eshia_research" >/dev/null 2>&1; then
  echo "'$PYTHON' cannot import eshia_research. Activate the venv or set PYTHON=..." >&2
  exit 1
fi
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# The remote venv python, and the app dir, in one place.
remote() { ssh "$HOST" "cd '$REMOTE_APP' && $*"; }
remote_py() { remote ".venv/bin/python -m eshia_research.cli $*"; }

echo "==> Deploying '$SOURCE_KEY' to $HOST"
[[ -n "$DRY_RUN" ]] && echo "    DRY RUN: production will be validated but not written"

if [[ ! -f "$LOCAL_DB" ]]; then
  echo "Local database not found at $LOCAL_DB" >&2
  exit 1
fi

# --- 1. What does production already have? --------------------------------
# This is what makes the transfer a delta on the wire rather than a full dump
# that gets diffed after it lands.
echo "==> [1/8] Fingerprinting production"
remote_py "commentary-manifest '$SOURCE_KEY' --output '$REMOTE_INCOMING/manifest-$SOURCE_KEY.json'" \
  || { echo "Could not read the production manifest. Is the migration applied?" >&2; exit 1; }
scp -q "$HOST:$REMOTE_INCOMING/manifest-$SOURCE_KEY.json" "$WORK/manifest.json"
echo "    manifest: $(wc -c <"$WORK/manifest.json") bytes"

# --- 2. Export only what differs ------------------------------------------
echo "==> [2/8] Exporting the delta"
DELTA="$WORK/$SOURCE_KEY-$STAMP.json.gz"
# Absolute, because the CLI runs from the repo root while the database lives a
# directory down — a relative URL silently resolves to the wrong place.
LOCAL_DB_ABS="$(cd "$(dirname "$LOCAL_DB")" && pwd)/$(basename "$LOCAL_DB")"
# Git Bash reports `/c/Users/...`, which a Windows Python cannot open.
if command -v cygpath >/dev/null 2>&1; then
  LOCAL_DB_ABS="$(cygpath -m "$LOCAL_DB_ABS")"
fi
DATABASE_URL="sqlite:///$LOCAL_DB_ABS" \
  "$PYTHON" -m eshia_research.cli export-commentary-delta "$SOURCE_KEY" \
    --manifest "$WORK/manifest.json" --output "$DELTA" \
  || { echo "Export failed." >&2; exit 1; }

DELTA_BYTES=$(wc -c <"$DELTA")
echo "    delta: $DELTA_BYTES bytes"
if [[ "$DELTA_BYTES" -lt 200 ]]; then
  echo "    Delta is empty — production already matches. Nothing to do."
  exit 0
fi

# --- 3. Ship it -----------------------------------------------------------
echo "==> [3/8] Uploading"
remote "mkdir -p '$REMOTE_INCOMING'"
scp -q "$DELTA" "$HOST:$REMOTE_INCOMING/"
REMOTE_DELTA="$REMOTE_INCOMING/$(basename "$DELTA")"

# --- 4. Schema ------------------------------------------------------------
# hadith_commentaries may not exist on production yet. Alembic is idempotent,
# so this is safe to run every time.
echo "==> [4/8] Applying migrations"
remote ".venv/bin/alembic upgrade head"

# --- 5. Back up BEFORE any write -----------------------------------------
echo "==> [5/8] Backing up the production database"
BACKUP="eshia_research.db.bak-$STAMP"
remote "cp -v eshia_research.db '$BACKUP'"
ROLLBACK="ssh $HOST 'cd $REMOTE_APP && cp $BACKUP eshia_research.db && sudo systemctl restart usul16-api'"

# --- 6. Validate every public_id, then import in one transaction ----------
# The import validates first and aborts before writing anything, so a delta
# built against a different corpus cannot half-apply.
echo "==> [6/8] Validating and importing"
if ! remote_py "import-commentary-delta '$REMOTE_DELTA' $DRY_RUN"; then
  echo >&2
  echo "IMPORT FAILED — production was not modified (the import aborts before writing)." >&2
  echo "If you need to restore anyway:" >&2
  echo "  $ROLLBACK" >&2
  exit 1
fi

if [[ -n "$DRY_RUN" ]]; then
  echo "==> Dry run complete. Nothing was written."
  echo "    Backup taken anyway: $BACKUP"
  exit 0
fi

# --- 7. Restart and check the service actually serves ---------------------
# `systemctl is-active` reports a unit that starts and then 500s as healthy,
# so assert on real responses instead.
echo "==> [7/8] Restarting the API"
remote "sudo systemctl restart usul16-api"

echo "==> [8/8] Verifying over HTTP"
ok=0
for _ in $(seq 1 30); do
  if remote "curl -fsS localhost:8000/health >/dev/null"; then ok=1; break; fi
  sleep 2
done
if [[ "$ok" -ne 1 ]]; then
  echo "API did not come back healthy. Roll back with:" >&2
  echo "  $ROLLBACK" >&2
  exit 1
fi

# A real data endpoint, not just /health: prove the rows are actually served.
SAMPLE=$(remote "curl -fsS 'localhost:8000/hadiths/alkafi-2' | head -c 4000" || true)
if [[ "$SAMPLE" != *"commentaries"* ]]; then
  echo "The API is up but did not return a commentaries field. Roll back with:" >&2
  echo "  $ROLLBACK" >&2
  exit 1
fi

echo
echo "==> Done. '$SOURCE_KEY' is live."
remote_py "commentary-manifest '$SOURCE_KEY' --output /dev/null" || true
echo
echo "Roll back with:"
echo "  $ROLLBACK"
echo
echo "Older backups on the server:"
remote "ls -1t eshia_research.db.bak-* 2>/dev/null | tail -n +4" || true
echo "(keep the newest three; delete the rest when you're happy)"
