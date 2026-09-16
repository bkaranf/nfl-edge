# NFL Edge v0.2 — Trusted Quote Research and Prospective Paper Pilot

**Version:** 2.0, September 15, 2026  
**Repository:** `bkaranf/nfl-edge`  
**Historical review anchor:** `20e954bb175eaa8f3966ccf0327bb0b4476008bd`  
**Expected local workspace:** `C:\projects\nfl-edge`; verify the selected checkout rather than assuming this path.  
**Orchestrator:** GPT-6 Astra (`gpt-6-astra`)  
**All implementation, investigation, and review subagents:** GPT-5.6 Sol (`gpt-5.6-sol`)  
**Delivery mode:** local changes and local verification only. No automatic wagering, push, PR, merge, deployment, or external messaging.

## 0. Authority, evidence, and decisions

This is the consolidated forward implementation plan. It incorporates the existing NFL Edge requirements and earlier independent review, the user-supplied transcript associated with YouTube video `MSbacZ99E14`, selected documentation from Kun Chen's repositories, and current official Codex documentation. Sources and verification limits are in Section 16.

The original review packet and tests remain historical evidence, not competing implementation plans. Keep them intact and link to this plan from the README. Do not reset or downgrade the working repository to the review anchor. At execution time, compare the actual checkout with that anchor, identify already-fixed findings, and preserve unrelated work.

The previous review reported 21 original passing tests and 13 characterization cases reproducing problematic behavior or absent safeguards. Those are prior-run results, not tests executed while preparing this plan. Characterization tests intentionally passing against incorrect behavior must be converted into desired-behavior regression tests. A filename, model assertion, or green test count is not verification of the intended behavior.

The video is used through the supplied transcript, not a claim of independently watching every visual demonstration. Repository README claims describe their authors' products; those tools were not installed, executed, or security-audited for this plan. Our implementation decisions are proposals explicitly adopted below, not claims made by the video.

### Decisions already made

- Keep the local Windows React/TypeScript + FastAPI/Python + SQLite application. Fix it incrementally.
- Deliver an on-demand exact-quote checker, evidence board, and trustworthy journal, not an automatic Underdog opportunity scanner.
- Use native Codex subagents. Adopt Firstmate's operating ideas without installing the entire Firstmate distribution.
- Astra plans, delegates, reconciles, integrates, and signs off. Sol performs bounded investigation, implementation, and independent review. No silent fallback to Luna, Terra, another vendor, or another model.
- Default to at most four concurrent Sol tasks, with no more than two writing tasks and no overlapping file ownership. These are provisional resource limits for this project, not a demonstrated optimal agent count.
- Disable integer-line screen qualification in v0.2. Preserve clearly labeled research calculations and journal records. Do not delete historical integer positions.
- Support production screening only for explicitly verified settlement profiles. Unsupported quotes can be recorded but cannot pass.
- Keep the provisional probability screens visible and frozen for the initial prospective protocol. Do not weaken them to create candidates.
- Finish engineering and instrument the pilot. Future games, account-specific receipts, and profitability evidence are separate milestones, not fabricated completion criteria.

## 1. Objective and success definition

Answer the following for one exact manually entered Underdog quote:

> Given this game's exact outcome definition, the all-in entry cost, the net returns in each supported settlement state, and contemporaneous comparable reference evidence, what is the estimated expected return, what assumptions support it, and what prevents relying on it?

The product must make unsupported conclusions difficult and missing evidence obvious. A valid session may produce zero qualifying candidates.

### Three separate success levels

| Level | Successful outcome | What it does not establish |
|---|---|---|
| Reliable research application | Reproducible calculations, durable evidence and records, useful research-only output, functioning local workflows and recovery | That reference probabilities are true or that an opportunity is executable |
| Evidence-screen readiness | At least one verified real contract profile and a complete documented quality path for qualifying an actual quote | Guaranteed returns or independence among books |
| Strategy evidence | Prospective, out-of-sample, execution-aware results with uncertainty and honest missing-data treatment | Permanent profitability, unlimited size, or a guaranteed win rate |

The Codex build goal ends at the first level, plus the second where actual evidence permits it, and delivery of the pilot protocol and instrumentation. Strategy validation is explicitly outside that build goal.

## 2. Scope and non-goals

### Included

NFL pregame full-game moneylines, spreads, and combined game totals; exact-line reference comparison; manual Underdog quotes; manual sportsbook pairs; fees and supported settlement profiles; quote lifetime and source health; separate paper and actual records; exposure caps; settlement corrections; closing comparisons; CSV exports; local diagnostic/evidence reports; Windows setup, verification, backup, and restore.

Moneylines require verified tie handling. Half-point spreads/totals can qualify under verified rules. Integer lines are research-only until a separate model-admission decision.

### Excluded

Live betting, player props, parlays, automatic placement, account funding, credential storage for betting venues, account scraping, proxy/geolocation bypass, paid data dependencies, public hosting, an independent NFL forecasting model, cloud orchestration, Discord/X relays, automatic publishing, remote secondmates, and unbounded self-improvement. Development agents are not production components: the application must run without an LLM or paid model API.

The user is in South Carolina; actual account/product eligibility and specific contracts must be checked in the app before treating a market as supported. This plan does not make a legal eligibility determination.

## 3. Video lessons translated into this project

The supplied transcript describes Firstmate as a single point of contact, crewmates working in parallel, explicit dispatch rules, queued versus immediate requests, status/decision summaries, visual review artifacts, evidence-backed validation, and retrospective instruction improvements. It also demonstrates choices that are deliberately not adopted here. [S1]

| Video idea | NFL Edge implementation | Boundary |
|---|---|---|
| One first mate, many crewmates | Astra is the single user-facing coordinator; every child is Sol | No requirement to juggle agent sessions yourself |
| Explicit dispatch rules | Task briefs specify model, effort, scope, files, tests, dependencies, and return format | Spare quota never overrides Astra/Sol selection |
| Parallel tasks | Parallelize genuinely independent work after shared interfaces are agreed | Isolated worktrees do not eliminate semantic conflicts; serialize shared-file changes |
| Ship versus scout tasks | Investigation tasks return evidence/recommendations; implementation tasks return bounded code and tests | A scout does not quietly edit the product or expand scope |
| Bearings and Ahoy | Persist task status, open decisions, last completed milestone, and a concise catch-up digest | These are project interaction conventions, not claimed built-in Codex slash commands |
| Queued follow-up versus steering | New nonurgent ideas enter the backlog; explicit scope-changing direction pauses affected tasks and invalidates outdated briefs | Do not assume Pi's keyboard shortcuts work in Codex |
| Lavish visual feedback | Produce local before/after desktop/mobile screenshots and a self-contained HTML review report | Core completion does not depend on installing Lavish, hosted sharing, or immediate user feedback |
| No-mistakes validation | Risk-based local review, executable tests, browser scenarios, evidence, then final Astra review | No `git push no-mistakes`, automatic PR, force push, or YOLO merge |
| Backpass-style learning | Promote repeated observed workflow failures into small, reviewed instruction changes | Not model training; never relax financial or security gates automatically |
| Calm output | Show milestone outcomes and genuine blockers; retain detailed logs on disk | Do not hide errors, approvals, uncertainty, or untested claims |
| Attention over token micromanagement | Use bounded context packets and native compaction; checkpoint durable state before context is lost | Do not copy Claude-specific environment variables or a fixed 500k threshold into Codex |
| Risk-specific guardrails | Pricing, temporal evidence, records, migrations, security, and pass-label UI receive the strongest gate | Cosmetic changes cannot silently change financial meaning |

The transcript itself illustrates a missed northern-lights task and an orchestrator briefly unaware of feedback sent directly to a worker. Counter those failure modes explicitly: assign every requested deliverable an ID, reconcile all direct feedback into the authoritative decision log, and require task coverage before completion. Do not treat many active agents as evidence of high throughput. [S1]

## 4. Repository adoption decisions

This is a targeted review of relevant projects, not a claim to audit every repository on the profile.

| Project | Documentation-supported idea | Final adoption decision |
|---|---|---|
| `kunchenguid/firstmate` | Single liaison, isolated tasks, durable state, scout/ship distinction, project modes; README advertises macOS/Linux | Adopt operating conventions; use native Codex on Windows. Do not transplant Firstmate internal skills into NFL Edge or install its whole distribution. [S2] |
| `kunchenguid/no-mistakes` | Local validation pipeline that ordinarily proceeds to push, PR, and CI | Reimplement a small local verification sequence using existing tests/scripts. Do not invoke its publishing workflow. [S3] |
| `kunchenguid/lavish-axi` | Local HTML review and feedback; hosted sharing opt-in; README advertises Windows | Use its visual-review concept with ordinary local HTML/screenshots. Optional pinned, reviewed installation only after the core release, if a real feedback need remains. [S4] |
| `kunchenguid/backpass` | Evidence-linked instruction proposals and separate human-approved apply; README advertises macOS/Linux | Use small manual retrospective proposals from at least two distinct incidents/sessions; exceptions for immediate safety corrections. No automatic transcript upload, global memory edits, or new dependency. [S5] |
| `kunchenguid/treehouse` | Reusable isolated worktrees; README advertises Windows | Use native Git/Codex worktrees first. Consider pooling only after measured setup overhead justifies it. Do not run install pipes or destructive worktree cleanup. [S6] |
| `kunchenguid/quota-axi` | Reports local subscription quota evidence; access may involve local auth stores | Prefer native Codex usage/status. No new credential reader or cross-provider routing is needed for the fixed Astra/Sol plan. [S7] |
| Herdr, through Firstmate's backend guide | Terminal/session orchestration with protocol-dependent capabilities | Defer. One Windows project does not need an additional terminal orchestration backend or remote fleet. [S8] |

No source code from these projects is copied by this plan. Any later reuse or installation requires exact revision/package pinning, license review, dependency/permission review, an explicit benefit, a compatible Windows validation, and a reversible installation path. A README platform badge is not independent platform verification.

## 5. Astra/Sol operating contract

### Roles

| Role | Model | Responsibilities | Prohibitions |
|---|---|---|---|
| Primary orchestrator | Astra | Repository preflight, interfaces, task graph, delegation, risk decisions, integration, final verification, concise user updates | Do not label implementation complete solely from a worker's report |
| General implementation/scout | Sol | One bounded work package; default high effort | No scope expansion, new delegation, publication, or editing unowned paths |
| Financial/storage implementation | Sol | Payoff, history, transaction, or migration changes; max effort where the selected runtime supports it | No production data migration or invented settlement facts |
| Independent reviewer | A fresh Sol context, not the author | Adversarial review of assigned diff and evidence; max effort where supported | No self-review, no edits to the reviewed patch, no accepting assertions as tests |

Astra uses high effort as the ordinary coordination default and can select a supported deeper effort for difficult decisions. All children remain Sol. Model identity is a runtime configuration requirement, not a nickname in a prompt. Verify the primary model and a spawned child's model using runtime/session metadata. If assignment cannot be verified or enforced, record `MODEL_ROUTING_BLOCKED`; do not secretly substitute another model or claim model-specific execution. Use the provided TOML examples only after checking current installed configuration support. [S9–S12]

### Delegation brief

Every task has a unique ID and contains:

```
Task ID and type: SCOUT / IMPLEMENT / REVIEW
Objective and user-visible consequence
Base revision and isolated worktree or exclusive write scope
Allowed files; read-only reference files
Dependencies and agreed schema/API contracts
Explicit non-goals and immutable constraints
Acceptance scenarios, expected results, and test commands
Risk class and supported reasoning effort
Evidence location and return format
Stop/escalation condition
```

Return format: result, actual changed files, commands executed, exit codes, test evidence, unresolved findings, assumptions, and next required decision. Include exact paths and revision identifiers. Redact secrets and keep operational log content out of chat unless needed.

### Parallelism and ownership

Start with up to four concurrent Sol tasks and at most two writers. Count investigators and reviewers within the four. No nested agent fleet. Use supported wait/completion mechanisms rather than rapid status polling.

Astra establishes shared domain/API/storage contracts before concurrent implementation. One writer owns `domain.py` and shared types at a time. One writer owns migrations/storage at a time. One writer owns shared dependency files at a time. Integration changes are serialized and followed by combined tests. Worktrees use separate test databases, output directories, and ports.

Astra maintains the task/ownership ledger. Never take over a worktree because a clock expired without first checking the previous task stopped. Never run destructive Git operations to make a task appear clean. Preserve user edits; stage only clearly owned paths. Local branches and worktrees are permitted; commit/checkpoint behavior follows applicable repository policy. No autonomous merge or publication is authorized.

### Durable project memory

Keep the root `AGENTS.md` short, preferably under about 100 lines, pointing to the authoritative plan and verification commands. Use existing equivalents when present rather than duplicating records.

- `docs/STATUS.md`: tasks, dependencies, owner/model, write scope, progress, evidence, blockers, and next steps.
- `docs/DECISIONS.md`: decision ID, options, selected option, reason, scope, evidence, authority, and status.
- `docs/VERIFICATION.md`: acceptance matrix, commands/results, environment, tests not run, and release verdict.
- `docs/SOURCE_REGISTRY.md`: access basis, coverage, semantics, latency/caching evidence, and admission state.
- `docs/PILOT_PROTOCOL.md`: frozen prospective sampling and analysis rules.
- `.qa/`: ignored local logs, screenshots, test databases, reports, and raw evidence; never a default location for irreplaceable user records.

At each milestone, deliver a brief catch-up: completed, currently underway, blocked, and decisions needed. Before compaction, interruption, or closing a task, checkpoint the ledger and evidence pointers. Resume from files, not supposed perfect chat memory. Use native model-default compaction initially; adjust a supported setting only after observing a specific problem. [S10, S11, S13]

Instruction improvements are proposed at milestone boundaries, not an endless autonomous optimization project. Require evidence from multiple independent incidents for ordinary changes. Never auto-change model assignments, safety boundaries, statistical thresholds, source admission, or settlement profiles based on a retrospective.

## 6. Product and UI specification

### Board

Show exact selection, event start/state, underlying sportsbook, provenance channel, both-side pair availability, observation time, upstream-age status, eligible-reference count, and research probability. Label conditional no-tie moneyline probability explicitly. Do not label an integer strict-win estimate as a generic binary probability.

Expose source eligibility and quote expiry beside the numbers. Calculate counts from current data rather than hardcoding two connected books. A reference board row is not an Underdog opportunity until an actual target quote has been entered and evaluated. An optional conditional price ceiling must be labeled for the fixed entered payout/quantity, not a discovered offer.

### Quote checker

Require exact event/market/side/line/period, exchange and supported profile identity, actual all-in cost, net winning return, other outcome returns where needed, true quote observation time, and actual/hypothetical/accepted status. Capture quantity and receipt/contract identity where available. Unknown quantity cannot establish size or scalable execution claims; total-return research calculations can still be shown when mathematically supported.

Display modeled ROI, sensitivity results, maximum cost at this quantity, evidence tier, expiry, ordinary-completion qualification, unsupported reasons, and separate exposure status. Use wording such as "Estimated positive EV under stated assumptions," not "guaranteed edge" or a win-rate assurance.

Status enum:

- `INSUFFICIENT_DATA`: cannot construct a defensible supported calculation.
- `RESEARCH_ONLY`: an indicative calculation exists, but one or more evidence/profile conditions fail, or the market is deliberately research-only.
- `MEETS_ESTIMATED_SCREEN`: current quote passes explicit provisional checks for a supported profile.
- `EXPIRED`: a previously current calculation is no longer valid for the active workflow.

Show specific reason codes, not a single generic checkbox failure. Unknown rules or source failures must not become a green result.

### Journal

Record paper observations and actual accepted entries separately, including unqualified or over-cap actual entries. Recording is not placement or endorsement. Separate original observed quote, immutable evaluation, accepted economics, acceptance time, recording time, and settlement events. A later saved accepted entry must never receive an unlabeled current-price "entry EV."

Support settlement corrections and reopening/reversal through auditable events when required, rather than destructive overwrites. Recorded cash return is the P&L authority; outcome-label inconsistencies create an explicit warning, not invented financial values. Export free-text safely for spreadsheet use.

### Visual review

Produce desktop and approximately 390-pixel-width evidence for ordinary, empty, invalid, stale, unavailable, and recovery states. Check keyboard focus, readable text, control reachability, exact units, and sign conventions. At most two targeted visual alternatives may be produced when a real unresolved decision exists; otherwise preserve the existing coherent layout. A screenshot demonstrates appearance, not transaction or timer correctness.

Generate a self-contained local HTML evidence report with links to recorded tests, screenshots, remaining decisions, and readiness status. It must use local assets and escaped user text, and must not contact a CDN, analytics service, or hosted sharing endpoint.

## 7. Financial model and immutable safeguards

### Money and probability semantics

For American odds A:

```
d = 1 + A/100           when A >= 100
d = 1 + 100/abs(A)      when A <= -100
r = 1/d
q_A = r_A / (r_A + r_B)
q_B = 1 - q_A
```

Pair both sides from the same originating book, exact market/profile, coherent snapshot, and matching line. Never mix opposite sides across books or snapshots. Different distributors of one book are one underlying reference. A book count does not demonstrate statistical independence.

Use proportional margin removal as the frozen baseline, with explicitly labeled alternatives for sensitivity. Do not silently change algorithms by selection. The median is a descriptive market-derived estimate, not the true probability. Unknown or suspicious pair margins must be flagged through documented source-specific checks, not normalized into unjustified confidence.

Represent supported settlement probabilities and total net returns explicitly:

```
V = p_win*W + p_tie_or_push*T + p_loss*L
EV = V - C
ROI = EV / C
```

`C` includes every entry fee exactly once. `W`, `T`, and `L` are net outcome returns, not profits. For additional exceptional states, extend the payoff vector only with defensible probabilities; otherwise clearly label EV as conditional on ordinary completion. No zero-substitution for unknown fees, rules, returns, or reference data.

Use Decimal or integer-minor-unit accounting for cash values, deterministic rounding, and bounded finite probability calculations. Persist the exact original monetary strings and calculation version. Preserve strictly positive stressed ROI at a cent-rounded ceiling, including tests where the next cent fails.

For ordinary binary no-push markets, `p_break_even = C/W`. When push return matters and loss return is zero, `p_win_break_even = (C - p_push*T)/W`. Do not display `C/W` as the complete break-even condition for a multi-outcome market. Handle impossible/out-of-range thresholds explicitly rather than silently clipping them into an apparently feasible probability.

### Moneyline ties

If source moneylines refund ties, normalized q is conditional on no tie:

```
p_win = (1 - t)*q
p_tie = t
p_loss = (1 - t)*(1 - q)
```

Tie payout comes from the verified profile and quantity, never automatically from `W/2`. Outcome-specific fees can make net tie return differ from half the net winning return. Contradictory explicit input must be rejected or reconciled visibly; it must never be ignored.

Use the existing 0–5% regular-season tie range only as an explicitly arbitrary sensitivity. It is not measured likelihood or confidence. Evaluate endpoint payoffs under the confirmed profile and take the least favorable modeled result. Postseason no-tie treatment requires verified event/profile classification, not an unreliable provider default.

### Integer spreads and totals

The strict/inclusive adjacent half-point identities are valid probability identities, but differently priced alternate-line markets need not provide calibrated estimates of one distribution.

For v0.2, `MEETS_ESTIMATED_SCREEN` is disabled for integer lines. Retain diagnostic research calculations, missingness, and integer journal support. Before any later qualification, require complete same-book adjacent pairs, compatible receipt times, identical rules, coherent joint win/push/loss aggregation, sign/symmetry tests, full payoff disagreement, and out-of-sample evidence on the selected estimation method. Do not claim arithmetic coherence alone solves alternate-line margin bias.

### Provisional screen settings

| Setting | Frozen starting point | Interpretation |
|---|---:|---|
| Distinct admitted eligible books | 3 | Corroboration heuristic |
| Maximum quote/reference observation age | 120 seconds | Subject to source admission; observed-now is not upstream-freshness proof |
| Minimum least-favorable modeled ROI | 3% | Economic screening floor |
| Win-probability stress | 2 percentage points moved from win to loss, at most available win mass | Sensitivity, not a lower confidence bound |
| Stressed ROI | Strictly greater than 0 | Required numerical condition |
| Win-estimate range | At most 5 percentage points | Provisional filter; also report payoff dispersion and source sensitivity |
| Regular-season tie sensitivity | 0–5% | Uncalibrated range, not inferred likelihood |

Report source-exclusion and alternative margin-removal sensitivities as diagnostics. A positive value that reverses under a documented plausible variant must carry a fragile-estimate warning; do not promote diagnostic robustness into statistical confidence.

At fixed payout/quantity:

```
C_max <= V_low / (1 + minimum_ROI)
C_max < V_stress
```

Changing quantity, accepted fees, market identity, or economics requires a new calculation. Exposure remains separate: provisional per-entry 0.5%, per-game open 1%, aggregate open 5% of a user-entered bankroll snapshot, rounded down to cents. No invented balance, external-account access, compounding, or automatic bankroll reset. Unlogged external positions are outside the journal's coverage.

## 8. Data-source policy and temporal integrity

### Initial roles

| Input | Role | Admission ceiling at start |
|---|---|---|
| ESPN-carried sportsbook lines | Schedule/state plus redistributed price research | Underlying book counts once; unknown upstream age remains research-only |
| Bovada | Existing directly observed price source | Eligibility conditional on documented access and freshness/caching qualification, not merely `kind=direct` |
| Kalshi public REST | Supplemental exchange comparison | Not an Underdog offer or a sportsbook vote; fees, rules, and size differ |
| Manual sportsbook pairs | Exact-line corroboration | Genuine source/observation evidence and matching rules required |
| Manual Underdog quote | Target economics | Exact current or actually accepted values, with real observation/acceptance times |

Kalshi documents unauthenticated market-data REST access and pagination, but this is not verification of every current NFL series or unrestricted collection. Pinnacle's official documentation states that public API access is closed, with application-based exceptions; do not assume a free drop-in feed. [S14, S15]

Admit each source only after documenting permitted access, collection limits, origin versus distributor, exact market/rule semantics, suspended-state behavior, event mapping, known timestamp meanings, caching limitations, fixtures, and failure behavior. Source states are `UNASSESSED`, `RESEARCH_ONLY`, `ELIGIBLE`, `DEGRADED`, or `DISABLED`, with effective time and reason. Admission changes invalidate dependent live screen status; historical evidence is retained.

Maintain one shared per-source rate limiter/cooldown across board refreshes, quote checks, and any other collector caller. Do not let parallel Sol agents probe the same endpoint independently. Respect Retry-After, bounded retries, backoff, stop on repeated access denial, and circuit breaking. On failed refresh keep the original timestamps. A fresh empty response must not revive a disappeared or suspended market. A transient fetch error and explicit market suspension are distinct states.

### Timing model

Persist at least:

- Request start and response completion.
- Provider-published price timestamp when supplied, with its documented meaning.
- Source-observed time and earliest provable local receipt/availability time.
- Ingestion/recording time, which may be later.
- Target observation, evaluation, acceptance, and recording times.
- Event schedule revisions, actual/authoritative live-state evidence, and closing cutoff.

For prospective entry evaluation, every reference must have been available to the system no later than evaluation/acceptance as applicable. A provider timestamp earlier than acceptance is not sufficient if the response arrived later. Backdated manual fields alone do not establish historical availability.

For closing, a response genuinely received before kickoff can be eligible even when its containing batch is stored afterward. Conversely, a post-kickoff fetch carrying an older provider timestamp is not a contemporaneous closing observation. Late manual/imported evidence must be labeled retrospective unless verified capture provenance supports stronger treatment.

Use UTC internally and clear local display. Invalid/future clocks, sleep/resume gaps, stale event state, inconsistent schedules, and uncertain kickoff must fail closed for qualification.

### Cadence

Choose on-demand operation for v0.2. Display the prior reference board, collect under permitted limits when requested, then evaluate the new target quote. Do not imply continuous coverage. The existing five-minute background interval and two-minute age screen are intentionally not reconciled by declaring older data fresh. Source-specific faster collection is deferred until evidence and access terms justify it.

Measure source update behavior, time to complete manual reference/target entry, remaining reference lifetime at evaluation, and target recheck survival. Do not assert which bottleneck dominates before measuring.

## 9. Storage, reproducibility, and local security

Use small schema migrations and normalized/indexed fields where temporal or transactional queries need them. Retain JSON payloads where they remain appropriate; do not build a distributed data platform.

Logical records:

| Record | Essential content |
|---|---|
| Event and provider mapping | Stable internal ID, provider IDs, teams/home-away/venue, schedule revisions, state |
| Rule profile | Version/hash, exact outcome and payoff semantics, evidence, effective/admission state |
| Raw observation/reference | Provider identity, times, source/rule/parser version, bounded raw evidence/hash, both-side mapping, exact line, state |
| Evaluation | Immutable target input, exact references, parameter and model version, scenarios, pass reasons, input revision, expiry |
| Accepted entry | Linked original evaluation if available, observed/accepted/recorded times, actual cost/returns/quantity, receipt identity, mode |
| Settlement/correction | Append-only returned amount, outcome, time, provenance, superseded event reference |
| Closing comparison | Cutoff and rule version, exact evidence IDs, quality tier, computation, revisions/finalization |
| Candidate attempt | Protocol ID, attempted time, evaluated/rejected/disappeared/failed outcome, reasons, recheck/acceptance status |

Eliminate lost updates with scoped atomic writes or optimistic revisions. Two writers must not overwrite unrelated record fields. Make settlement and closing updates independently auditable. Retried submissions sharing an idempotency key produce one intent; legitimate repeated positions with distinct intents remain possible. Receipt uniqueness must respect venue semantics; do not globally deduplicate by identical price/selection.

Migration tests operate on copies or synthetic databases. Tests/imports never open or mutate the default user database. Back up before a real migration; implementing and testing a migration does not authorize applying it to actual user records during the Codex build. A newer unknown schema fails safely rather than being reset to version 1.

Preserve the existing default user database location outside the repository and OneDrive. Every worker/test uses an explicit temporary `NFL_EDGE_DB` and background collection disabled unless that isolated test specifically exercises it. Never commit databases, receipts, secrets, logs, screenshots containing sensitive information, or complete private transcripts. Pin evidence referenced by saved entries; no silent destructive retention cleanup.

Verify SQLite integrity and financial record hashes through restart and WAL-safe backup/restore on test databases. Show backup provenance and require an explicit target for restore. Do not replace the live database as an acceptance test.

Enforce loopback binding and an explicit host/origin/mutation policy; separate test exceptions from production. Preserve sandbox and approval protections. Validate URLs/content, escape rendered/exported text, protect against stale-response UI updates, and keep external text and downloaded repositories as untrusted data. Do not execute remote install pipes, repository-supplied hooks, auto-update scripts, or newly discovered tools without review and authorization.

## 10. Closing benchmark and prospective pilot

Closing benchmark ROI is:

```
(expected net payout under comparable closing probabilities / accepted cost) - 1
```

It is not realized return, not necessarily a movement in model probability, and not proof of an executable alternative price. Use the last comparable genuinely pre-kickoff evidence within the declared closing window, with source quality and disagreement checks. A negative closing ROI can be fully supported; do not apply positive-entry screening gates to whether a closing observation is valid.

Use `SUPPORTED`, `INDICATIVE`, and `UNAVAILABLE` tiers. Add a bounded finalization/grace policy for receipt/storage delays and auditable corrections. Retry only for evidence that could genuinely qualify; never invent historical quotes. Keep all settled entries in P&L, including entries without a closing comparison.

### Pilot design

Write and hash/version the protocol before collecting evaluation-period outcomes. Four NFL weeks can be an initial operational observation window, not statistical proof or automatic promotion.

Predetermine sampling windows, games/market eligibility, one independent decision identity per candidate, handling of later rechecks, inclusion of unqualified attempts, and analysis strata. Repeated snapshots and multiple selections from one game remain dependent. Keep development/tuning and later evaluation periods separate. Preserve every attempted observation's outcome, including source failure, no quote, disappearance, rejection, and no acceptance.

Metrics:

- Exact-line and supported-rule coverage, with denominators.
- Eligible-source completeness, unknown/stale rates, and outages.
- Reference age at evaluation, target observation-to-evaluation time, and recheck delay.
- Fraction of targets still available at recheck; separately, actual accepted quantity/economics when available.
- Estimated versus accepted fee-adjusted ROI and price deterioration.
- Calibration in appropriate probability/outcome strata.
- Cost-weighted realized ROI, total cost, open exposure, drawdown, sample size, and distinct game/week clusters.
- Closing quality and missingness by market and entry evidence tier.
- Source exclusion, margin-removal, tie, fee, and execution sensitivities.

A paper recheck demonstrates displayed-price persistence, not actual fillability or scalable size. Without accepted receipts, executable-edge evidence remains unproven. Same-source closing prices are correlated benchmark evidence, not an independent oracle.

Use uncertainty procedures appropriate to the clustered decision unit and actual sample size. Do not treat a tiny number of weeks as enough for stable cluster asymptotics. Predefine one main performance question, label exploratory subgroup results, and avoid repeatedly checking until a favorable significance result appears. Report uncertainty and failed hypotheses, not just point ROI.

A successful pilot may conclude: operationally useful but insufficient probability evidence; target delay destroys the discrepancy; adequate research signal needing more independent data; or no durable edge. None of these justifies silently relaxing the gates.

## 11. Implementation sequence and task graph

This sequence prioritizes false-positive and record-integrity prevention. Effort categories are relative scope, not promises or delivery estimates.

| Phase | Owner/work | Dependencies | Exit criteria | Effort |
|---|---|---|---|---|
| 0. Preflight and contracts | Astra with read-only Sol scouts | Selected checkout | Remote/branch/commit/worktree and environment recorded; prior findings mapped; baseline tests run safely; model routing verified; write ownership and domain/API contracts agreed | Small–medium |
| 1. Contain invalid qualification | Sol financial implementer; fresh Sol reviewer; Astra sign-off | Phase 0 | Unsupported rules cannot pass; no ignored moneyline tie returns; integer qualification disabled; original journal data preserved | Medium |
| 2. Reliable data and history foundation | Sol storage writer; source/parser writer only in disjoint files | Agreed contracts, Phase 1 | Durable identities/times; immutable evaluations; idempotency; concurrent update tests; safe migrations and imports; source validation and error isolation | Large |
| 3. Quote lifecycle and journal UI | Sol frontend writer; closing work only after storage API settles | Phase 2 APIs | Input/revision-bound asynchronous results, true earliest expiry, correct supplemental identity, honest acceptance logging, closing cutoff/quality/revisions | Medium–large |
| 4. Source admission and operational workflow | Sol source scout/implementer; Astra admission decision | Stable provenance and collectors | Published registry with evidence; permitted on-demand collection; actual manual times and failure/disappearance logging; no automatic threshold reduction | Medium, evidence-constrained |
| 5. Local delivery and adversarial verification | Sol QA/reviewer; Astra integration | Prior phases | Combined backend/type/build checks, isolated browser flows, Windows verification where available, backup/recovery evidence, local HTML review and exception report | Medium–large |
| 6. Pilot instrumentation and handoff | Sol analyst/documentation; Astra final audit | Trustworthy event/evaluation/journal records | Frozen protocol and metric definitions, tests for denominators and missingness, scripts/user instructions, final readiness report | Medium |

Parallelism rules: Phase 0 scouts can run concurrently. Phase 2 storage and providers may run concurrently only after contracts are frozen and shared domain edits are serialized. Phase 3 frontend and closing can run concurrently only against stable APIs. Final combined integration tests are mandatory even if every isolated branch passed.

### Prior review traceability

| Review item | Primary work packages | Required proof |
|---|---|---|
| F1 settlement/payoffs | Phase 1 | Explicit supported profile, contradiction rejection, net tie arithmetic |
| F2 integer incoherence | Phase 1 containment; later separate admission | No integer pass; coherent diagnostic vector/sign tests |
| F3 late accepted-entry evidence | Phase 2/3 | Original/accepted/recorded time separation and no lookahead |
| F4 lost updates/duplicates | Phase 2 | Concurrent settlement+closing interleaving, idempotency tests |
| F5 display/input expiry | Phase 3 | Browser fake-clock/kickoff/settings/race/line-change scenarios |
| F6 closing timing/quality | Phase 3 | Receipt vs batch cutoff and adverse benchmark supported correctly |
| F7 parser isolation | Phase 2 | OFF/unavailable/malformed outcomes preserve unrelated coverage |
| F8 source/timing ceiling | Phase 4 | Honest source admission and on-demand/manual workflow measurements |
| F9 identity/provenance | Phase 2 | Rescheduling preserves linked history/exposure; exact rule/period identity |
| F10 delivery/test isolation | Phase 2/5 | No default-DB side effects, migration integrity, verified platform/recovery |

## 12. Executable acceptance catalogue

For every case record test ID, risk, fixture, expected behavior, command, result, environment, and evidence path. Do not replace tests with natural-language assertions.

### Financial examples and edge cases

1. Fair coin at -115: C=115, W=215, p=0.5 gives V=107.5, EV=-7.5, ROI=-6.52173913%; must not pass.
2. Nonzero-overround pair -120/+100 normalizes selected-side q to 12/23 = 0.5217391304.
3. p=0.55, W=20, C=10.50 gives EV=0.50 and ROI=4.76190476%; a 2-point win-to-loss stress gives EV=0.10 and ROI=0.95238095%. Quality/profile gates still apply.
4. V_low=10 and V_stress=9.60 at a 3% floor: the maximum cent-valued cost satisfying both conditions is 9.59. The next cent must fail strict stressed positivity.
5. Contradictory moneyline example: q=.74, W=100, C=70.60, t_max=.05, explicit T=0 must not be ignored or converted to T=50. A contradictory profile must reject; a supported zero-tie-return diagnostic at t=.05 yields EV=-.30. This is a synthetic contract example, not an assertion about actual Underdog terms.
6. Joint integer counterexample: book vectors (over,push,under)=(.48,.07,.45),(.46,.05,.49),(.50,.01,.49) must not become three marginal medians totaling 1.02. Integer qualification stays off regardless.
7. Identical .46 strict-win estimates with push masses .03/.16/.18 must show payoff disagreement; do not report full agreement solely from strict-win agreement.
8. Cover over/under, home/away, negative/positive/zero integer spreads, mirror symmetry, monotone/non-monotone adjacent prices, unavailable sides, and mismatched rules/periods.
9. Reject non-finite/invalid odds, monetary inputs, lines, impossible probabilities, and unsupported returns. Assert fees counted once and deterministic rounding.

### Temporal and UI examples

10. References are 110 seconds old when evaluation completes with a 120-second TTL: the live result expires no later than 10 additional seconds, even if the target was just observed.
11. Expire on kickoff, provider suspension, incompatible event revisions, rule/admission change, settings change, loss of freshness, future clock, and sleep/resume gaps. Do not silently renew via a successful UI fetch.
12. Editing a line or fee invalidates the old result; an older asynchronous response cannot attach to the new inputs. Supplemental comparisons for the prior line disappear.
13. Acceptance at t must not use evidence received after t, even if the provider timestamp is earlier. Missing historical evidence means unavailable historical entry EV.
14. A response received one second before kickoff and stored one second after can support close; a response received after kickoff with an earlier provider timestamp cannot. Prove both paths.
15. Closing with large book disagreement cannot be supported; closing with high-quality evidence and negative ROI can be supported. Missing closure can be finalized/revised honestly without inventing quotes.

### Records, sources, and delivery examples

16. Same idempotency key plus equivalent payload creates one intent; conflicting replay fails explicitly. Different keys can represent two intentional equal-term positions.
17. A controlled settlement/closing interleaving preserves both changes and audit history. Corrections survive a stale read, restart, and export.
18. Changed global settings/source data do not change stored original evaluation bytes. Migrating legacy ambiguous records marks provenance unknown rather than fabricating values.
19. ESPN OFF and a malformed Bovada/ESPN outcome preserve valid unrelated markets; invalid normalized lines never crash the whole board. Test actual recorded fixtures when access permits, clearly labeled synthetic fixtures otherwise.
20. Failed refresh preserves ages; fresh empty/closed/suspended results do not resurrect markets; partial success and 403/429 paths have bounded behavior and accurate health labels.
21. Rescheduling preserves canonical event links, journal entries, exposure grouping, and correct cutoff history; ambiguous mappings quarantine.
22. Tests/imports leave a sentinel default user database untouched. Migrations do not reset unknown schema versions. Backup/restore validates SQLite integrity and record/P&L equivalence.
23. API origin/host/mutation controls and CSV/HTML text escaping are tested in production configuration, not only test exceptions.
24. Exercise the complete paper and accepted-record workflow with synthetic data in a real browser: evaluate, edit, expire, record, settle, correct, export, restart, restore a test copy. Verify desktop and narrow screens.
25. Pilot instrumentation counts rejected, disappeared, unavailable, and failed attempts in the correct denominators; repeated snapshots share a decision identity; paper and actual results never mix.

The catalogue defines minimum relevant scenarios, not a target count of test functions. A single parameterized test may cover many scenarios; a passing count alone proves nothing.

## 13. Risk-based verification gate

Use the sequence `intent -> reproduction -> bounded fix -> tests -> independent review -> combined integration verification -> evidence report -> Astra decision`.

- Critical financial/record/temporal/security changes require a fresh Sol reviewer and independent expected-result derivation, targeted unit/property/integration tests, and relevant real browser/database workflows.
- Collection and operational changes require recorded or labeled synthetic fixture coverage, outage behavior, and a bounded live smoke only when permitted.
- Pure cosmetic/documentation changes require appropriate lint/build/render/link checks. Changing labels that convey financial status is not merely cosmetic.

A worker cannot certify its own high-risk patch. A second Sol context reduces shared-history bias but is not a statistically independent model or a correctness guarantee. Review must cite reproducible evidence.

After at most two unsuccessful repair/review cycles for the same unresolved root issue, Astra records the residual defect and changes the approach or escalates the genuine blocker. Never loop indefinitely, weaken the expected behavior, delete failing regression tests, or relabel an untested scenario as a pass. New fixes reopen impacted gates. Final review targets the integrated diff, not only workers' isolated changes.

## 14. Completion and readiness reporting

A final report states the actual commit/worktree, models observed, environment, changed files, test/build/browser commands, results, evidence locations, excluded/unrun checks, blockers, and next permitted action.

Use separate readiness dimensions:

- **Engineering verified:** implemented functionality and relevant tests/build/browser evidence are complete for the tested environment.
- **Windows release ready:** actual Windows setup/start/restart/recovery and UI checks executed successfully. Linux-only results cannot satisfy this label.
- **Manual research ready:** quote entry, clear research/unsupported states, journal, and recovery work even with insufficient live references.
- **Real-quote screen ready:** an actual contract profile and complete eligible evidence path are verified. Otherwise say `REAL_QUOTE_SCREEN_BLOCKED` and name the missing evidence.
- **Pilot instrumented:** protocol, logging, collection controls, and reporting are implemented. This does not mean a multiweek pilot has been completed.
- **Strategy validated:** not established by this build; requires later prospective evidence.

Zero qualifying candidates is compatible with an honest research release. Missing mandatory engineering checks are not. If the environment lacks Windows, browsers, required models, sources, or exact contract evidence, complete nonblocked implementation, preserve failing/untested status, and report the specific limitation without pretending the stronger milestone is complete.

Do not keep the Codex goal alive waiting for future NFL games or invent a four-week dataset. Stop at the declared build completion contract or a documented blocker/budget limit, with durable resumption instructions. [S12]

## 15. Deliverables and execution instructions

### Repository deliverables

- Updated source code and regression tests addressing applicable F1–F10 findings.
- Preserved existing data, explicit schema migrations, immutable historical evidence, concurrency/idempotency safeguards.
- Updated README, compact AGENTS.md, this forward plan, status/decision/verification/source/pilot records.
- Project-scoped Astra/Sol configuration after native runtime verification; no global config replacement.
- Reproducible dependencies and local scripts for setup, start, stop, verify, test-data backup/restore, and pilot reporting. Use existing names/conventions where practical.
- Real-browser evidence and self-contained local HTML readiness report.
- Final completion report distinguishing implemented, executed, blocked, and evidence still unestablished.

### Starting Codex

Place this file at the repository root as `NFL_EDGE_FINAL_PLAN.md`. Keep the supplied review inputs available under `review_inputs/` or another explicit location. The `codex_examples` files are merge templates, not an installer: inspect existing `.codex` config and merge compatible settings without replacing user security, approval, or project policy.

Select Astra for the parent session. Official model documentation identifies `gpt-6-astra` and `gpt-5.6-sol`; local custom agents and `[agents]` defaults support model configuration. Verify the effective settings and an actual child, because a name in text does not choose a model. [S9–S11]

Paste `CODEX_GOAL_PROMPT.txt` into the Astra session. The prompt explicitly requests implementation, so it must not stop after another plan or generic summary. It does not authorize publication, actual betting, production migrations, or future-data fabrication.

## 16. Source record and verification limits

Access date: September 15, 2026. The supplied transcript is retained in the execution pack as `review_inputs/VIDEO_TRANSCRIPT.txt`. External repository docs are mutable; the recorded blob hashes identify the specific retrieved README content where available. These are blob hashes, not commit IDs or claims of a full repository audit.

- **S1 — Supplied video transcript:** https://www.youtube.com/watch?v=MSbacZ99E14 . Full user-provided transcript used. Direct YouTube page retrieval failed; no invented timestamps or independent audiovisual inspection claimed.
- **S2 — Firstmate README:** https://github.com/kunchenguid/firstmate/blob/main/README.md . Targeted sections on architecture, modes, platforms, worktrees, supervision, and skills. The fetched response was truncated after substantial README content; no unseen sections were assumed.
- **S3 — no-mistakes README:** https://github.com/kunchenguid/no-mistakes/blob/main/README.md . Retrieved blob `eb0deffafbb9fcd27806cf4045f78a5ab7deb872`. Its ordinary workflow includes external push and PR creation.
- **S4 — Lavish README:** https://github.com/kunchenguid/lavish-axi/blob/main/README.md . Retrieved blob `c564b081cbd001628a22e6d8f68dab48f3460abb`. Local HTML review concept; no tool installation or functional verification performed here.
- **S5 — Backpass README:** https://github.com/kunchenguid/backpass/blob/main/README.md . Retrieved blob `7579462137c713c75187726b0e5adb73fc218e87`. Evidence-gated proposals and separate apply step.
- **S6 — Treehouse README:** https://github.com/kunchenguid/treehouse/blob/main/README.md . Retrieved blob `8cb37bc4c830b28e5dd9a910683a9ce9cf5fa576`. Worktree pooling concept; no cleanup/install scripts executed.
- **S7 — quota-axi README:** https://github.com/kunchenguid/quota-axi . Retrieved README blob `356cc558d20f39ddbddbb576110f5a380ff5cdcb` for the fetched excerpt; public page also inspected. No credentials accessed by this planning work.
- **S8 — Firstmate Herdr backend documentation:** https://github.com/kunchenguid/firstmate/blob/main/docs/herdr-backend.md . Retrieved blob `97523457071c3769a2cd7c6ba90e91ba8c3b0903`. Session-backend concepts and protocol limits, not an installed backend.
- **S9 — Official model IDs:** https://developers.openai.com/api/docs/models and https://learn.chatgpt.com/docs/models . IDs verified in official documentation; availability in the user's actual workspace must still be checked.
- **S10 — Official subagent configuration:** https://learn.chatgpt.com/docs/agent-configuration/subagents . Custom agent files, model/effort configuration, sandbox inheritance, and concurrency controls. Config schema may evolve; examples must be validated against the installed client.
- **S11 — Official configuration reference:** https://learn.chatgpt.com/docs/config-file/config-reference . Current `[agents]` defaults, concurrency, and model-default compaction. No global configuration modified.
- **S12 — Official Goals guide:** https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex . Goals have measurable completion, constraints, evidence, lifecycle, and budget/blocker stopping conditions.
- **S13 — Official AGENTS.md instructions:** https://learn.chatgpt.com/docs/agent-configuration/agents-md . Durable project instructions; do not substitute imported tools' instructions for the user's authority.
- **S14 — Kalshi public data:** https://docs.kalshi.com/getting_started/quick_start_market_data . Official unauthenticated REST/pagination/orderbook documentation, not measured current NFL coverage or latency.
- **S15 — Pinnacle access:** https://github.com/pinnacleapi/pinnacleapi-documentation . Official public-access restriction statement; no feed approval presumed.
- **S16 — NFL Edge current README and earlier review:** https://github.com/bkaranf/nfl-edge . Retrieved README blob `9c6ea22cde9103538d2da91eff6db70b8c6a3869`, on the returned default branch `codex/initial-review`. Existing evidence remains anchored to the full historical SHA above. Only the README was refreshed for this planning update; this is not a new whole-repository audit.
- **S17 — Underdog profile evidence to obtain:** https://help.underdogsports.com/en/articles/16075547-prediction-picks-football and https://help.underdogsports.com/en/articles/14127510-your-exchange-why-experiences-may-differ . Direct retrieval failed in this update. Treat contract-specific rule inventory as blocked until actual authoritative text or user-provided contract evidence is available; do not infer missing fees or rules.

This plan and configuration examples were authored locally. No NFL Edge source changes, new application tests, actual quotes, live latency measurements, tool installations, model-subagent runtime verification, or betting/account actions were performed to produce them.
