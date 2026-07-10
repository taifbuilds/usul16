# Al-Kafi Source-Prior Impact - 2026-07-09

## Why This Pass Was Done

The first 50 imported external reviews showed that several high-frequency Al-Kafi opening patterns were being treated as unresolved or ambiguous even though they are standard source-opening conventions:

- `محمد بن يحيى` at chain opening -> `محمد بن يحيى أبو جعفر العطار`
- `علي بن إبراهيم` at chain opening -> `علي بن إبراهيم بن هاشم`
- opening `عنه` -> same opening source as the previous hadith

These were implemented as narrow Phase D source priors in `collective_resolver.py`. They only fire for Al-Kafi chain openings and retain previous candidates as audit alternatives.

## Backup

Before applying the pass:

- `eshia_research.before-kafi-source-priors.20260709-183514.db`

## Applied Resolver Changes

Command:

```powershell
python -m eshia_research.cli refine-compiler-priors --source-book-id 11005
```

Result:

- examined source-prior targets: `8,283`
- resolved by source-prior pass: `7,858`
- `kafi_opening_ali_ibrahim`: `3,921`
- `kafi_opening_muhammad_yahya`: `3,489`
- `kafi_opening_anaphora_previous_hadith`: `448`

Then context refinement was rerun:

```powershell
python -m eshia_research.cli refine-collective-context --source-book-id 11005
```

Result:

- ambiguous nodes examined: `31,773`
- additional context resolutions: `3,800`

## Machine Review Before/After

Before:

- `approve_current`: `28,959`
- `needs_external_review`: `54,910`
- `flag_contradiction`: `3,878`

After:

- `approve_current`: `37,844`
- `needs_external_review`: `45,991`
- `flag_contradiction`: `3,912`

Net movement:

- approvals: `+8,885`
- external-review queue: `-8,919`
- contradiction flags: `+34`

## Source-Prior Decision Breakdown

Rank-1 source-prior methods now in `mention_resolutions`:

- `kafi_opening_ali_ibrahim`: `3,921`
- `kafi_opening_muhammad_yahya`: `3,489`
- `kafi_opening_anaphora_previous_hadith`: `448`

Machine decisions for these:

- `kafi_opening_ali_ibrahim`: `3,921 approve_current`
- `kafi_opening_muhammad_yahya`: `3,489 approve_current`
- `kafi_opening_anaphora_previous_hadith`: `440 approve_current`, `8 flag_contradiction`

## External Review Rows

The two imported external review result files were re-imported after machine-review recomputation so `decision_id` links point at current machine decisions.

- external review rows: `50`
- unmatched actionable rows: `0`
- admin decisions under `codex-admin-external-v1`: `50`

## Verification

- Backend full suite: `236 passed, 1 warning`
- Frontend lint: passed
- Frontend build: passed
- Live admin page smoke: passed
