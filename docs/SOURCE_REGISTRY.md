# Source admission registry

Registry version: `source-registry-v1-doc-review`, 2026-09-15. This is an admission
inventory, not a completed freshness/access study. No live sportsbook requests
were made during preflight. Supplied-plan source claims remain prior evidence.

States are UNASSESSED, RESEARCH_ONLY, ELIGIBLE, DEGRADED and DISABLED. Eligibility
requires all relevant evidence below and an effective revision/time. Changing
admission invalidates dependent live screens while retaining historical evidence.
Being directly observed, manually entered, or publicly reachable is insufficient.

| ID / origin | Intended use | Starting state | Evidence limits / missing admission gates |
|---|---|---|---|
| ESPN / actual originating sportsbook | Schedule/state and redistributed full-game price research | RESEARCH_ONLY | Underlying book deduplicated; upstream price age, caching, rule semantics and permitted collection not verified in this build |
| Bovada / Bovada | Direct price research | UNASSESSED | Direct HTTP receipt is not upstream freshness proof; access basis, update/cache behavior, suspended states and exact contract equivalence need evidence |
| Kalshi public market REST / Kalshi | Supplemental exchange comparison | RESEARCH_ONLY | Never a sportsbook vote or an Underdog offer; per-contract fees/rules/size and current NFL coverage unknown |
| Manual sportsbook pair / entered originating book | Exact-line corroboration/research | RESEARCH_ONLY | Require genuine capture/observation time, source identity, both-side coherence, explicit rule semantics and availability evidence; a checkbox cannot admit a source |
| Manual target / entered exchange/product | Target economics and accepted journal | UNASSESSED | No verified account-specific contract/profile supplied; exact net returns, fees, rules and receipt/quantity evidence required for stronger claims |

The list of bookmaker names in the UI is an input vocabulary, not proof of legal
access, available coverage, independent price discovery, or admission. Public
endpoint access alone does not establish permission. No credentials, accounts,
scraping bypass, paid feed or external account data is needed for manual research.

## Evidence required for admission

For each origin/distributor retain access basis and link/date, permitted request
limits, exact markets/period/overtime/tie/push/exception rules, parser version,
provider ID mappings, suspended/empty/error behavior, timestamp meanings,
response receipt times, cache headers and measured update limitations. Bound raw
evidence size; retain a content hash and clearly label synthetic fixtures.

Document the admission decision, effective time, actor/evidence and version.
Unknown provider timestamps remain null; local receipt and ingestion cannot be
substituted for price origination time. Two distributors of one originating book
contribute at most one reference, and different books are not asserted independent.

## Runtime contract to implement

On-demand collection uses a shared per-source limiter and cooldown across every
caller. Respect Retry-After, bounded retries and denial circuit breaking. Explicit
fresh empty/suspended/closed responses invalidate old live markets. Transport
failure preserves historical timestamps and marks health degraded; it cannot
freshen cached evidence. Unsupported/unadmitted sources remain useful as labeled
research where their data is coherent, never as a screen vote.

Closing evidence requires genuine local availability before kickoff at quote
level. A pre-kickoff provider timestamp on a post-kickoff response is insufficient.
Backdated manual fields are retrospective evidence unless separately verified
capture provenance establishes actual earlier availability.

## Verification state

Source live smoke: NOT_RUN. Official-document access review: PARTIAL (S03 below).
Freshness/cache
measurement: NOT_RUN. Actual contract profile: NOT_VERIFIED. Parsers currently
have baseline synthetic fixtures; forthcoming regressions and recorded fixtures
must identify their provenance. Real-quote screening remains blocked until these
evidence gates are met. The manual research and recording implementation can
proceed without promoting any source or profile.

## Official-document review, 2026-09-15

No live price endpoints were probed. These are written-document findings, not
operational latency/cache measurements or legal opinions. Network collection stays
DISABLED for all initial policies until its access and evidence gates are reviewed.
Manual research submissions remain available without becoming eligible by checkbox.

- [Underdog football help](https://help.underdogsports.com/en/articles/16075547-prediction-picks-football)
  was available only through an official indexed rendering; direct retrieval returned
  403. It describes overtime and a $0.50-per-team-contract terminal tie, with provider
  exceptions and exceptional completion rules. It does not bind a particular entry
  to exchange, effective profile version, quantity or net fees. Production profile
  admission remains blocked; W/2 is not a valid substitute for explicit net T.
- [Kalshi market-data guide](https://docs.kalshi.com/getting_started/quick_start_market_data)
  describes unauthenticated market data, but the [orderbook reference](https://docs.kalshi.com/api-reference/market/get-market-orderbook)
  currently lists authentication headers as required. [Get Markets](https://docs.kalshi.com/api-reference/market/get-markets)
  documents contract rules and lifecycle/price fields; its update filtering refers
  to non-trading metadata, not proof of price origination. [Rate limits](https://docs.kalshi.com/getting_started/rate_limits)
  describe authenticated token budgets and backoff, leaving the public-call budget
  unresolved. [Fees](https://help.kalshi.com/en/articles/13823805-fees) vary by market.
  Supplemental market-list research may be reviewed later; current NFL coverage,
  exact rules/fees, size, timestamps, caching and access remain unverified.
- [Bovada terms](https://www.bovada.lv/contents/terms_of_service_bvd.pdf), dated
  2024-01-03, contain restrictions on storing content in another retrieval system
  without consent and disclaim data timeliness. No documented collection permission,
  API limits or price/cache timestamps were established. Reachability is insufficient
  for admitting the current collector.
- [ESPN's legal route](https://support.espn.com/hc/en-us/articles/360035445091-Terms-of-Use)
  leads to [Disney terms](https://disneytermsofuse.com/english/), dated 2024-05-24,
  covering ESPN and restricting automated extraction/database creation without
  permission. Editorial sportsbook attribution does not supply JSON endpoint access
  permission or price freshness. A separately authorized access path is needed.

S03 did not admit any source/profile. Preserve exact provider rulebooks, access
evidence and actual entry semantics before a later review. Existing prototype
collector code is not an admission decision. Implementation must enforce the
disabled collection policy; this document alone does not change runtime behavior.
