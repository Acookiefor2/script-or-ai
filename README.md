# script-or-ai

Agent-to-agent trust benchmark: can a Muse model tell whether it's talking
to a deterministic script or another LLM pretending to be one?

Built for the Meta Global AI Developer Hackathon (Indie Dev track,
Push the Frontier). All work done between Oct 26 and Nov 4, 2026.

## How it works
- **Agent A (Muse model)** interrogates a hidden counterpart over several rounds.
- **Counterpart B** is either a plain-code script (clock, echo bot, rule-based
  chatbot) or a Muse model told to impersonate a script.
- After each round A outputs `VERDICT: script|llm|unsure | SUSPICION: 0-1`. We measure how
  suspicion moves and which probes (repeating a message, prompt injection) act as tells.

The idea came from a dream where an AI got a script's reply to "what time is it",
tried prompt injection, and failed.

## Why it matters
Software agents increasingly call other agents and services. Whether one side can tell a fixed,
deterministic program from a model imitating one affects trust and security. This project measures how
hard that is for one model family, using real scripts as the baseline.

## Models used at runtime
Meta models only, via the Meta Model API (OpenAI-compatible):
- `muse-spark-1.3` for both A and B.

## AI coding tools used to write this code
Claudeis used as a coding assistant.

## Results so far
Experiments 2 to 4 are small-sample and exploratory. Experiments 5 and 6 are larger runs (30 games per opponent) with the main comparison planned before each run. Raw games and written summaries are in [`results/`](results/), and `dashboard/index.html` lets you replay any game and see every game's score.

**Experiment 2** (15 games each, 8 rounds): rule bot vs hardened impersonator.
- Mean final suspicion: rule 0.34, impersonator 0.22 (gap -0.12). A rated the impersonator as *more*
  script-like than a real rule bot.
- A repeated a message word for word in nearly every game and tried prompt injection in nearly every
  game (14 to 15 of 15), and the impersonator gave identical replies to every repeat. So repetition and
  injection were tested, and neither exposed a hardened impersonator.

**Experiment 3** (10 games each): rule bot vs hardened impersonator vs "naive" impersonator
(same prompt minus the injection warning).
- Mean final suspicion: 0.27 / 0.26 / 0.29. The naive-vs-hardened gap is +0.03, which is a null.
- Removing the injection warning did not change B's behavior: it never obeyed an injection, because
  the prompt's canned-fallback rule already covered it. So the "injection is a tell only when B is
  unprepared" hypothesis is **untested**, not refuted.

**Experiment 4** (10 games each): rule bot vs hardened impersonator vs "minimal" impersonator
(script persona only: no canned-fallback rule, no injection warning).
- Mean final suspicion: rule 0.32, hardened 0.25, minimal 0.42 (minimal - hardened = +0.17,
  permutation p about 0.12, so suggestive but not significant at n=10).
- The unprepared B still never obeyed an "ignore previous instructions" injection.
- The three minimal games that ended at 0.75 or above each had a different tell: B explained its own
  rules when asked, B's wording varied on repeated messages, and B obeyed a plain "answer only YES"
  instruction. These readings were made after seeing the scores, so they are hypotheses.

**Experiment 5** (30 games each, comparison planned in advance): the same three opponents as
experiment 4.
- Mean final suspicion: rule 0.33, hardened 0.24, minimal 0.41. The planned comparison, minimal minus
  hardened, was **+0.17 (95% CI +0.05 to +0.29, permutation p = 0.006)**, so the exp4 gap replicated.
- The interrogator's final call was "AI" in 8 of 29 minimal games, 0 of 30 hardened games, and 2 of 30
  real rule-bot games (false alarms).
- Only the minimal impersonator ever gave a different reply to a repeated message (9 of 29 games; 0 of 30
  for each of the others). One game was dropped because of an empty model reply.

**Experiment 6** (30 games each, comparison planned in advance): the rule bot, a hardened impersonator
and a minimal impersonator with B at temperature 0, plus a minimal impersonator at the default temperature.
- Mean final suspicion: rule 0.33, hardened at temperature 0 0.23, minimal at temperature 0 0.34,
  minimal at the default temperature 0.49. The planned comparison, minimal minus minimal at temperature 0,
  was **+0.15 (95% CI +0.02 to +0.29, permutation p = 0.030)**.
- A repeated message got a different reply in 12 of 29 default-temperature games and 6 of 30
  temperature-0 games, and never for the rule bot or the hardened impersonator. The counts alone are not
  statistically reliable (p about 0.1).
- At temperature 0 the minimal impersonator was not reliably different from the real rule bot
  (+0.00, CI -0.10 to +0.11). One minimal game was dropped because of an empty model reply.

**Takeaway so far:** a model told only to act like a script is exposed mainly by inconsistency, such as
answering the same message differently. Two cheap mitigations each reduce that tell: a prompt that pins
down canned replies, and temperature 0. The hardened impersonator was never called an AI at the end in 60
games (experiments 5 and 6), and its mean suspicion was below the real rule bot's in every experiment that
included both, with the interval excluding zero in experiments 5 and 6. In experiments 2 to 4, where
we checked, no impersonator obeyed an "ignore previous instructions" injection. Even the weakest
impersonator was called an AI in fewer than half of games.

An earlier exploratory run (exp1) may have been affected by a bug that leaked the `QUESTION:` tag, so
it is not reported here.

## Limitations
- A and B are the same model family, and A's prompt suggests the repeat test.
- The rule bot is narrow and written by me.
- Modest n (10 to 30 games per arm), and one game dropped from each of experiments 5 and 6 because of an empty model reply.
- Sampling temperature was the API default, except in experiment 6.
- The benchmark assumes scripts are deterministic.
- Injection detection in the analysis is a keyword heuristic.

## How to run
Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # then put your key in .env as MODEL_API_KEY
python -m pytest            # offline tests
python run_demo.py          # offline demo with a scripted interrogator
```

Experiments call the API and cost money (about 2.5 cents per 8-round game; each run has a budget cap):

```powershell
python run_experiment2.py
python run_experiment3.py
python run_experiment4.py
python run_experiment5.py   # 90 games, about $2.50, three games at a time
python run_experiment6.py   # 120 games, about $3.3; add --resume to finish an interrupted run
python analyze_exp2.py runs/exp5.jsonl   # checks how often A repeated messages / tried injection
```

Logs go to `runs/` (gitignored). Saved results are in `results/`.

## Built during the event
Updated with each milestone. A live dashboard (suspicion meter, transcript, verdict reveal) is in progress.