# Al-Kafi 10k External Assessment Import - 2026-07-09

## Source Files

- Main corrected result file: `scratch_audit/external_assessment_alkafi_10000_review_results_REDO_v2_ambiguity_corrected.md`
- Earlier small review files re-imported for parser cleanup:
  - `C:\Users\taifh\.codex\attachments\b3a8c2dc-1275-4185-af0d-b19449ba64e8\pasted-text.txt`
  - `C:\Users\taifh\.codex\attachments\fbefd25f-b399-466b-a1e3-a44e1892f51b\pasted-text.txt`

## Backup

- `eshia_research.before-10k-external-import.20260709-225954.db`
- Size: `2,121,252,864` bytes

## Import Results

The corrected 10k file parsed cleanly:

- Parsed cases: `10,000`
- Missing chain nodes: `0`
- Actionable person rows matched: `3,933`
- Unmatched actionable person rows: `0`
- Verdicts:
  - `keep_ambiguous`: `5,792`
  - `approve_current`: `2,056`
  - `override_person`: `1,877`
  - `flag_text_or_chain_issue`: `275`
- Confidence:
  - `low`: `4,845`
  - `high`: `4,268`
  - `medium`: `887`

After re-importing the earlier 50-row packets plus the corrected 10k packet:

- External review rows stored: `10,050`
- Source labels:
  - `external_assessment_alkafi_10000_review_results_REDO_v2_ambiguity_corrected`: `10,000`
  - `pasted-text`: `50`
- Stored source-reference fields with leaked case headings: `0`
- Stored raw-case fields with leaked case headings: `0`

## Code Changes

- Tightened `src/eshia_research/rijal/external_review.py`:
  - case headings are treated as parser boundaries
  - slash variants like `al-Sarrad / al-Zarrad` match the local `al-Zarrad` row safely
  - nisba/nasab variants like `al-Yaqtini` can match local `b. Yaqtin`
  - `mawla Al Yaqtin` identifying notes can match the local canonical base name
  - broad trailing-nisba fallback is not used too early against resolver candidate rows
  - promotion deduplicates multiple external reviews for the same node by keeping the latest imported row
  - `approve_current` rows that supply a matched person where the machine had no/different selected person are promoted as admin overrides, not as false machine approvals
- Added regression tests in `tests/test_external_review.py`.

## Promotion Results

Promoted external reviews for Al-Kafi under reviewer `codex-admin-external-v1`.

- Review rows considered: `10,050`
- Unique admin decisions written: `10,031`
- Nodes with multiple review rows collapsed by latest-review rule: `19`
- Skipped unmatched actionable rows: `0`
- Unknown verdicts: `0`

Admin decision counts:

- `keep_ambiguous`: `5,792`
- `approve_external_override`: `3,961`
- `flag_text_or_chain_issue`: `276`
- `approve_current`: `2`

Confidence counts:

- `low`: `4,845`
- `high`: `4,298`
- `medium`: `888`

## Verification

- Focused external-review tests: `7 passed`
- Full backend test suite: `239 passed, 1 warning`
- API summary confirmed:
  - `GET /person-resolution-decisions/summary?source_book_id=11005&reviewer=codex-admin-external-v1`
  - `total_decisions=10031`
- Frontend route smoke:
  - `http://127.0.0.1:3000/review/person-resolutions?admin_reviewed=true` returned `200`
- Local servers remained running:
  - Frontend: `127.0.0.1:3000`, PID `10364`
  - Backend: `127.0.0.1:8000`, PID `30672`

## Next Step

Do not generate another broad 10k packet immediately. The admin layer now contains a large amount of structured outside-review signal. The next productive phase is to mine the high-confidence repeated overrides into narrow resolver/source-prior rules, then rerun Al-Kafi machine review and measure how many `needs_external_review` cases disappear without hiding ambiguity.
