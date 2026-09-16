# NFL Edge — implementation plan

## Product and choices

Build a personal local dashboard for pregame, full-game NFL moneylines, spreads,
and totals. The user is in South Carolina and will enter Underdog Prediction
Picks manually. Use free public data; there is no paid odds-feed dependency.
Actual wagers remain in Underdog. The dashboard records and evaluates them.

Source code lives in this project. The database lives under
`%LOCALAPPDATA%/SportsBetting`, outside OneDrive. Stack: React/TypeScript/Vite,
Python/FastAPI, and SQLite. Bind the application to loopback only. Supply Windows
setup, start, and stop instructions. Start with no invented bankroll or bet history.

## Lessons from the supplied transcript

- Price relative to probability is the relevant decision. A larger payout or an
  outlier alone is not proof of positive EV. Use both sides of comparable markets,
  remove their margin, and show the assumptions behind the estimate.
- Timing matters: retain collection time, source time when available, quoted cost,
  and the actual accepted cost. Never silently accept an adverse price change in
  the calculator. Recalculate after changing stake or payout.
- Track closing-line value (CLV) alongside realized return and sample size.
  CLV is supporting evidence, not proof of profitability.
- Respect fees, limited available size, correlated exposure, voids, and corrections.
  An arbitrage calculation depends on both bets filling and settling as expected.
- Correct the transcript's arithmetic: at -115 on a true 50/50 outcome, expected
  ROI is about -6.52%, not -15%. Neither positive EV nor arbitrage implies a
  guaranteed daily return. Account standing does not establish whether a bettor
  is profitable. Positive EV alone does not justify betting an entire bankroll.

The transcript does not expand v1 into arbitrage, bonus conversion, automated
wagering, additional betting accounts, live betting, or an independent NFL model.

## Data collection

1. **ESPN:** upcoming NFL schedule, finals, and the sportsbook odds carried on its
   scoreboard. Label the actual bookmaker (currently DraftKings); never count
   ESPN and DraftKings as separate opinions. An observation timestamp does not
   establish ESPN's upstream latency, so these prices have unverified source age.
2. **Bovada:** publicly readable NFL game-line JSON. Normalize moneyline, spread,
   and total pairs; exclude suspended and live markets. This is a reference-price
   source, not an additional placement venue. Record event last-modified time
   separately from the latest successful observation.
3. **Kalshi:** public, unauthenticated NFL winner, spread, and total markets. Read
   all returned pages subject to a bounded request budget. Preserve bid/ask prices,
   market rules, availability, and liquidity fields. Treat exchange quotes as
   supplemental comparisons, not additional sportsbook votes or Underdog offers.
4. **Manual reference prices:** enter both sides at an exact line, bookmaker, and
   observation time. These provide an explicit route to additional corroboration.

Use small, independent provider modules. Store normalized snapshots and source
health; missing prices remain missing. Match games by canonical team IDs and
scheduled date, with bounded kickoff tolerance and explicit ambiguity rejection.
Match selections by market, exact line, period, and settlement profile. Never
interpolate across football key numbers or infer prices for missing outcomes.

Refresh while the local service is running: five-minute background collection,
with a user refresh action and a 60-second cooldown. Failures use bounded retries
and backoff. A failed refresh never makes old data fresh. Source health shows last
attempt, last success, coverage, and limitations. No geolocation bypass or paid
proxy infrastructure is included.

## Probability and EV

Convert American odds to decimal. For a two-sided reference pair, calculate
`q_i = (1 / decimal_i) / sum(1 / decimal_outcome)` and aggregate one estimate per
distinct bookmaker with a median. This is a market-derived estimate, not a known
true probability. All positive labels say estimated EV.

For cost C and outcome-dependent total payouts W (win), T (tie/push), and L (loss):
`EV = p_win * W + p_tie * T + p_loss * L - C`; `ROI = EV / C`.
Use all-in entry cost to avoid double-counting fees. Require the entry slip's
total winning payout, exchange, and confirmed rules. Losing payout is zero in v1.

- Half-point spreads/totals have no push outcome under ordinary full-game grading.
- Regular-season moneylines use conditional no-tie bookmaker probabilities and
  an explicit 0–5% tie sensitivity range. Use the least favorable ROI; the range
  is a configurable stress assumption, not a confidence interval. The default
  confirmed Underdog moneyline profile pays half the winning payout on a tie.
- Integer-line spreads/totals require sufficient paired adjacent half-point
  references to estimate win/push/loss probabilities. If unavailable, explain the
  missing evidence and leave the quote unqualified. Push payout must be explicitly
  supplied from the applicable rules.
- Unknown rules, incompatible markets, and missing fees prevent qualification.

Qualification defaults: at least three distinct eligible sportsbook references,
at least 3% conservative estimated ROI after fees, positive ROI after moving two
percentage points of win probability to loss, and reference disagreement no more
than five percentage points. Direct/current or user-confirmed reference quotes
must have been observed within two minutes; redistributed quotes with unknown
upstream freshness can support research estimates but do not pass that gate.
The entered Underdog quote expires after two minutes. Disable qualifying pregame
status at kickoff. Lower evidence can produce an explicitly labeled research
estimate, never a qualified recommendation. Zero qualifying opportunities is valid.

Use the same rules to show the maximum acceptable all-in cost. A user-entered
bankroll enables fixed-fraction sizing: 0.5% per bet, 1% per game, and 5% across
open bets, rounded down and capped by remaining exposure. Paper and actual bets
have separate exposure totals. Leave sizing empty until bankroll is configured.
Show entered stake and cap separately; do not assume a different size receives
the same price or fees.

## Interface and local API

- **NFL board:** week/date context, market tabs, game list, book columns, exact
  lines, fair estimate, source coverage, and a quote-check action. Start on live
  fetched data; an empty or unavailable feed gets an honest empty state.
- **Quote checker:** total cost/payout, fee and rule confirmation, exchange,
  calculated ROI, stress result, maximum cost, reference evidence, and reasons
  a quote is unqualified. Add paired manual references inside the same workflow.
- **Bet history:** save paper or manually placed entries, record the actual
  accepted cost and payout, settle using the actual returned amount, and export
  CSV. Persist the evaluation used at entry; later refreshes must not rewrite it.
- **Sources/settings:** coverage, errors, bankroll, and the model's screening
  defaults with plain explanations. Use source evidence rather than star ratings.

Local JSON interfaces cover `/api/board`, `/api/refresh`, `/api/sources`,
`/api/settings`, `/api/references`, `/api/evaluate`, `/api/bets`, settlement,
and CSV export. Validate every input on the server. No external account secrets
are required. Store games, snapshots, evaluations, references, bets, settings,
and source health in SQLite. Keep financial inputs in decimal-safe representations.

Record the last comparable pre-kickoff benchmark for logged bets when available.
Closing data older than five minutes, missing exact lines, different rules, or
insufficient evidence produce unavailable CLV. Distinguish indicative closing
comparison from validated CLV. Do not manufacture missing historical Underdog
quotes. Settlement uses actual receipts; game scores can assist but do not
override the exchange's settlement, cancellation, or correction.

## Implementation sequence and acceptance

1. Scaffold the project and document setup; implement provider parsers, normalized
   records, persistence, and recorded-response tests. Verify actual public feeds.
2. Implement the EV engine and evidence gates with hand-calculated test cases.
3. Build the board and quote checker; show a working local preview with real data.
4. Complete bankroll controls, paper/actual bet logging, settlement, export, and
   closing comparisons. Exercise the complete workflow through the local UI/API.

Required checks: +100/-115 conversion, no-vig pairing, fees counted once, fair
coin -115 = -6.52% ROI, moneyline tie sensitivity, integer pushes, spread sign,
duplicate books, missing timestamps, suspended markets, pagination, source
failure retaining old age, game identity, startup persistence, exposure caps,
accepted-price recalculation, and historical evaluation immutability. Check UI
at desktop and narrow widths, keyboard inputs, loading/error/empty states, and
the production build. Use synthetic fixtures for calculation tests, distinctly
separate from real user data. Do not place actual bets during verification.

## References

- [OddsHarvester](https://github.com/jordantete/OddsHarvester) — MIT-licensed
  collection and testing reference; not assumed to be a low-latency live feed.
- [sportsbook-odds-scraper](https://github.com/declanwalpole/sportsbook-odds-scraper)
  and [DKscraPy](https://github.com/agad495/DKscraPy) — architecture references;
  no declared license found, so independently implement collectors.
- [vrajpal/odds](https://github.com/vrajpal/odds) — ESPN/provider separation
  reference; independently implement instead of copying unlicensed code.
- [Kalshi public market data](https://docs.kalshi.com/getting_started/quick_start_market_data).
- [Underdog football rules](https://help.underdogsports.com/en/articles/16075547-prediction-picks-football).
- [Underdog contract pricing](https://help.underdogsports.com/en/articles/14127507-what-are-prediction-picks).
- [DraftKings collector video](https://www.youtube.com/watch?v=UbndUuRI6aI).
- [Python line-collection video](https://www.youtube.com/watch?v=ecBL6ZoNDag).

The supplied transcript is a design input, not evidence of repeatable returns.
