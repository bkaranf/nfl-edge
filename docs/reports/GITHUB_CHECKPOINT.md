# GitHub review checkpoint — 2026-09-15

The user explicitly requested pushing all current updates and a ChatGPT 6.0
review prompt. This checkpoint is a partial implementation, not a completed
release. The relevant revision is the commit containing this report on
`codex/initial-review`; historical baseline is
`20e954bb175eaa8f3966ccf0327bb0b4476008bd` in `bkaranf/nfl-edge`.

## Included work

- I01 database import/lifespan isolation, accepted by independent R01.
- I02 explicit Decimal payoff/profile/integer containment and closing financial
  preflight, accepted by independent R02 after repairs.
- I07a exact installed-environment pins and verifier; no clean-install claim.
- HTML evidence-report generator and its seven safety tests.
- Governing final plan, contracts, decisions, source evidence, acceptance ledger,
  and inactive pilot protocol accepted as a specification by R03.
- I03 `backend/records.py` draft only: request/history types, draft structures,
  canonical hashing, intent constants. No application imports or uses it yet.

The I03 author confirmed that this single file was the only I03 mutation; no
mutation was interrupted. No migration module, schema, API, middleware, storage,
service, engine, or I03 test changes were made. Draft SHA-256:
`D178DF9A83892CCBEA936FDE94EF2A48BE44244F93EB26F0E017259C8D77EEB2`.

## Checkpoint verification actually run

Windows; Python 3.12.10; Node 24.14.1; npm 11.11.0. Orchestrator runtime verified
as native `gpt-6-astra` / `max`, turn
`01a0a838-013b-7d91-ab66-19658dc1bd86`. Existing contributors/reviewers were native
`gpt-5.6-sol` / `xhigh`; their session evidence is summarized in STATUS.md.

| Check | Result |
|---|---|
| Full pytest, cache plugin disabled, JUnit output | 81 passed, 2 dependency deprecation warnings, 7.41s |
| TypeScript and Vite production build | PASS; original application assets unchanged |
| Installed environment verifier | PASS; 23 Python distributions, 8 direct frontend dependencies, 25 installed npm packages |
| Draft records compile and import | PASS; no database created; no dedicated functional tests/review |
| Fresh R02 final financial review before checkpoint | ACCEPT; 3 independent closing probes and 14 targeted cases passed |

Pytest was launched with a unique temporary `NFL_EDGE_DB` and
`NFL_EDGE_NO_COLLECT=1`. `tests/conftest.py` sets another dedicated temporary test
database before application imports; the outer database guard remained absent.
No real database, live collector, install, or migration was used for these checks.
The two warnings concern Starlette's deprecated httpx TestClient integration and
AnyIO BlockingPortal alias. They were not suppressed or repaired by installing
new packages.

Commands: `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
--junitxml=.qa/github-checkpoint/pytest.xml`,
`npm --prefix frontend run build`,
`.venv\Scripts\python.exe scripts/check_environment.py`,
`python -m py_compile backend/records.py`, and an isolated `import backend.records`.
Raw logs, screenshots, local synthetic preview, generated reports, and databases
remain in ignored `.qa/`; they are not available through GitHub. Published test
source and these summaries allow review without pretending the raw logs shipped.

The staged whitespace check found intentional Markdown hard-break spaces in the
verbatim supplied plan and one extra final blank line in the closing adapter test.
The test-only blank line was removed after the run; assertions and implementation
are unchanged. Historical R02 hashes refer to its original reviewed bytes.
The supplied plan is preserved exactly; the remaining staged whitespace check
excludes that document. No database, log, environment file, dependency directory,
or generated frontend build is included in the checkpoint.

## Material unfinished areas

1. Immutable evaluation-to-acceptance history, accepted/observed/recorded times,
   idempotency, concurrent append-only events, migrations, and local write security.
2. UI financial contract integration, expiry/revision binding, asynchronous races,
   old-line removal, full journal flows, and accessible mobile behavior.
3. Parser failure isolation, stable event identity, source policy enforcement,
   receipt provenance, shared rate limits, and closing timing/quality/finalization.
4. Windows launch/restart/WAL backup/restore, clean-install verification, complete
   browser acceptance, final evidence report, and pilot logging/reporting.

The existing app can still initiate network collection: the no-collect variable
only blocks its background loop, and D08 is not yet enforced at every runtime
entry point. Source and profile admission remain unverified; the production
settlement-profile registry is empty. Historical entry save/settlement and closing
timing defects are still present in the old paths. The draft records module does
not repair them.

Engineering verified: NOT YET. Manual research release ready: NOT YET. Real-quote
screen: BLOCKED. Pilot: inactive specification, instrumentation NOT YET.
Profitability: UNPROVEN. A01-A09 financial evidence does not establish A10-A28.

The user preview at port 8766 is a separate frozen synthetic snapshot with a
sample-data banner and refresh blocked. It is appearance evidence only and is
not the final application/browser acceptance test.
