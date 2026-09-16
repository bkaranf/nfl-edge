# NFL Edge prospective pilot protocol

Protocol ID: `nfl-edge-pilot-v1`. Status: **prepared; inactive**. No prospective
observations, accepted receipts, future outcomes or profitability are asserted.
Activation requires the implemented logging checks and separate contract/source
admission gates. Development fixtures never count as prospective observations.

Before the first due observation, persist this document's SHA-256, an activation
manifest, its SHA-256 and server activation time. Activated versions are immutable.
Changing selection, parameters or analysis creates a new version and separate
period; never rewrite earlier results or pool development with evaluation data.

## Fixed population and main question

Among prospectively logged, actually accepted, receipt-supported entries selected
under this protocol, what is cost-weighted realized return? Report open positions,
missing outcomes, deviations, selection failures and dependence. Four complete NFL
weeks are an operational pilot, not validation. Without actual entries the question
is unanswered. Paper rechecks measure displayed persistence, not fills or size.

The manifest names season/phase, four complete week IDs, UTC start/end and display
timezone; exact canonical event IDs and schedule snapshot hash; target venue/product,
profile and settlement-semantics hash; full-game markets and both sides; inclusion/
exclusion rules and due times. Freeze the universe independently of reference-board
or target availability, profile eligibility and modeled EV. Create every opportunity
before observations, including opportunities with no board row or no usable quote.

For each event inspect both sides of moneyline, the target's explicitly labeled
main spread, and explicitly labeled main total. Do not search alternate lines for
favorable EV. Without a unique main line record `INVALID_TARGET`; a successful
inspection finding no quote is `NO_TARGET_QUOTE`. Moneyline has no line. Exact
observed line becomes decision identity, not a reason to discard an opportunity.

Schedule revisions preserve event/opportunity IDs and revise pending due times only
within the fixed end. A move beyond it is `RESCHEDULED_OUTSIDE_WINDOW`; cancellation
is `CANCELLED`. A late-added game is a manifest exception outside the primary
population. Retain frozen sampling week and actual kickoff week. Never extend the
pilot until favorable results appear.

## Timing and identities

Initial nominal due time is kickoff minus 60 minutes, tolerance 2 minutes early to
5 minutes late. Order slots by due time, canonical event ID, market (`moneyline`,
`spread`, `total`), then side (`away`, `home` or `over`, `under`). Record misses.
Repeats cannot replace the primary failure/miss; they are workload and secondary
observations. Record actual times, never backdated trusted receipt.

Exactly one standard recheck is scheduled for the primary decision created by each
opportunity's primary initial attempt, if a valid economic candidate was observed,
even if profile/reference/screen gates fail. Due time is 120 seconds after that
observation, tolerance 15 seconds early to 30 seconds late. Selection is
independent of favorable EV and acceptance intent. It checks the original exact
contract. Immediate pre-acceptance recheck is an additional stage. No automatic
placement occurs. Source failure cannot establish disappearance. Decisions first
created by a protocol/acceptance recheck are secondary, even within the initial
clock window, and cannot recursively schedule another standard recheck.

| Identity | Meaning |
|---|---|
| `opportunity_id` | Frozen event/target/market/side inspection slot; exists without data |
| `attempt_id` | One stage-specific action/result; optional batch ID and repeat ordinal |
| `decision_id` | Protocol, event, venue/product/contract locator, market, period, side, exact canonical line and settlement-semantics hash |
| `recheck_id` | Scheduled obligation for an original decision, with one primary result |
| `acceptance_intent_id` | One placement intent, independent of snapshots or other equal-term intents |

Price, quantity and snapshots are children/revisions of one decision. A line change
creates a linked successor; different venue/product creates another. Profile
metadata changes preserving semantics hash do not split a signal. No-quote/failure
records have opportunity/attempt IDs but no fabricated decision ID.

Each stage has one exclusive terminal outcome plus overlapping reason flags.
Pending obligations remain pending until completed or explicitly missed.

| Stage | Terminal outcomes |
|---|---|
| Initial | `EVALUATED`, `NO_TARGET_QUOTE`, `INVALID_TARGET`, `SOURCE_FAILURE`, `MISSED_WINDOW`, `CANCELLED`, `RESCHEDULED_OUTSIDE_WINDOW` |
| Recheck | `VISIBLE_SAME_TERMS`, `VISIBLE_REPRICED`, `LINE_CHANGED`, `DISAPPEARED_OR_OFF`, `INVALID_TARGET`, `SOURCE_FAILURE`, `MISSED`, `CANCELLED`, `RESCHEDULED_OUTSIDE_WINDOW` |
| Acceptance intent | `ACCEPTED`, `VENUE_REJECTED`, `OPERATOR_DECLINED`, `TECHNICAL_FAILURE` |

`EVALUATED` means a valid target reached evaluation, even with INSUFFICIENT_DATA or
RESEARCH_ONLY output. Screening is separate from collection/placement outcomes.
DISAPPEARED_OR_OFF requires successful inspection. No intent differs from decline.
Once a standard obligation exists, invalid targets and schedule terminations remain
in its all-scheduled denominator and get their own terminal buckets; never silently
void them or label a cancellation as an operator miss.

## Frozen screen and exposure

Use 3 distinct admitted eligible books, 120-second maximum observed age, at least
3% least-favorable modeled ROI, 2 percentage points win-to-loss stress bounded by
win mass, strictly positive stressed ROI and at most 5-point win-estimate range.
Regular-season tie sensitivity is 0-5% where the confirmed profile permits it;
this is arbitrary sensitivity, not inferred likelihood. Admission, receipt and
rule matching apply. Integer lines remain research only. Unknown profiles and
unadmitted sources cannot pass. Never lower settings to generate candidates.

Freeze parameter, profile, source-policy/admission, calculation and code hashes.
Other-parameter observations remain logged as deviations/development. Caps at the
entered bankroll snapshot are 0.5% per entry, 1% per game open, 5% all open, rounded
down to cents. Exposure is separate from evidence; unlogged external exposure is
unknown. No automatic balance updates or compounding. Unknown quantity permits
total-return research only, not size/fillability or comparable deterioration claims.

## Explicit denominators

Counts precede rates. Zero denominator is UNAVAILABLE. Report the frozen universe,
due opportunities at cutoff, pending/not-yet-due slots and schedule terminations.
Primary opportunity rates include due missed/terminated slots; show termination
counts and any secondary actionable subset separately.

| Metric | Numerator / denominator |
|---|---|
| Initial start | Initial attempts started / frozen opportunities due |
| Initial buckets | Each exclusive outcome / frozen opportunities due |
| Exact-line, rule and eligible-evidence coverage | Distinct due opportunities whose primary initial decision meets each condition / frozen opportunities due; also conditional decision rates |
| Screen pass | Passing primary initial decisions / evaluated primary initial decisions; distinct due opportunities with a passing primary initial decision / frozen opportunities due |
| Standard recheck start | Started primary rechecks / all standard rechecks scheduled and due |
| Exact-target survival | Same-terms plus repriced same-contract results / all standard rechecks scheduled and due |
| Recheck buckets | Each exclusive result / that same all-scheduled denominator |
| Actual conversion | Distinct due opportunities with at least one accepted actual intent / frozen opportunities due |
| Placement success | Accepted actual intents / all terminal actual placement intents |
| No actual intent | Evaluated decisions without actual intent / evaluated decisions |

Show pending actual intents separately and an all-started secondary denominator.
Repeated attempts are workload, never replacements for opportunity/decision counts.
Opportunity numerators count each due opportunity at most once. Recheck-created
successor decisions cannot enlarge initial coverage/pass numerators. Accepted
decisions and intents remain separately reported counts, including secondary ones.
Unknown/stale reason rates may overlap; label them. Show actual quantities, target
observation-to-evaluation time, oldest reference age, remaining life and recheck delay.

## Actual reconciliation and return

Freeze one selection_evaluation_id before acceptance. Primary eligibility uses only
immutable evidence available no later than acceptance and frozen parameters. Actual
recording requires placed confirmation, real accepted time/economics; receipt ID/hash
is needed for receipt-supported inclusion. Later recording cannot establish earlier
evidence. Accepted repricing uses pinned original evidence only.

Report (1) the receipt-supported protocol-eligible actual subset and (2) every
pilot-linked placed-confirmed actual entry, including unqualified, over-cap,
parameter-mismatch, missing-receipt/linkage and other deviations. Each actual entry
reconciles once between primary and named deviation strata. Freeze exclusion
precedence: missing receipt, missing/invalid selection linkage, parameter/protocol
mismatch, failed screen, over cap, other deviation, then primary. Also show overlapping
flags. Never remove unfavorable outcomes or entries with missing closing. Paper
records carry no actual accepted cash, placement, exposure or actual P&L.

For each population settled ROI is `(sum credited returns - sum corresponding
accepted costs) / sum corresponding settled accepted costs`. Open entries are absent
from settled ROI but present in accepted cost, open exposure and count/cost-weighted
outcome completeness. Recorded cash is authoritative; labels cannot invent return.
Closing quality/missingness is separate. Deterioration needs comparable quantity/
profile and original immutable evidence; report unavailable linkage counts.

## Calibration, dependence and drawdown

At most one calibration_anchor_evaluation_id per primary initial decision is selected
mechanically: its first complete compatible forecast from its primary initial
attempt/window with frozen parameter hash. Recheck-created successors, incomplete/
incompatible forecasts and unresolved outcomes have explicit calibration exclusion
reasons. Later snapshots or acceptance cannot replace an anchor or fill in a
previously unavailable initial forecast. Report the all-forecast population once; acceptance-
time or actual-only subsets are labeled secondary. Never count one decision again
as both paper and actual in the same population.

Keep market/rule/profile/product/evidence-tier strata compatible. Binary half-line
spreads and totals remain separate. Conditional-no-tie moneylines have a separate
conditional denominator; ties are counted exclusions, never losses. Integer strict-
win diagnostics are excluded. Prespecify Brier score with no fitted bins/curve for
this sparse pilot; report raw forecast/outcome pairs, counts, mean forecast and
empirical rate. Missing outcomes stay missing.

Canonical event is the minimum cluster. Show decisions, entries, games, frozen
sampling weeks, actual kickoff weeks and cost/per-game concentration. Four weeks
supports descriptive reports only: no entry-level intervals, p-values or promotion
rule. Later cluster intervals require a separate predeclared method/period. Source,
margin-removal, tie, fee and execution sensitivities are diagnostics, not confidence
bounds. Same-source closing evidence is correlated.

Audit-time realized-P&L drawdown starts at zero, ordered by immutable server
settlement-event sequence. First settlement contributes return minus accepted cost;
correction/reversal/reopen contributes only the delta from prior authoritative
realized state, without charging cost twice. Exclude paper and open stakes; report
open exposure separately. Maximum absolute drawdown is largest running peak minus
later cumulative realized P&L. Percentage drawdown is UNAVAILABLE without one fixed
activation bankroll denominator; never splice per-entry bankroll snapshots.

## Instrumentation gate

Persist manifests/schedule revisions, all five identities, stage and due/start/
observed/received/evaluated/accepted/recorded times, prospective/development mode,
original economic strings, immutable evaluation/source/profile snapshots, eligibility
and deviations, settlement event sequence/deltas and closing revisions. Reports
include cutoff, code/hash, all numerator/denominator counts and distinct game/weeks.
The minimum expected-result suite is `reports/R03.md` I08-P01 through P08.

Activation remains disabled until logging/denominator/identity/financial/temporal
checks pass and required real profile/source evidence is separately admitted.
Implementation and synthetic verification do not fabricate a four-week dataset.
