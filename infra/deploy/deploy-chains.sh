#!/usr/bin/env bash
#
# Publish one book's parsed chains to production as a delta.
#
# The sibling of deploy-db.sh, which does the same for commentary. Code deploys
# itself when main is pushed; chain work happens locally and does not.
#
#   ./infra/deploy/deploy-chains.sh 11021              # Faqih
#   ./infra/deploy/deploy-chains.sh 11021 --dry-run
#
# It never replaces the production database, and it never touches a book other
# than the one named: every delete inside the import is scoped to the reports
# carried by the delta. That matters because production holds tens of thousands
# of human resolution decisions for al-Kafi.
#
# Rows travel keyed by public_id. `person_id` and `canonical_narrator_id` also
# cross the wire, and both are checked by name on arrival — an id that means a
# different man on the target aborts the whole import rather than silently
# reassigning who narrated what.
#
# Order matters. Everything that can fail without touching production happens
# first: fingerprint the target, export the delta, ship it, migrate, dry-run,
# back up, and only then write.

set -euo pipefail

SOURCE_BOOK_ID="${1:-}"
DRY_RUN=""
[[ "${2:-}" == "--dry-run" ]] && DRY_RUN="--dry-run"

if [[ -z "$SOURCE_BOOK_ID" ]]; then
  echo "usage: $0 <source-book-id> [--dry-run]" >&2
  echo "  e.g. $0 11021     # Man La Yahduruhu al-Faqih" >&2
  echo "       $0 10083     # Tahdhib al-Ahkam" >&2
  exit 2
fi

HOST="${USUL16_HOST:-usul16-production}"
REMOTE_APP="${USUL16_REMOTE_APP:-/home/deploy/app/eshia-research}"
REMOTE_INCOMING="${USUL16_REMOTE_INCOMING:-/home/deploy/incoming}"
LOCAL_DB="${DATABASE_FILE:-eshia-research/eshia_research.db}"

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

remote() { ssh "$HOST" "cd '$REMOTE_APP' && $*"; }
remote_py() { remote ".venv/bin/python -m eshia_research.cli $*"; }

echo "==> Deploying chains for book $SOURCE_BOOK_ID to $HOST"
[[ -n "$DRY_RUN" ]] && echo "    DRY RUN: production will be validated but not written"

if [[ ! -f "$LOCAL_DB" ]]; then
  echo "Local database not found at $LOCAL_DB" >&2
  exit 1
fi

# --- 1. What does production already have? --------------------------------
echo "==> [1/8] Fingerprinting production"
remote "mkdir -p '$REMOTE_INCOMING'"
remote_py "chain-manifest '$SOURCE_BOOK_ID' --output '$REMOTE_INCOMING/chain-manifest-$SOURCE_BOOK_ID.json'" \
  || { echo "Could not read the production manifest. Is the code deployed?" >&2; exit 1; }
scp -q "$HOST:$REMOTE_INCOMING/chain-manifest-$SOURCE_BOOK_ID.json" "$WORK/manifest.json"
echo "    manifest: $(wc -c <"$WORK/manifest.json") bytes"

# --- 2. Export only what differs ------------------------------------------
echo "==> [2/8] Exporting the delta"
DELTA="$WORK/chains-$SOURCE_BOOK_ID-$STAMP.json.gz"
LOCAL_DB_ABS="$(cd "$(dirname "$LOCAL_DB")" && pwd)/$(basename "$LOCAL_DB")"
if command -v cygpath >/dev/null 2>&1; then
  LOCAL_DB_ABS="$(cygpath -m "$LOCAL_DB_ABS")"
fi
DATABASE_URL="sqlite:///$LOCAL_DB_ABS" \
  "$PYTHON" -m eshia_research.cli export-chain-delta "$SOURCE_BOOK_ID" \
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
scp -q "$DELTA" "$HOST:$REMOTE_INCOMING/"
REMOTE_DELTA="$REMOTE_INCOMING/$(basename "$DELTA")"

# --- 4. Schema ------------------------------------------------------------
echo "==> [4/8] Applying migrations"
remote ".venv/bin/alembic upgrade head"

# --- 5. Rehearse against the real target ----------------------------------
# The import validates every public_id and every identity before writing, so
# this proves the delta fits production without a backup being needed yet.
echo "==> [5/8] Dry run against production"
remote_py "import-chain-delta '$REMOTE_DELTA' --dry-run" \
  || { echo "DRY RUN FAILED — production was not modified." >&2; exit 1; }

if [[ -n "$DRY_RUN" ]]; then
  echo "==> Dry run complete. Nothing was written."
  exit 0
fi

# --- 6. Back up BEFORE any write -----------------------------------------
echo "==> [6/8] Backing up the production database"
BACKUP="eshia_research.db.bak-chains-$SOURCE_BOOK_ID-$STAMP"
remote "cp -v eshia_research.db '$BACKUP'"
ROLLBACK="ssh $HOST 'cd $REMOTE_APP && cp $BACKUP eshia_research.db && sudo systemctl restart usul16-api'"

# --- 7. Write ------------------------------------------------------------
echo "==> [7/8] Importing"
if ! remote_py "import-chain-delta '$REMOTE_DELTA'"; then
  echo >&2
  echo "IMPORT FAILED — the import aborts before writing, so production should" >&2
  echo "be untouched. If you need to restore anyway:" >&2
  echo "  $ROLLBACK" >&2
  exit 1
fi

# --- 8. Restart and prove it ---------------------------------------------
echo "==> [8/8] Restarting the API"
remote "sudo systemctl restart usul16-api"

echo "    waiting for /health"
for attempt in $(seq 1 30); do
  if remote "curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1"; then
    echo "    healthy after ${attempt}s"
    break
  fi
  if [[ "$attempt" == 30 ]]; then
    echo "API did not come back healthy. Roll back with:" >&2
    echo "  $ROLLBACK" >&2
    exit 1
  fi
  sleep 1
done

echo
echo "==> Done. Backup on the server: $BACKUP"
echo "    Roll back with:"
echo "      $ROLLBACK"
