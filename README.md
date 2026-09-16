# NFL Edge

A local NFL price-research dashboard and Underdog quote evaluator.

**Status: partial implementation, published as a review checkpoint.** The goal is
to identify potentially positive-EV NFL quotes using explicit costs, settlement
returns, and comparable market evidence. The financial core has been reviewed;
the complete application, real-quote screening, and profitability remain unproven.

## Current implementation plan

The governing forward plan is [NFL_EDGE_FINAL_PLAN.md](NFL_EDGE_FINAL_PLAN.md),
confirmed by the user on September 15, 2026. Local reliability work is underway;
see [execution status](docs/STATUS.md), [shared contracts](docs/CONTRACTS.md) and
[verification evidence](docs/VERIFICATION.md) for completed and outstanding gates.
The prepared [pilot protocol](docs/PILOT_PROTOCOL.md) is inactive. Engineering
checks do not establish real-quote screening readiness or profitability. Use the
[independent review prompt](docs/REVIEW_PROMPT.md) and
[checkpoint results](docs/reports/GITHUB_CHECKPOINT.md) to review this work.

## Historical independent review

Read [the full project plan and review brief](PROJECT_PLAN_FOR_REVIEW.md).
It contains the requirements, source strategy, formulas, implementation status,
known defects, acceptance criteria, and questions for the reviewer.

The shorter [initial implementation plan](PLAN.md) and full review brief remain
historical evidence; the forward plan and execution ledger now govern new work.

## Scope

- NFL pregame full-game moneylines, spreads, and totals.
- Free/manual reference evidence; existing ESPN, Bovada, and Kalshi adapters
  remain unadmitted and need source-policy enforcement.
- Manual Underdog quote input and manual sportsbook reference pairs.
- Market-derived probability estimates, fee-aware EV, and evidence checks.
- Paper/accepted-entry journal, exposure settings, settlement corrections,
  closing comparisons, and CSV export.
- Local Windows operation using React, TypeScript, FastAPI, and SQLite.

Actual placement remains manual in Underdog. This application has no trading,
deposit, or withdrawal endpoint and requires no sportsbook credentials.

## Completed at this checkpoint

- Lazy database initialization and isolated tests, independently reviewed.
- Explicit Decimal win/tie-or-push/loss returns, profile contradiction checks,
  versioned settlement profiles, conservative integer-line research calculations,
  and strict cent ceilings. Independent financial review accepted this scope.
- Financial preflight for closing calculations; closing timing and quality are
  separate outstanding work.
- Exact installed dependency versions, an environment verifier, and a local HTML
  evidence-report generator.
- An independently reviewed, inactive prospective pilot specification.

## Outstanding work

- `backend/records.py` is an unused, incomplete draft. Immutable entry linkage,
  idempotency, concurrent settlement/closing, migrations, and stronger local
  mutation controls are not integrated.
- UI input/revision binding, expiry, races, accessible mobile flows, and the new
  financial input fields remain unfinished. The built UI is still the prototype.
- Parser isolation, durable event identity, trustworthy receipt times, source
  admission enforcement, on-demand collection, and closing finalization remain open.
- No real settlement profile or source quality path is admitted. D08 requires
  initial network collection to be disabled, but application-wide enforcement is
  not implemented yet. `NFL_EDGE_NO_COLLECT=1` stops the background loop only;
  the existing refresh endpoint can still initiate network requests.
- Windows launch/recovery packaging, clean-install verification, complete browser
  acceptance, and pilot instrumentation remain unfinished.

The default database is `%LOCALAPPDATA%\SportsBetting\nfl-edge.sqlite3`. Tests
must use synthetic temporary paths. Do not use real records to review this
checkpoint. Operational setup and recovery instructions will accompany I07;
this checkpoint is not a release.

## Verify

```powershell
$env:NFL_EDGE_DB = Join-Path $env:TEMP ('nfl-edge-review-' + [guid]::NewGuid() + '.sqlite3')
$env:NFL_EDGE_NO_COLLECT = '1'
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe scripts/check_environment.py
npm --prefix frontend run build
```

These commands assume the existing pinned development environment: Python
3.12.10, Node 24.14.1, npm 11.11.0. No packages were installed during this work.
The push checkpoint passed **81 tests** (two dependency deprecation warnings),
TypeScript/Vite build, and installed-environment verification. Draft records
types received a compile/import check, not a dedicated functional review.
Detailed results and limits are in [verification](docs/VERIFICATION.md).

## Repository map

| Location | Responsibility |
|---|---|
| `backend/domain.py` | Input validation, canonical teams, time and odds conversion |
| `backend/providers.py` | Public reference collectors and parsers |
| `backend/engine.py` | Book pairing, probability estimates, EV, evidence and exposure |
| `backend/settlement_profiles.py` | Versioned payoff/rule profiles; production registry empty |
| `backend/storage.py` | Local SQLite records and snapshots |
| `backend/records.py` | Unused draft of future history/intent contracts |
| `backend/service.py` | Collection, source health, board, closing capture |
| `backend/app.py` | Local API and production frontend serving |
| `frontend/src/` | Dashboard and forms |
| `tests/` | Synthetic calculation and integration tests |

Source code and review documents are intended for review. Local databases,
credentials, dependencies, logs, and build outputs are excluded from Git.
