# Bounded dispatch briefs and continuation queue

All tasks retain base `20e954bb175eaa8f3966ccf0327bb0b4476008bd` plus integrated
uncommitted changes, until an explicit later local revision is recorded. Native
Sol/xhigh session metadata must be verified before each new task/spawn. No nested
agents. Every writer preserves others' changes and owns only its listed files.
No production/default database, network collection, install or publication is
permitted as an incidental test. Astra owns integration/docs and fresh review.

## I02 financial containment (accepted; scope released)

Current disposition: fresh R02 accepted the complete closing payoff preflight
table. All three independent probes and 14 targeted cases passed; root's full
81-test suite passed twice, including the push checkpoint. Earlier repair-cycle
notes below are retained as history; their pending/open labels are superseded by
`reports/R02.md` final acceptance. Financial acceptance does not close temporal,
source-quality, persistence, UI, or release gates.

Author: S01 Sol session `01a0a7e7-f8c4-7a43-9d3b-12a75cf5f635`, current task
I02 with routing reverified. Risk HIGH. Contract C01-C04 in CONTRACTS.md.
Write set: backend/domain.py, engine.py, settlement_profiles.py; service.py only
shared payoff call adaptation; tests/test_engine.py, test_financial_contracts.py,
and test_workflow.py financial fixtures/expected behavior. No app/storage/providers/
frontend/conftest/isolation/docs edits. Logs under `.qa/I02`; parent report
`docs/reports/I02.md`. Require A01-A09 plus missing profile/returns, contradiction,
admission/effective times, full profile snapshot and integer containment tests.
Fresh reviewer R02 session `01a0a808-27ab-7890-946f-83d6c3fc4874` is active;
root draft review is not that gate. Author reports 51 focused / 58 full passing
isolated tests; full packet in reports/I02.md and .qa/I02/verification.txt.
R02 requires one service payoff repair: derive no-tie semantics from the pinned
evaluation profile for closing. Author owns only service.py and the relevant
workflow regression during repair; all other financial files remain frozen.
That first repair passed its reproducer, but cycle 2 found a known incompatible
profile could still produce closing ROI through generic fallback. Repair 2 now
separates financial admissibility from tie presence; both reviewer probes and
71 integrated tests pass per author. R02 targeted final confirmation is pending.
Evidence `.qa/I02-repair2/verification.txt` and `.qa/R02/closing_contradiction_probe.py`.
R02 confirmed both numerical fixes but found absent-profile missing T had no
OUTCOME_RETURN_REQUIRED code and the wrong reference-data explanation. D10 changes
the approach to a complete payoff preflight table before benchmark selection;
author owns service plus an adapter-test file, with nine explicit cases and all
three reviewer probes. Log `.qa/I02-adapter-table`. No I03 tracked writes yet.

Astra draft review feedback resolved by author, awaiting R02: admission as of evaluation; full
profile semantics/evidence snapshot; reject unsupported non-OT and no-tie REG
profiles rather than ignoring T; registry key/hash/version conflicts; unique
reason codes; general break-even classification/inequality; Decimal exposure.

## I03 durable history/schema (unused draft; frozen for GitHub checkpoint)

Assigned native Sol session `01a0a815-49f2-74c2-a4dc-ff0a58e54ab5` was authorized
to write after I02 acceptance, then frozen by the user's push request. Only
`backend/records.py` exists: unused request/draft types and canonical hashing.
Compile/import checks pass; no I03 functional tests, migration, schema/API/store
wiring, or fresh review exist. No mutation was interrupted. The remaining brief
below is future authorized implementation scope, not completed behavior. C09 fixes
phase boundaries. Keep writers frozen through the review checkpoint.

Objective: no lookahead entry EV, no duplicate intent/lost update, honest legacy
history, recoverable schema. Risk HIGH. Assign one Sol writer with serial ownership
of backend/storage.py, app.py, records.py additive history request models, a migrations
module if needed, tests/test_records.py and test_migrations.py, and only impacted
workflow fixtures. If service currently writes whole bets, coordinate a minimal
atomic-call adaptation in this same serialized scope. After START_WRITES, root also
authorizes a small engine.py pure payoff helper extraction/addition for pinned
repricing and exact contributor ID/time metadata, including integer inclusive pairs.
Financial semantics must remain unchanged; re-run A01-A09 and include the helper
in fresh phase-2 review. No current quote/registry lookup in accepted repricing.
Log `.qa/I03`, parent report I03.md.

Interfaces: C05-C09. Immutable evaluation + exact reference/profile/event/settings
snapshot; per-intent keys with conflict 409; accepted_at versus observed_at versus
recorded_at; actual recording remains possible with unavailable historical EV;
no current-price evaluation in save. Scoped settlement/reopen and closing events
must coexist under controlled concurrency and survive restart. Canonical event
and schedule-revision storage, manual event path, source/evidence revision and
trusted receipt fields are shared foundations for later UI/parsers.
Accepted additive API design: GET evaluation by ID; POST reopen; POST manual event;
GET events/list/by ID and schedule revision; read-only profiles. Flat SaveEntryIntent
adds idempotency_key, optional evaluation_id, accepted_at required for actual,
receipt_identity and placed confirmation. Mutations require JSON and
`X-NFL-Edge-Intent: local-write-v1`; exact origin/loopback Host and fetch metadata
checks apply in production. Intent equivalence includes operation AND target ID.
Immutable original evaluation is distinct from ORIGINAL_TERMS/PINNED_REPRICE/
UNAVAILABLE/LEGACY_UNKNOWN accepted calculation. Missing exact contributor or
trusted receipt lineage is UNAVAILABLE, never inferred from rounded ages.

Migration tests: empty DB to latest; known v1 copy to latest preserving legacy
payloads/evaluation bytes and unknown provenance; repeated migration idempotent;
unknown/newer version unchanged and fails clearly; rollback on interrupted/error
migration. No production migration during build. Backups use sqlite backup APIs
and explicit unused paths. Actual restore delivery belongs to I07.

Acceptance: A13/A16-A18 and foundational A21-A23. Include receipt-after-acceptance
even when provider time predates it, absent link, economic/selection mismatch,
settings/source change after evaluation, equivalent/conflicting duplicate
submissions, distinct equal-term intents, controlled settlement/closing
interleaving, reopen/correction, record-level safe CSV free-text escaping. All
synthetic databases/ports. Fresh reviewer + integration required before UI API
freeze. No real-quote or strategy readiness inferred from transactional passes.

## Later queue

- I04 providers: C06/C07, parser isolation and normalized observations, exact
  IDs/time semantics, recorded-or-labeled-synthetic fixtures; no independent live
  source probes. Parent coordinates source limiter and policy ownership.
- I05 frontend: stable backend contracts first; result revision/input binding,
  expiry/races/kickoff/reconnect, remove old-line comparisons, actual times and
  honest journal history, mobile accessible labels/focus, complete manual-empty
  workflow while source collection disabled. Original screenshots in
  `.qa/browser-baseline`; existing 390px nav buttons have no accessible names.
- I06 service/closing: C06/C08; no background loop, per-source cooldown/circuit,
  grace/finalization policy and append-only quality-aware closing. Negative ROI
  can be supported; disagreement and post-cutoff receipts cannot.
- I07 delivery: lock already-installed dependencies without new installs, local
  Windows setup/start/stop/verify/backup/restore scripts, safe explicit paths,
  meaningful process restart and WAL-equivalence tests on synthetic copies.
- I08 pilot: inactive docs protocol first independently reviewed by R03. Hash/
  version on activation, every attempt, recheck identity, separate strata and
  denominators, honest no-data reports. No future observation fabrication.
- V00 final: fresh Sol review of integrated diff, repair/retest, backend/type/build,
  real browser desktop/390px complete flows, local self-contained HTML evidence
  report, A01-A28 audit and setup/recovery/pilot handoff. No future waiting to claim
  profitability. Missing real sources/profiles retain explicit blocked labels.

Browser preparation: use CUA APIs only; after a compaction call
`cua.rewriteDocumentation()` before interaction. A frozen user-requested synthetic
preview is running on 8766 (see STATUS.md); keep it available to the user and do
not reuse its database for tests. Use a unique explicit .qa synthetic DB and loopback port, no collectors,
and a fixture identity endpoint. Cover empty/manual event, exact references/quote,
edits and older responses, real expiry, settings/evidence/kickoff invalidation,
paper/actual record, settle/correct/reopen/export, server restart and restored-copy
flows. Existing baseline server script refuses reuse of its existing DB. Reset
viewport and close test tabs/owned processes after captures. Report generator and
seven escaping/path/image checks exist; final manifest/report and visual QA remain.
