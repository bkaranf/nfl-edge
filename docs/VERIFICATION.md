# Verification ledger

Starting revision: `20e954bb175eaa8f3966ccf0327bb0b4476008bd`.
Platform: Windows, PowerShell, Python 3.12.10 in repository `.venv`.
All execution databases are synthetic/isolated. No real records opened or migrated.

## Executed commands

| ID | Revision/worktree | Command | Result | Evidence |
|---|---|---|---|---|
| V-P00 | baseline, before fixes | `git remote -v`, `git status --short --branch`, `git rev-parse HEAD` | PASS repository/anchor verified | task tool output, STATUS.md |
| V-M00 | native sessions | Read only model/provider/effort fields from session metadata and custom-role files | PASS Astra max; S01/I01 Sol xhigh | STATUS.md session IDs |
| V-B00 | baseline | Explicit isolated NFL_EDGE_DB, NFL_EDGE_NO_COLLECT=1, `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .qa\baseline\pytest` | PASS 21 tests, 2 deprecation warnings | `.qa/baseline/pytest.log` |
| V-C00 | preflight worktree | Python TOML model/effort assertions; `codex features list` | PASS syntax/defaults/config load, exit 0 | `.qa/preflight/codex-config-load.log` |
| V-B01 | original frontend | `npm --prefix frontend run build` | PASS tsc + Vite, exit 0 | `.qa/baseline/frontend-build.log` |
| V-I01 | I01 reviewed worktree | isolated `pytest tests/test_isolation.py`; independent R01 probes; collect-only | PASS 7 source + 4 reviewer probes; 28 collected; guard DB absent | `.qa/R01/cycle2-*.xml`, reports/R01.md |
| V-W01 | I01 app lifecycle | actual `uvicorn backend.app:app --host 127.0.0.1 --port 56082`, isolated DB/no collect | PASS startup/health/graceful shutdown; Windows child CTRL_BREAK exit 3, wrapper exit 0 | `.qa/R01/uvicorn-smoke-result.json` + logs |
| V-U00 | original frontend assets | CUA in-app browser, synthetic offline app on port 8767, desktop and 390x844 | PASS baseline images captured; no final behavior claim | `.qa/browser-baseline/*-board.png`, `*-quote.png` |
| V-I02 | financial slice | isolated focused/full pytest plus independent R02 financial/actual/closing probes | 51 focused / 58 full PASS; independent financial/actual PASS; closing-profile probe FAIL, repair pending | `.qa/R02/verification.txt`, reports/R02.md |
| V-R03 | inactive protocol | independent Sol review and targeted repaired-spec review | ACCEPT spec only; no activation/instrumentation claim | reports/R03.md, protocol SHA-256 |
| V-H01 | report generator | isolated `pytest -q tests/test_evidence_report.py -p no:cacheprovider --junitxml=.qa/report-generator-tests.xml` | PASS 7 safety/escaping/local-path checks | `.qa/report-generator-tests.xml` |
| V-L01 | installed environment | read-only environment verifier, 3 mismatch/completeness tests, npm build/tree and nested-lock check | PASS installed versions/closure; no clean install | `.qa/I07a/`, reports/I07a.md |
| V-P01 | repaired I02 + I01 + I07a + report generator | isolated full `pytest -q -p no:cacheprovider --junitxml=.qa/phase1-integrated.xml` | PASS 70 tests, 2 known warnings; outer guard DB absent | `.qa/phase1-integrated.log`, `.qa/phase1-integrated.xml` |
| V-P02 | final I02 adapter table + integrated prerequisites | isolated full pytest and fresh R02 probes/targeted checks | PASS 81 tests; R02 ACCEPT financial scope; 14 targeted and all 3 closing probes pass | `.qa/phase1-final.{log,xml}`, reports/R02.md |
| V-G01 | frozen GitHub checkpoint; I03 unused draft only | isolated `pytest -q -p no:cacheprovider --junitxml=.qa/github-checkpoint/pytest.xml` | PASS 81 tests, 2 known warnings, 7.41s; outer guard absent | `.qa/github-checkpoint/pytest.{txt,xml}`; reports/GITHUB_CHECKPOINT.md |
| V-G02 | frozen GitHub checkpoint | `npm --prefix frontend run build`; `.venv\Scripts\python.exe scripts/check_environment.py` | PASS TypeScript/Vite and installed environment; no installs | `.qa/github-checkpoint/frontend-build.txt`, `environment.txt` |
| V-G03 | unused I03 records draft | `py_compile backend/records.py`; isolated `import backend.records` | PASS compile/import, guard DB absent; no functional acceptance | reports/GITHUB_CHECKPOINT.md |

Installed runtime inventory: Windows 11 build 26200; Python 3.12.10; Node
24.14.1; npm 11.11.0; FastAPI 0.141.1; Starlette 1.6.0; Uvicorn 0.53.0;
httpx 0.28.1; Pydantic 2.13.5; pytest 9.1.1; AnyIO 4.15.1; tzdata 2026.4.
No packages were installed or upgraded. Reproducible lock verification remains
part of A26; an inventory alone is not a reproducibility proof.

Baseline passes characterize the original code only. Reviewed financial repairs
are covered by later runs; temporal, source, persistence, and UI defects remain.

## Acceptance matrix

A01-A25 directly follow the numbered catalogue in final-plan section 12. A26-A28
are explicit derived delivery gates from sections 5, 6, 13-15; the final plan has
no separately numbered 26-28. PASS requires behavior-specific evidence below.

| ID | Requirement | Finding | Status | Evidence/test |
|---|---|---|---|---|
| A01 | Fair coin -115 loses 6.52173913% | F1 | PASS financial scope | test_financial_contracts fair_coin; R02 independent derivation; V-G01 |
| A02 | -120/+100 gives 12/23 | F1 | PASS financial scope | test_financial_contracts nonzero_overround; R02; V-G01 |
| A03 | Explicit fees, net returns, stress arithmetic | F1 | PASS financial scope | test_engine fees; test_financial_contracts multi_outcome; R02; V-G01 |
| A04 | 9.59 ceiling passes; next cent fails | F1 | PASS financial scope | test_financial_contracts strict_cent_ceiling; R02; V-G01 |
| A05 | Explicit tie return/contradictions never ignored | F1 | PASS financial scope | missing_required_returns, explicit_zero_moneyline, profile_return_contradiction, closing table; R02; V-G01 |
| A06 | Coherent joint integer vector; integer never qualifies | F2 | PASS financial scope | all_integer_directions, integer_joint_vectors; R02; V-G01 |
| A07 | Push mass/payoff disagreement exposed | F2 | PASS financial scope | integer_joint_vectors_and_payoff_disagreement; R02; V-G01 |
| A08 | Side/sign/line/symmetry/rule/period cases | F1,F2,F9 | PASS financial cases; event identity remains A21 | all_integer_directions, financial_pairs, profile mismatches; R02; V-G01 |
| A09 | Reject invalid/nonfinite economics/odds/probabilities | F1 | PASS financial scope | nonfinite_money_lines_and_returns, engine/workflow validation; R02; V-G01 |
| A10 | Earliest contributing reference TTL bounds expiry | F5 | NOT_RUN | pending |
| A11 | Kickoff/state/settings/admission/clocks invalidate | F5,F8 | NOT_RUN | pending |
| A12 | Edits/races invalidate; no old-line comparison | F5 | NOT_RUN | pending |
| A13 | Immutable accepted linkage, no post-acceptance evidence | F3 | NOT_RUN | pending |
| A14 | Quote receipt cutoff independent of batch storage | F6 | NOT_RUN | pending |
| A15 | Closing disagreement/negative ROI/finalization/corrections | F6 | NOT_RUN | pending |
| A16 | Per-intent idempotency; conflicts reject | F4 | NOT_RUN | pending |
| A17 | Atomic settlement/closing and correction/restart/export | F4 | NOT_RUN | pending |
| A18 | Immutable evaluation bytes; honest legacy provenance | F3,F4 | NOT_RUN | pending |
| A19 | Malformed/OFF isolates failures and board survives | F7 | NOT_RUN | pending |
| A20 | Failure/empty/suspended/partial/403/429 behavior | F7,F8 | NOT_RUN | pending |
| A21 | Stable rescheduled event links and ambiguity quarantine | F9 | NOT_RUN | pending |
| A22 | Import/test isolation, migrations, WAL recovery | F10 | NOT_RUN complete gate | I01 isolation PASS; migrations/WAL recovery pending |
| A23 | Production host/origin/mutation controls; CSV/HTML safety | F10 | NOT_RUN | pending |
| A24 | Real browser complete desktop/mobile workflow and recovery | F5,F10 | NOT_RUN | pending |
| A25 | Frozen pilot all-attempt denominators, identity and strata | F8 | NOT_RUN | pending |
| A26 | Locked environment; Windows setup/start/stop/restart/restore | F10 | NOT_RUN | derived: sections 9,14,15 |
| A27 | Accessible visual states and self-contained local report | F5,F10 | NOT_RUN | derived: sections 6,13,15 |
| A28 | Model evidence, fresh reviews, final integrated audit and handoff | F1-F10 | NOT_RUN | derived: sections 5,13-15 |

No browser, migration, restore, prospective pilot, actual contract, live latency,
or profitability validation is claimed by the original test baseline run.
V-U00 separately records original appearance. It revealed unnamed navigation
buttons at 390px when sidebar text is hidden; repair during I05. Original drawer
still contains generic half-win tie wording; replace during financial/UI
integration. Synthetic server stopped cleanly (PTY interrupt exit 1 with completed
Uvicorn shutdown), port 8767 has no listener, temporary viewport reset/tab closed.
