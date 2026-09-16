# Shared contracts

Status: **phase 1 contract accepted**, 2026-09-15. S01 proposed and Astra accepted
the following interfaces. I02 owns implementation. Domain/API/storage changes
are serialized; source/history details will be frozen before their writers start.

Immutable constraints: explicit net cash returns; no invented profile evidence;
integer lines remain research-only; immutable evaluation and accepted history;
observation/availability/acceptance/recording times differ; stale or unsupported
data never turns into qualifying evidence; actual records can be recorded even
when research is unavailable or exposure caps are exceeded.

## C01 quote and settlement contract

Canonical additions to `QuoteInput`:

- `period`: `full_game` (unsupported periods fail qualification).
- `settlement_profile`: optional `{profile_id, version}`; registry is server-owned.
- `outcome_returns`: explicit decimal-string `{win, tie_or_push, loss}`; unknown
  state returns remain null. Quantities and contract/receipt identifiers optional.
- Retain legacy `winning_payout`, `push_return`, `losing_return` as a wire/storage
  bridge. Canonical and legacy duplicates must be equal as Decimal values; reject
  structurally conflicting duplicates with 422. Generic confirmations never
  supply a missing return or admit a profile. Preserve original monetary strings.

A profile binds version/hash, exact exchange/product/market/period/outcome
semantics, season/overtime/ordinary-completion limitations, required returns,
optional explicit return constraints, effective dates and evidence/admission.
Duplicate profile version with different content is invalid. No real production
profile is admitted from current supplied evidence. Test profiles are injected
only by tests, never shipped as selectable admitted production contracts.

Missing, unknown, retired, ineffective or unadmitted profiles are recordable.
If enough explicit semantics exist, calculate labeled research diagnostics.
A quote conflicting with a known profile gets a financial calculation rejection
(`SETTLEMENT_PROFILE_CONTRADICTION`, no net calculation); this must not make a
real accepted position impossible to journal. Keep original entered economics
and issues. Only malformed/structurally ambiguous payloads warrant schema 422.

## C02 payoff calculation

`V=p_win*W+p_tie_or_push*T+p_loss*L`, `EV=V-C`, `ROI=EV/C`.
Every required input is explicit. Cash uses Decimal/minor units and deterministic
rounding. Probability bounds and sums must be validated. Stress transfers at
most available win mass to loss, so L also contributes. Fees enter the provided
net outcome returns/all-in cost once. Moneyline tie returns never default to W/2.

Persist calculation version, exact monetary inputs, resolved profile snapshot,
probability vector, expected/stressed return, conditional ordinary-completion
label and chosen settings. Break-even output must use the full payoff equation;
identify impossible or non-unique thresholds instead of clipping into [0,1].
At fixed quantity, the displayed maximum cent cost meets the ROI floor and has
strictly positive stressed ROI. V=10 and stressed V=9.60 at 3% gives 9.59; 9.60
must fail strict positivity. Outcome-dependent fees can make T differ from W/2.

## C03 result contract

Canonical `status` is one of `INSUFFICIENT_DATA`, `RESEARCH_ONLY`,
`MEETS_ESTIMATED_SCREEN`, `EXPIRED`. Missing defensible probability or required
payoffs means INSUFFICIENT_DATA. Calculable unsupported/unadmitted/failed-gate
cases mean RESEARCH_ONLY. EXPIRED is reserved for previously current results
invalidated by lifecycle checks. `qualified` is exactly the derived predicate
`status == MEETS_ESTIMATED_SCREEN`; retain compatible labels/reasons for old UI.

Use stable deterministic unique reason codes plus human-readable messages:
event state, missing pairs/returns, insufficient eligible references,
disagreement, stale/future quote, fees, missing/unknown/unadmitted/ineffective/
contradictory profile, integer containment, ROI floor and stressed positivity.
Store inputs/settings/profile/evidence so later consumers can bind revisions.

## C04 integer diagnostics

Every integer spread/total includes `INTEGER_LINE_RESEARCH_ONLY`; it cannot pass
in v0.2. Preserve diagnostic/journal data. Each admitted diagnostic book vector
uses coherent strict-win and win-or-push adjacent pairs; derive push/loss from
cumulative probabilities. Never independently median all three marginal states.
Reject non-monotone/incompatible vectors. Aggregate coherently, report win,
push/loss and payoff disagreement, and cover side/sign/mirror symmetry. This is
arithmetic containment, not alternate-line model admission or calibration proof.

## Implementation ownership

I02: domain, engine, settlement_profiles; service payoff call adaptation only;
financial tests and affected workflow fixtures. No storage/API lifecycle/UI
edits during this scope. The source scout S02 is read-only. I01 import isolation
is frozen for independent R01 review. Later schema/API changes await I02 review.

## C05 immutable records and acceptance (phase 2 design accepted)

New evaluations persist immutable target JSON, original monetary text, complete
reference snapshots/IDs, settings, event/profile/source revisions, calculation
version, input hash and expiry. API input never supplies trusted revision or
admission claims. Global changes cannot rewrite evaluation payloads.

New journal intents supply `idempotency_key`, optional `evaluation_id`, accepted
economics, `accepted_at` (required for actual), observation time, optional receipt
identity and notes. Server generates `recorded_at`. Actual entries additionally
require placed confirmation. Two distinct keys permit intentional equal-term
positions. Same key and equivalent payload returns the same resource; a
conflicting replay is 409. Apply these guarantees transactionally, including
settlement/correction intents; no read-before-write duplicate race.

Never call current-market evaluation while saving an accepted entry. Pin the
original evaluation when a valid ID is supplied, and retain original versus
accepted economics separately. Any accepted-economics reprice uses only the
pinned probabilities/reference/profile/settings evidence available at acceptance,
is a separate immutable calculation, and is labeled as such. Missing/mismatched/
post-acceptance/expired historical linkage yields unavailable historical entry
EV with explicit reasons; the actual cash record is still saved. A provider's
old timestamp or a backdated manual field is not proof of earlier availability.

Settlement and closing use separate append-only event/revision records and
scoped atomic transactions (or checked optimistic revisions). No API caller may
overwrite a stale whole bet. Corrections, reopening/reversal and superseded
events remain auditable after restart and CSV export. Recorded cash return is
P&L authority; labels inconsistent with profile/economics generate a warning,
not an invented return. Paper and actual cash/exposure stay separate.

## C06 provenance and source policy (accepted S02 design)

Each immutable source policy revision records effective/recorded time, admission
state, collection mode, exact market/rule scope, access/freshness/cache semantics,
rate/cooldown policy, evidence references/hash and reason. Initial states are
non-eligible; network collectors start disabled pending access qualification.
Manual source submissions remain possible as labeled research. Source health
is separate from admission and cannot promote it. Admission changes invalidate
dependent current screens, never original stored evidence.

One response/page or atomic manual submission is one snapshot. Persist its ID,
scope, request start, response receipt, monotonic duration, record time, parser
version, completeness, status/error, bounded raw evidence/hash and clock issues.
Aggregate refresh completion is not a receipt or quote-observation time.

Every quote carries immutable observation/snapshot/pair IDs, provider event/
market/outcome identity, origin book and distributor, canonical event/mapping
revision, exact period/rule semantics, side/raw and canonical line, price/state,
provider timestamp plus meaning, source observation, trusted local receipt and
record times, policy/parser revisions and raw locator/hash. Null means unknown.
Manual observation time is attested; trusted receipt is server-generated.
Unverified retrospective imports have no backdated trusted receipt.

Pair within the same snapshot/pair group, origin book/distributor, event, exact
market/period/rule semantics/line and compatible event/source/parser revision.
Duplicate/conflicting sides quarantine only that pair. Latest OFF/suspended/
closed or successful full-empty scope cannot resurrect an older OPEN market.
Partial scopes preserve failed partitions at their original times; failures do
not refresh ages. Each provider is rate-limited across all callers, with bounded
429 Retry-After handling and denial circuit breaking. No background price loop.

## C07 durable event identity and legacy migration

New canonical event IDs are opaque and schedule-independent. Keep provider-ID
mapping and schedule/state revision history. An unchanged provider event ID
with changed kickoff keeps all journal/exposure links. New provider IDs may link
only with unique strong identity evidence (league/season/phase/week/home/away)
or explicit reviewed crosswalk; conflicts/multiple matches quarantine.
Support manual event entry with explicit teams/start/observation, labeled manual
schedule evidence, so safe research works while network sources are disabled.

Migrate known schema versions transactionally on synthetic databases/copies.
Unknown/newer versions fail without changing schema or data. Preserve legacy
payload bytes; expose new metadata through side tables/projections. Existing
game IDs remain canonical aliases, preserving historical links. Existing source
observations retain claimed times with receipt/provenance unknown; do not assign
current or inferred historical receipt. Legacy evaluations are never recomputed.
Production migration is not run during this build. Recovery must use SQLite's
backup interface and validate integrity plus financial/record equivalence.

## C08 closing and result lifetime

Closing selects at quote level: source observation within the frozen closing
window and trusted receipt strictly before the versioned kickoff cutoff.
Recording may occur later. Post-cutoff receipt is excluded even if the provider
timestamp predates cutoff. SUPPORTED needs comparable admitted evidence and
quality/disagreement gates, independent of ROI sign. Other comparable evidence
is INDICATIVE; no comparable evidence is UNAVAILABLE. Use bounded grace for
pre-cutoff receipts awaiting storage, then finalization; corrections append a
new closing revision. The precise grace policy will be frozen before I06 tests.

Live evaluations bind normalized target inputs, settings, event, rule/profile,
admission and evidence revisions. Expiry is no later than the earliest target
or contributing reference lifetime, kickoff or relevant profile/state validity.
The UI clears/invalidates on edits, incompatible revision, kickoff, stale state,
disconnection, sleep/resume or future clock. Older responses cannot attach to
newer inputs. Successful fetching never renews a quote. Supplemental comparisons
must match the active exact selection and disappear after line changes.

## C09 phase 2 implementation boundary and API compatibility

Keep existing flat quote request fields and `/api/evaluate`, `/api/bets`,
`/api/bets/{id}/settle`, `/api/export.csv` paths. Add explicit history fields rather
than make existing financial fields mean something different. New writes require
idempotency keys; actual writes require `accepted_at` and placed confirmation.
Add a separate reopen event path. Response projections can retain `quote`, `game`,
`evaluation`, `settlement`, `closing` and `audit` for UI migration, but must also
expose original evaluation/link validity, accepted calculation, immutable timestamps
and event history. Unavailable history must never masquerade as entry research.

Generate an immutable evaluation bundle containing the canonical target, original
request monetary text, result, exact reference snapshots, settings, event and full
profile snapshot, server evaluation/record times, calculation/input/revision hashes
and earliest expiry. Save the bundle with INSERT only; expose read-by-ID. Original
bundle bytes cannot change when global settings, sources or schedules change.
Accepted repricing is a separate labeled calculation; changing cost/quantity/net
returns does not authorize replacing pinned probabilities or ignoring profile
contradictions. Selection/venue/product/profile/contract mismatch invalidates the
historical link. A missing link never prevents an honest actual record.

Intent equivalence is based on validated canonical data (including normalized
monetary/time values), not incidental JSON whitespace or decimal scale. A UNIQUE
constraint plus one transaction enforces key equivalence/conflict under concurrency.
Distinct keys may create equal-term positions. Settlement/closing/reopen updates
append scoped events; stale whole-bet replacement is removed. A correction records
previous/current authoritative cash states and P&L delta; reopening restores open
exposure and reverses previously recognized realized P&L without deleting history.

Migrations inspect `user_version` and known schema before any journal-mode/DDL
mutation. Empty v0 and known v1 can migrate; unknown v0 layouts or newer versions
fail unchanged. Preserve legacy JSON bytes in original rows; use side metadata and
append-only projections for new provenance/history. Legacy ambiguous accepted/
receipt/evaluation times stay unknown. Keep indexed IDs, dates and foreign keys
where transactional and temporal queries need them, without an unnecessary ORM.

Manual events provide explicit teams, kickoff, season/phase/week and provenance;
new IDs are opaque. Provider-ID maps, schedule revisions and quarantines support
C07; `put_games` compatibility for internal synthetic fixtures is not permission
to merge ambiguous real provider events. Source snapshots/quote observations have
trusted receipt only from server collection/manual submission, never a user-entered
observed time. Source/admission revisions are immutable; initial policies cannot
qualify evidence. Concrete provider ingestion and source/closing behavior follow
after storage APIs freeze.

API mutations require JSON and an explicit same-origin intent header (document its
name/value for the frontend). Check exact scheme/host/port Origin, reject cross-site
fetch metadata, and reject arbitrary Host values. Originless local clients still
need the intent header. This is a browser request boundary, not authentication of
other local software. `testserver` is not a production host exception; test clients
use a loopback base URL or an explicit isolated factory test option. Preserve I01
import isolation. Production launch binds loopback; no default database is exercised
during development. Tests cover actual production middleware, CSV text fields and
immutable record operations, not only factory exceptions.
