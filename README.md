# NFL Edge

A local NFL price-research dashboard and Underdog quote evaluator.

**Status: research prototype under review.** The application compares reference
prices and estimates expected value. It has not demonstrated a profitable
strategy or a verified executable Underdog edge.

## Start here for an independent review

Read [the full project plan and review brief](PROJECT_PLAN_FOR_REVIEW.md).
It contains the requirements, source strategy, formulas, implementation status,
known defects, acceptance criteria, and questions for the reviewer.

Suggested review request:

> Review PROJECT_PLAN_FOR_REVIEW.md using its reviewer instructions. Inspect the
> implementation where needed. Challenge the probability, fee, settlement,
> freshness, and source-independence assumptions. Rank changes that prevent
> misleading positive-EV estimates, and distinguish a useful research tool from
> a demonstrated profitable strategy.

The shorter [initial implementation plan](PLAN.md) provides background; the
full review brief is the current reference for status and unresolved work.

## Scope

- NFL pregame full-game moneylines, spreads, and totals.
- Free public reference collectors: ESPN-carried sportsbook prices, Bovada,
  and supplemental Kalshi comparisons.
- Manual Underdog quote input and manual sportsbook reference pairs.
- Market-derived probability estimates, fee-aware EV, and evidence checks.
- Paper/accepted-entry journal, exposure settings, settlement corrections,
  closing comparisons, and CSV export.
- Local Windows operation using React, TypeScript, FastAPI, and SQLite.

Actual placement remains manual in Underdog. This application has no trading,
deposit, or withdrawal endpoint and requires no sportsbook credentials.

## Current limitations

- The automated sources currently provide two underlying sportsbooks. Under the
  prototype's freshness policy, only the directly observed sportsbook can count
  toward its three-eligible-book screen when fresh. Manual corroboration is needed.
- Redistributed prices have unknown upstream latency. Kalshi is a comparison,
  not an Underdog execution price or a sportsbook vote.
- Five-minute background collection leaves gaps under the two-minute screen.
- Rule profiles, historical accepted-entry evaluation, result expiry, source
  handling, and browser-tool staging need further hardening. The review brief
  distinguishes observed defects from code-review concerns.
- Complete isolated browser verification, launch scripts, and backup/restore
  packaging are unfinished.

## Run locally

The initial build used Python 3.12 and Node.js 24. Run these commands in PowerShell
from the project root:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[test]"
cd frontend
npm ci
npm run build
cd ..
.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765/`. Stop the foreground server with Ctrl+C.
The collectors run while the server is running. Internet access is required for
reference prices; missing or inaccessible sources are reported in the UI.

The default database is `%LOCALAPPDATA%\SportsBetting\nfl-edge.sqlite3`, outside
the repository. `NFL_EDGE_DB` overrides the database path; use a separate database
for experiments. `NFL_EDGE_NO_COLLECT=1` disables background collection for tests.

For frontend development, run the backend above and `npm run dev` in `frontend`;
Vite serves the interface on port 5173 and proxies `/api` to port 8765.

## Verify

```powershell
.venv\Scripts\python.exe -m pytest -q
cd frontend
npm run build
```

The last implementation verification completed 21 tests and a production build.
Those tests cover selected financial calculations, data handling, persistence,
and API workflows. They do not validate a betting strategy or complete the
outstanding browser and source-quality studies.

## Repository map

| Location | Responsibility |
|---|---|
| `backend/domain.py` | Input validation, canonical teams, time and odds conversion |
| `backend/providers.py` | Public reference collectors and parsers |
| `backend/engine.py` | Book pairing, probability estimates, EV, evidence and exposure |
| `backend/storage.py` | Local SQLite records and snapshots |
| `backend/service.py` | Collection, source health, board, closing capture |
| `backend/app.py` | Local API and production frontend serving |
| `frontend/src/` | Dashboard and forms |
| `tests/` | Synthetic calculation and integration tests |

Source code and review documents are intended for review. Local databases,
credentials, dependencies, logs, and build outputs are excluded from Git.
