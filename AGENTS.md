# NFL Edge working contract

The user confirmed `NFL_EDGE_FINAL_PLAN.md` as the governing implementation plan
on 2026-09-15. `PLAN.md` and `PROJECT_PLAN_FOR_REVIEW.md` remain historical evidence.

- Orchestrator: native `gpt-6-astra`, reasoning `max`.
- Every child: native `gpt-5.6-sol`, reasoning `xhigh`. Verify actual turn metadata
  and custom-role overrides before work/on spawn. No silent model substitution.
- No nested delegation. At most four Sol tasks and two Sol writers; the current
  runtime permits three simultaneous children. Use exclusive file ownership.
- Serialize domain/API/storage/service contracts. Fresh Sol review is required
  for financial, temporal, persistence, migration, security, and pass-label work.
- Preserve user changes and real records. Local code only: no publishing,
  wagering, credentials, new accounts, installs, or global configuration edits.
  Exception: on 2026-09-15 the user explicitly authorized pushing all current
  project updates to GitHub as a review checkpoint; this does not authorize deployment.
- Do not initialize, migrate, or test the real default database. Every test uses
  an isolated temporary `NFL_EDGE_DB` and `NFL_EDGE_NO_COLLECT=1`.
- Keep arithmetic, research evidence, provisional screening, and profitability
  claims separate. Unsupported settlement profiles/sources cannot qualify.
- Never fabricate historical availability, future observations, source access,
  contract evidence, or Windows/browser verification.

Read `docs/STATUS.md` before resuming. Record decisions in `docs/DECISIONS.md`,
contracts in `docs/CONTRACTS.md`, and results in `docs/VERIFICATION.md`.
Local logs, fixtures with sensitive data, screenshots, and test databases belong
in ignored `.qa/`; source tests use synthetic fixtures clearly marked as such.

Baseline verification (PowerShell, always isolate database before importing):

```powershell
$env:NFL_EDGE_DB = Join-Path $env:TEMP ('nfl-edge-qa-' + [guid]::NewGuid() + '.sqlite3')
$env:NFL_EDGE_NO_COLLECT = '1'
.venv\Scripts\python.exe -m pytest -q
npm --prefix frontend run build
```

No test count alone proves acceptance. Record PASS/FAIL/NOT_RUN against the
specific scenarios and run integrated verification after review repairs.
