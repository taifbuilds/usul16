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
