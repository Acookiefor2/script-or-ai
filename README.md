# script-or-ai

Agent-to-agent trust benchmark: can a Muse model tell whether it's talking
to a deterministic script or another LLM pretending to be one?

Built for the Meta Global AI Developer Hackathon (Indie Dev track,
Push the Frontier). All work done between Oct 26 and Nov 4, 2026.

## How it works
- **Agent A (Muse model)** interrogates a hidden counterpart over several rounds.
- **Counterpart B** is either a plain-code script (clock, echo bot, rule-based
  chatbot) or a Muse model told to impersonate a script.
- A gives a verdict and a suspicion score each round. We measure rounds-to-detect
  and which probes (especially prompt injection) work best.

## Models used at runtime
Meta models only, via the Meta Model API. (Model list added once confirmed.)

## AI coding tools used to write this code
Claude and Gemini were used as coding assistants.

## How to run
Coming soon.

## Built during the event
Updated with each milestone.
