# Operations

## Runtime

- Backend: `eshia-research`, FastAPI/SQLAlchemy, Python 3.11 or newer.
- Frontend: `web`, Next.js.
- Main database: `eshia-research/eshia_research.db`.
- Local URLs: backend `http://127.0.0.1:8000`, frontend `http://127.0.0.1:3000`.

Database files, environments, dependency directories, generated review packets,
and logs are intentionally excluded from Git. `AGENT_HANDOFF.md`, source code,
migrations, tests, small audit reports, and reproducible audit scripts are source
artifacts and should be committed.

## Database changes

Before changing corpus or resolver-derived database rows:

1. Record the scope and intended backup name in `AGENT_HANDOFF.md`.
2. Copy `eshia_research.db` to that backup name.
3. Run the command in dry-run mode when one exists.
4. Apply the change, run invariants/evaluation, and update the handoff with counts.

Never commit the database or its snapshots.

## Snapshot retention

Inspect eligible snapshots without deleting anything:

```powershell
.\scripts\database-backup-retention.ps1
```

The default policy protects the seven newest snapshots and only considers older
snapshots after 14 days. Review the printed list, then explicitly apply it:

```powershell
.\scripts\database-backup-retention.ps1 -Apply
```

The script only considers known backup-name patterns in the database directory
and never considers the live `eshia_research.db` file.

## Verification

```powershell
Set-Location eshia-research
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m pytest -q

Set-Location ..\web
npm run lint
npm run build
```

## Public deployment gates

The public API is read-only by default. Do not route production traffic until
all of the following are true:

1. Keep `API_ADMIN_TOKEN` empty on the public API. Run editorial tooling as a
   separate private deployment with a long random token and restricted network
   access.
2. Keep `ENABLE_REVIEW_UI=false` on the public frontend.
3. Set `API_ALLOWED_ORIGINS` to the exact HTTPS frontend origin. Never use `*`.
4. Set `NEXT_PUBLIC_API_BASE_URL` and `NEXT_PUBLIC_SITE_URL` to their public
   HTTPS origins. A missing site URL deliberately causes `robots.txt` to block
   indexing.
5. Keep API documentation disabled unless it is needed on a private network.
6. Give the public API database user read-only permissions where the deployment
   database supports them.
7. Put request rate limiting at the reverse proxy or edge, especially for
   `/search` and `/transmission-graph`.

Before opening traffic, warm the expensive transmission aggregation:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/transmission-graph?source_book_id=11005&min_count=2&max_nodes=500'
```

Monitor `/health`, 5xx rate, p95 response latency, process memory, database
availability, and backup age. Restore a recent backup into a disposable
database at least once before launch; a backup is not proven until it restores.
