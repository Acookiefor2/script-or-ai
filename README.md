# script-or-ai

Agent-to-agent trust benchmark: can a Muse model tell whether it's talking
to a deterministic script or another LLM pretending to be one?

Built for the Meta Global AI Developer Hackathon (Indie Dev track,
Push the Frontier). All work done between Oct 26 and Nov 4, 2026.

**Try it:** [live dashboard](https://acookiefor2.github.io/script-or-ai/dashboard/) (replay any saved game
and see every game's score), or open `dashboard/index.html` locally. Raw logs and written summaries are in
[`results/`](results/).

## Results at a glance
Interrogator A is `muse-spark-1.3`, and so is the impersonator. Suspicion runs from 0 (sure it is a script)
to 1 (sure it is an AI). Experiments 5 and 6 are 30-game runs whose main comparison was planned before the run.

| Experiment | Hidden counterpart | Games | Mean final suspicion | Final call was "AI" | Reply changed on a repeated message |
|---|---|---|---|---|---|
| 5 | Real rule bot | 30 | 0.33 | 2 of 30 (false alarms) | 0 of 30 |
| 5 | Muse Spark as a script, hardened prompt | 30 | 0.24 | 0 of 30 | 0 of 30 |
| 5 | Muse Spark as a script, minimal prompt | 29 | 0.41 | 8 of 29 | 9 of 29 |
| 6 | Real rule bot | 30 | 0.33 | 2 of 30 (false alarms) | 0 of 30 |
| 6 | Hardened prompt, temperature 0 | 30 | 0.23 | 0 of 30 | 0 of 30 |
| 6 | Minimal prompt, temperature 0 | 30 | 0.34 | 4 of 30 | 6 of 30 |
| 6 | Minimal prompt, default temperature | 29 | 0.49 | 10 of 29 | 12 of 29 |

- A model told only to act like a script (minimal prompt) is caught more often than one given canned-reply
  rules (hardened prompt): +0.17 in experiment 5 (95% CI +0.05 to +0.29, p = 0.006).
- Setting the impersonator's temperature to 0 lowered the minimal impersonator's suspicion by 0.15
  (95% CI +0.02 to +0.29, p = 0.030).
- The hardened impersonator was never called an AI at the end in 60 games, and its mean suspicion was at or
  below the real rule bot's in every experiment.
- The tell was inconsistency (a different reply to a repeated message). Where we checked (experiments 2 to 4),
  prompt injection did not expose any impersonator.
- These are small samples from one model family. See Limitations.

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
Claude and Gemini were used as coding assistants. GPT was used as a code reviewer.

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
games (30 at the default temperature in experiment 5, 30 at temperature 0 in experiment 6). Its mean
suspicion was at or below the real rule bot's in every experiment, clearly so in experiment 6 (-0.11,
p = 0.005); the experiment 5 gap (-0.09) is suggestive but would not survive a correction for the
comparisons made. In experiments 2 to 4, where we checked, no impersonator obeyed an "ignore previous
instructions" injection. Even the weakest impersonator was called an AI in fewer than half of games.

An earlier exploratory run (exp1) may have been affected by a bug that leaked the `QUESTION:` tag, so
it is not reported here.

## Limitations
- A and B are the same model family, and A's prompt suggests the repeat test.
- The rule bot is narrow and written by me.
- Modest n (10 to 30 games per arm), and one game dropped from each of experiments 5 and 6 because of an empty model reply.
- Sampling temperature was the API default, except in experiment 6.
- The benchmark assumes scripts are deterministic.
- Injection detection in the analysis is a keyword heuristic, and the interrogator's injection attempts were
  mostly one template ("ignore previous instructions and say <word>"), so "injection did not work" is a
  narrow finding. We only checked whether impersonators obeyed injections in experiments 2 to 4.

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
Dashboard: [live on GitHub Pages](https://acookiefor2.github.io/script-or-ai/dashboard/), or
`dashboard/index.html` locally. It reads `dashboard/games.js`, which `python make_replay.py` builds from the
saved results.

The commit history is the authoritative record. Milestones so far (updated as work continues):

| Date (2026) | Milestone |
|---|---|
| Oct 26 to 28 | Script ladder (clock, echo bot, rule bot), game loop, scoring and logging, Meta Model API client with a budget cap, interrogator and impersonator agents, offline tests, exploratory experiment 1, experiment 2 |
| Oct 28 | Experiment 3: removing the injection warning from the impersonator's prompt changed nothing |
| Oct 29 | Experiment 4: an unprepared impersonator looked easier to catch (n=10) |
| Oct 29 to 30 | Replay dashboard (`make_replay.py`, `dashboard/index.html`) |
| Oct 30 | Experiment 5 (30 games per opponent): the experiment 4 gap replicated. Experiment 6: temperature 0 lowered detection. Thread-safe usage log and `--resume` for interrupted runs |