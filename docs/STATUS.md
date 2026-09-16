# Execution checkpoint

Updated: 2026-09-15 (America/New_York). Objective remains the complete build in
`NFL_EDGE_FINAL_PLAN.md`, with local changes and verified evidence only.

Current checkpoint: the user explicitly requested a GitHub push and independent
ChatGPT review on 2026-09-15. Implementation is frozen for that checkpoint. I02
is accepted; I03 contains only an unused draft `backend/records.py`. See
`reports/GITHUB_CHECKPOINT.md` and `REVIEW_PROMPT.md`. This is not final delivery.

## Preflight

- Repository: `https://github.com/bkaranf/nfl-edge.git`.
- Checkout: `C:\Users\bkara\OneDrive\Documents\ChatGPT\SportsBetting`.
- Branch: `codex/initial-review`; starting HEAD:
  `20e954bb175eaa8f3966ccf0327bb0b4476008bd` (also the historical review anchor).
- Initial working tree: only untracked user-supplied `NFL_EDGE_FINAL_PLAN.md`.
- User confirmed this plan supersedes the missing goal filename
  `NFL_EDGE_PROJECT_PLAN.md`. Preserve all three existing plans.
- No repository/ancestor AGENTS.md existed; user-level instructions inspected.
- Python 3.12.10 virtual environment and Node/npm already installed. No installs.
- Baseline suite: 21 passed, 2 dependency deprecation warnings, isolated database
  and collection disabled. Evidence: `.qa/baseline/pytest.log`.
- Historical packet describes 13 characterization cases but those files are not
  in this checkout or the supplied Downloads plan. Reproduce desired behavior
  from the plan; do not claim those 13 cases were run.

## Verified runtime

Native session metadata (not a prompt nickname) establishes:

| Task | Session ID | Role/provider | Model / effort |
|---|---|---|---|
| Orchestrator | 01a0a7e3-8829-7ae0-a1c9-930ad0d27330 | primary / openai | gpt-6-astra / max |
| S01 | 01a0a7e7-f8c4-7a43-9d3b-12a75cf5f635 | default / openai | gpt-5.6-sol / xhigh |
| I01 | 01a0a7e8-371f-7742-aaf2-d5f855f66edc | default / openai | gpt-5.6-sol / xhigh |
| S02 | 01a0a7eb-f6c4-7a53-ac8f-d2d24f61c56a | default / openai | gpt-5.6-sol / xhigh |
| R01 | 01a0a7ed-0f21-7b23-a089-a7bcde2f3f7e | default / openai | gpt-5.6-sol / xhigh |
| R03 | 01a0a7fb-ba10-7b60-b7fd-233654785c40 | default / openai | gpt-5.6-sol / xhigh |
| R02 | 01a0a808-27ab-7890-946f-83d6c3fc4874 | default / openai | gpt-5.6-sol / xhigh |
| I07a | 01a0a80b-0c1f-7a31-99ca-3abb4e7d89f5 | default / openai | gpt-5.6-sol / xhigh |
| I03 | 01a0a815-49f2-74c2-a4dc-ff0a58e54ab5 | default / openai | gpt-5.6-sol / xhigh |
| S03 | 01a0a819-5dfb-70a2-9bb6-67672388f4ec | default / openai | gpt-5.6-sol / xhigh |

Evidence: matching `session_meta` and `turn_context` entries in the session JSONL
files under `%USERPROFILE%\.codex\sessions\2026\09\15`. Global model settings
agree. Custom `ocx-*` roles contain routing instructions and ignore normal model
selection; none were selected. No global configuration changed.
Sanitized evidence is retained in `.qa/preflight/runtime-models.json`.
Latest follow-up/new-session proof is `.qa/preflight/runtime-models-current.json`.
Project `.codex/config.toml` sets matching defaults and a three-child cap; TOML
assertions and `codex features list` configuration load both passed. CLI 0.147.0;
desktop native session runtime 0.154.0-alpha.6.2.

## Task and ownership ledger

| ID | Status | Owner | Write scope | Dependencies / next gate |
|---|---|---|---|---|
| P00 preflight/baseline | PASS | Astra | docs and AGENTS only | completed safe baseline |
| S01 financial contracts | PASS | Sol xhigh | read-only | proposal adopted in CONTRACTS.md |
| I01 database isolation | PASS | Sol xhigh, routing reverified | scope released | 7 source tests; 4 independent probes; actual isolated Uvicorn smoke; included in 81-test checkpoint |
| S02 temporal/source contracts | PASS | Sol xhigh | read-only | design accepted C06-C08 |
| R01 isolation review | ACCEPT | fresh Sol xhigh, routing reverified | read-only; scope released | both requested regression repairs verified in cycle 2 |
| R03 pilot protocol review | ACCEPT | fresh Sol xhigh | scope released | inactive protocol spec only, SHA in reports/R03.md; instrumentation/A25 pending |
| I02 payoff/profile containment | PASS | S01 Sol xhigh, routing reverified | scope released | complete adapter table, three reviewer probes, 81-test integration |
| R02 financial review | ACCEPT | fresh Sol xhigh, routing verified | scope released | financial scope only; temporal/source/closing-quality gates remain open |
| I03 durable history/schema | DRAFT_FROZEN | Sol xhigh, routing verified | backend/records.py only; no further writes | unused request/hash scaffolding; no schema/API/storage integration or I03 functional tests |
| I04 parsers/identity/provenance | NOT_STARTED | unassigned Sol | providers/source tests | frozen I03 contracts |
| I05 lifecycle/journal UI | NOT_STARTED | unassigned Sol | frontend only | stable backend API |
| I06 closing/source operation | NOT_STARTED | unassigned Sol | service/closing/source registry | I03/I04 |
| I07 Windows delivery/recovery | NOT_STARTED | unassigned Sol | scripts/manifests/operations tests | stable storage, no installs |
| I07a environment lock | PASS | Sol xhigh, routing verified | scope released | 3 tests, version/tree verifier and build pass; no clean install/hash-lock claim |
| S03 source documentation | PASS | Sol xhigh, routing verified | scope released | official docs reviewed; no source/profile admitted; collection remains disabled by contract, runtime enforcement pending |
| I08 prospective pilot | NOT_STARTED | unassigned Sol | instrumented attempts/reporting/protocol | stable evidence model |
| V00 integrated/browser review | NOT_STARTED | fresh Sol + Astra | evidence only | all impacted implementations |

No production server or collector was started by this work. Baseline tests used a dedicated
database under ignored `.qa/baseline`, never the default user database.
Isolated synthetic servers were used for R01 Uvicorn smoke and original-frontend
desktop/390px screenshots. Both servers stopped; baseline listener 8767 is absent.
Original UI assets: JS `index-L8uixFF0.js`, CSS `index-MGUY_iLe.css`.
Screenshots are `.qa/browser-baseline/{desktop,mobile}-{board,quote}.png`.
This is appearance evidence, not final transaction/lifecycle verification.
Root's final phase-1 integrated suite passed 81 tests (two known dependency
deprecation warnings), log/JUnit `.qa/phase1-final.{log,xml}`. The push checkpoint
reran all 81 tests, TypeScript/Vite build, and the environment verifier successfully;
local evidence is `.qa/github-checkpoint/`. These include report-generator and
environment checks; they do not close later phase gates.
Offline intermediate artifact `.qa/checkpoint-report.html` was rendered using
`scripts/build_evidence_report.py` and `.qa/checkpoint-manifest.json`. Its checks
are explicitly incomplete; regenerate after final integration. Browser screenshot
files named .png actually contain CUA-returned JPEG bytes; the report detects MIME
from bytes. Original evidence files are preserved. Final visual QA is still pending.

The user-requested frozen synthetic preview is running at `http://127.0.0.1:8766/`
from `.qa/user-preview/snapshot-20260915-231251`, isolated from ongoing source
edits and real records. It has a visible sample-data banner and blocks refresh
collection. CUA verified the rendered board and kept the tab open. Owned server
PID 132432 / exec session 13306; leave running for the user. An existing listener
on port 8765 was observed and left untouched. Preview artifacts are not published.

## Readiness

- Engineering verified: **not yet**.
- Windows release ready: **not yet**.
- Manual research ready: **not yet**.
- Real-quote screen: **BLOCKED by missing verified contract and source evidence**;
  unrelated engineering work continues.
- Pilot instrumented: **not yet**. No future observations or outcomes collected.
- Strategy validated / profitability: **unproven**, outside the build milestone.

## Resume

Read this ledger and CONTRACTS/DECISIONS/VERIFICATION, inspect live agent status
before reclaiming any write scope, recheck Git and runtime model metadata, then
continue dependency-ready work. Do not reset to the baseline or rerun tests on
real records. Do not treat the present baseline passes as fixed behavior.
Detailed active/queued scope briefs are in `docs/TASKS.md`.
