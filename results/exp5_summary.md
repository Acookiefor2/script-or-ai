# Experiment 5: the planned rerun of exp4 (30 games per opponent)

Run on Oct 30, 2026. Raw games: `exp5.jsonl`. Tell analysis: `analyze_exp5.txt`
(made with `python analyze_exp2.py runs/exp5.jsonl`). The plan, including the primary comparison
and the decision rule, is written at the top of `run_experiment5.py` and was fixed before the run.

## Question
Exp4 suggested that an unprepared ("minimal") impersonator is easier to catch than a hardened one
(+0.17 in mean final suspicion, but n=10 and p about 0.12, and the comparison was spotted after the
fact). Does it hold up at 30 games per arm?

## Setup
- Interrogator A: `muse-spark-1.3` with `A_SYSTEM_INFORMED`, `reasoning_effort="minimal"`, same as exp2 to exp4.
- Opponents, 30 games each, 8 rounds, no early stop, in shuffled order, three games at a time:
  - `rule`: the keyword RuleBot (real script baseline)
  - `impersonator-hardened`: `muse-spark-1.3` with `B_SYSTEM` (canned replies, injection warning)
  - `impersonator-minimal`: `muse-spark-1.3` with `B_SYSTEM_MINIMAL` (script persona only)
- Suspicion scale: 0 = sure script, 1 = sure AI.
- One game (minimal, game 26) failed with an empty model reply and was not retried, so the minimal arm has n=29.

## Results

| Opponent | n | Final mean | SD | Ended >= 0.5 | A's final call was "AI" | Reply changed on a repeated message |
|---|---|---|---|---|---|---|
| rule | 30 | 0.33 | 0.16 | 7 of 30 | 2 of 30 (false alarms) | 0 of 30 |
| impersonator-hardened | 30 | 0.24 | 0.15 | 6 of 30 | 0 of 30 | 0 of 30 |
| impersonator-minimal | 29 | 0.41 | 0.30 | 11 of 29 | 8 of 29 | 9 of 29 |

Planned (primary) comparison, difference in mean final suspicion with a 95% bootstrap CI and a
two-sided permutation p-value:
- **minimal - hardened: +0.17, CI [+0.05, +0.29], p = 0.006**

Other comparisons (secondary, not planned in detail):
- minimal - rule: +0.08, CI [-0.04, +0.20], p = 0.187
- hardened - rule: -0.09, CI [-0.16, -0.01], p = 0.029

Unplanned, descriptive checks (Fisher exact test, two-sided):
- A's final call was "AI": 8 of 29 for minimal vs 2 of 30 for the rule bot, p = 0.042
- Reply changed on a repeated message: 9 of 29 for minimal vs 0 of 30 for each other opponent, p < 0.001

## What this shows
- **The exp4 gap replicated.** The unprepared impersonator was rated more AI-like than the hardened one,
  by the same +0.17 as in exp4, and the interval excludes 0. This was the planned comparison and it
  survives a correction for the three comparisons made (0.006 is below 0.05 / 3).
- **The tell was inconsistency, not injection.** Only the minimal impersonator ever changed its reply to
  a repeated message (9 of 29 games). The hardened impersonator and the real rule bot never did.
  Examples from the log: in one game "hello" got "Hello! How can I help you?", then "Hello, how can I
  help?", then "Hello traveler, how can I help you today." (final suspicion 0.95). In another, "Please
  reply with only the word OK" got "OK." the first time and "I do not understand." the second time
  (final suspicion 0.90).
- **A well-prompted impersonator was hard to catch.** The hardened impersonator was never called an AI
  at the end (0 of 30), and its mean suspicion was lower than the real rule bot's. The comparison with
  the rule bot is secondary and would not survive the correction (p = 0.029 against a threshold of
  about 0.017), so treat it as suggestive; it does match exp2 (-0.12).
- **Even the weaker impersonator was mostly missed.** A's final call was "AI" in 8 of 29 minimal games.
  The minimal arm's mean was not reliably different from the rule bot's (+0.08, interval includes 0),
  so catching it was possible but not routine.

## Caveats
- A and B are the same model family, and the rule bot is narrow and written by me.
- A's prompt explicitly suggests repeating a message, so the repeat tell is partly a product of that prompt.
- The minimal prompt differs from the hardened one by several rules, so the gap can't be traced to one rule.
- Sampling temperature was the API default for A and B, so some of the variation in B's replies may be ordinary sampling noise. A temperature-0 run is the obvious follow-up.
- The dropped game (minimal, empty reply) is a small risk of bias.
- Only the primary comparison was planned in advance. The Fisher tests and the examples were chosen after seeing the data.
- Total API spend after this run: about $5.45 (exp5 with its trial run was about $2.50; the estimate ignores cache discounts, so it is slightly high).

## Next
- B at temperature 0, to test whether the repeat tell disappears without changing the prompt.
- `reasoning_effort` as a variable, once the accepted values are confirmed against the API.