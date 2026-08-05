# Shia Hadith Project

Local research workspace for building an auditable Shia hadith corpus, with
Al-Kafi as the current gold-standard pilot.

- `eshia-research/`: crawler, database models, extraction, isnad/person
  resolution, FastAPI API, CLI, migrations, and backend tests.
- `web/`: Next.js reader, review tools, narrator profiles, and transmission
  network.
- `AGENT_HANDOFF.md`: durable corpus decisions, applied database changes, and
  current research status.
- `docs/operations.md`: runtime, database-change, backup-retention, and
  verification procedures.
- `docs/operations/PRODUCTION_DEPLOYMENT.md`: **canonical reference for how
  production works** — architecture, the three deployment layers (code, schema,
  data), `deploy-db.sh`, backup policy, and per-change deployment checklists.
  Read this before touching production.

Operational databases, snapshots, logs, environments, dependencies, and
generated review packets are intentionally excluded from source control.
