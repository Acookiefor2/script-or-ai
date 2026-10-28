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

## Models used at runtime
Meta models only, via the Meta Model API (OpenAI-compatible):
- `muse-spark-1.3` for both A and B.

## AI coding tools used to write this code
Claude and Gemini were used as coding assistants. GPT was used as a code reviewer.

## Results so far
All results are small-sample and exploratory. Raw games and summaries are in [`results/`](results/).

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

**Takeaway so far:** with these prompts, Muse Spark as interrogator does not reliably tell a Muse model
impersonating a script from a real script, and impersonating a script is easy for the model.

An earlier exploratory run (exp1) may have been affected by a bug that leaked the `QUESTION:` tag, so
it is not reported here.

## Limitations
- A and B are the same model family.
- The rule bot is narrow and written by me.
- Small n (10 to 15 games per arm).
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
python analyze_exp2.py runs/exp3.jsonl   # checks how often A repeated messages / tried injection
```

Logs go to `runs/` (gitignored). Saved results are in `results/`.

## Built during the event
Updated with each milestone. A live dashboard (suspicion meter, transcript, verdict reveal) is in progress.