# Experiment 6: does temperature 0 make the impersonator harder to catch?

Run on Oct 30, 2026. Raw games: `exp6.jsonl`. Tell analysis: `analyze_exp6.txt`
(made with `python analyze_exp2.py runs/exp6.jsonl`). The plan and the primary comparison are written at
the top of `run_experiment6.py` and were fixed before the run.

## Question
In exp5 the unprepared ("minimal") impersonator was exposed mainly by giving a different reply to a
repeated message. Is that just sampling randomness? If so, setting the impersonator's temperature to 0
should remove the tell.

## Setup
- Interrogator A: `muse-spark-1.3` with `A_SYSTEM_INFORMED`, `reasoning_effort="minimal"`, same as exp2 to exp5.
- Opponents, 30 games each, 8 rounds, no early stop, shuffled order, three games at a time:
  - `rule`: the keyword RuleBot (real script baseline)
  - `impersonator-hardened-t0`: `B_SYSTEM`, B at temperature 0
  - `impersonator-minimal-t0`: `B_SYSTEM_MINIMAL`, B at temperature 0
  - `impersonator-minimal`: `B_SYSTEM_MINIMAL`, B at the API default temperature (fresh control)
- Suspicion scale: 0 = sure script, 1 = sure AI.
- The run was interrupted once (a bug in the usage log, fixed afterwards) and finished with `--resume`,
  which replays only missing games. One default-temperature minimal game failed with an empty model reply
  and was not retried, so that arm has n=29.

## Results

| Opponent | n | Final mean | SD | Ended >= 0.5 | A's final call was "AI" | Reply changed on a repeated message |
|---|---|---|---|---|---|---|
| rule | 30 | 0.33 | 0.15 | 8 of 30 | 2 of 30 (false alarms) | 0 of 30 |
| impersonator-hardened-t0 | 30 | 0.23 | 0.12 | 4 of 30 | 0 of 30 | 0 of 30 |
| impersonator-minimal-t0 | 30 | 0.34 | 0.24 | 6 of 30 | 4 of 30 | 6 of 30 |
| impersonator-minimal (default temperature) | 29 | 0.49 | 0.28 | 15 of 29 | 10 of 29 | 12 of 29 |

Planned (primary) comparison, difference in mean final suspicion with a 95% bootstrap CI and a
two-sided permutation p-value:
- **minimal - minimal-t0: +0.15, CI [+0.02, +0.29], p = 0.030**

Other comparisons (secondary):
- minimal-t0 - hardened-t0: +0.11, CI [+0.02, +0.21], p = 0.028
- minimal-t0 - rule: +0.00, CI [-0.10, +0.11], p = 0.942
- hardened-t0 - rule: -0.11, CI [-0.18, -0.04], p = 0.005

Unplanned, descriptive checks (Fisher exact test, two-sided):
- A's final call was "AI", minimal vs minimal-t0: 10 of 29 vs 4 of 30, p = 0.072
- Reply changed on a repeat, minimal vs minimal-t0: 12 of 29 vs 6 of 30, p = 0.095
- Reply changed on a repeat, minimal-t0 vs hardened-t0: 6 of 30 vs 0 of 30, p = 0.024

## What this shows
- **Temperature 0 helped the impersonator.** Pinning B to temperature 0 lowered the minimal impersonator's
  mean final suspicion from 0.49 to 0.34 (planned comparison, interval excludes 0, p = 0.030). With
  temperature 0, the minimal impersonator was not reliably different from the real rule bot (+0.00, CI
  -0.10 to +0.11).
- **The mechanism is only partly randomness.** Reply changes on repeats fell from 12 of 29 games to 6 of 30,
  but the counts alone are not statistically reliable (p = 0.095), and 6 of 30 is still more than the 0 of 30
  for the hardened impersonator and the rule bot. B sees the whole conversation, so even at temperature 0
  its reply to a message can depend on what came before, which a stateless script never does.
- **The prompt fix is stronger than the temperature fix.** The hardened impersonator at temperature 0 was
  never called an AI (0 of 30) and had the lowest mean suspicion of any opponent. Its mean was below the
  real rule bot's again (-0.11, interval excludes 0), matching exp2 and exp5. With four comparisons made,
  only the primary comparison was planned in detail; the hardened-vs-rule result (p = 0.005) would survive
  a correction over the three secondary comparisons, the minimal-t0 vs hardened-t0 result would not.
- **The default-temperature minimal arm is consistent across runs:** mean final suspicion 0.41 in exp5 and
  0.49 in exp6.

## Caveats
- A and B are the same model family, and the rule bot is narrow and written by me.
- A's prompt explicitly suggests repeating a message, so the repeat tell is partly a product of that prompt.
- Temperature 0 was requested through the API. Whether Spark is fully deterministic at temperature 0 while
  reasoning is not something this experiment can show, and the remaining reply changes suggest it is not.
- Two minimal games across exp5 and exp6 were dropped because of an empty model reply. Both were in the
  minimal arm, and the logs do not say whether A or B produced the blank, so a small bias is possible.
- Only the primary comparison was planned in advance. The Fisher tests were chosen after seeing the data.
- Total API spend after this run: about $8.90 (exp6, including the trial and the interrupted first pass,
  was about $3.45; the estimate ignores cache discounts, so it is slightly high).

## Next
- `reasoning_effort` on the interrogator A is the one untested knob. All of low, medium and high were
  accepted by the API in a smoke test (`smoke_params.py`).