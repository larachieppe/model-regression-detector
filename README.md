# Model Regression Detector

CI/CD for LLM prompt changes. Runs a golden dataset against a versioned prompt
config, scores the outputs on multiple dimensions, diffs the run against the
last baseline, and (once wired up) blocks merges and pages Slack when the
diff crosses a regression threshold.

The feature under test right now is a customer support email classifier:
given raw email text, return a `category` (billing / technical / account /
general) and a one-sentence `summary`.

## Status

Phase 1 only — the feature under test and its typed interface exist and are
tested offline. Nothing here calls a real LLM yet; nothing evaluates or
alerts yet. See Roadmap below for what's next and in what order.

## Layout

```
prompts/            versioned prompt YAML — this is the "code" under test
src/schemas.py       Pydantic contract: PromptConfig, LLMClassification, ClassificationOutput
src/prompt_loader.py loads prompts/<version>.yaml into a PromptConfig
src/classifier.py    classify_email(email_text, prompt_config, client=None)
tests/               offline tests using a fake ChatClient (no network, no API key needed)
data/golden_dataset/ empty — Phase 2 populates this with hand-labeled test cases
reports/             generated HTML diff reports land here (Phase 4, gitignored)
```

## Setup

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in OPENAI_API_KEY when you're ready to hit the real API
pytest -q
```

The test suite runs fully offline via a `FakeChatClient` injected into
`classify_email(..., client=fake)`. You do not need an API key to run
`pytest`. You do need one to actually classify a real email — `classify_email`
raises a clear `RuntimeError` if `OPENAI_API_KEY` is unset and no client was
passed in.

## The interface contract

`src/schemas.py` defines the boundary between "the feature" and "the eval
pipeline that will be built around it":

- `PromptConfig` — everything that makes a prompt version reproducible:
  version id, timestamp, model, temperature, system prompt, few-shot examples.
  This is what gets diffed run-over-run.
- `LLMClassification` — the exact shape requested from the model via
  structured outputs (`category`, `summary`). Nothing else, because this
  schema is sent to OpenAI as a JSON schema and extra fields would just be
  noise the model has to reason about.
- `ClassificationOutput` — `LLMClassification` plus run metadata (latency,
  token counts, which prompt version and model produced it). This is the
  shape the eval engine will actually score and log.

Splitting these two was deliberate: the eval engine needs latency/tokens per
case, but the model should never be asked to produce them.

## Adding a new prompt version

Copy `prompts/classifier_v1.yaml` to `prompts/classifier_v2.yaml`, bump
`version`, edit the system prompt / few-shot examples, and load it with
`load_prompt_config("v2")`. Nothing else needs to change — the eval pipeline
(once built) will consume any `PromptConfig` the same way.

## Roadmap

- **Phase 2 — golden dataset.** 50-100 hand-labeled emails in
  `data/golden_dataset/`, each with a stable id, expected category, ideal
  summary, and a `difficulty` tag for edge cases (ambiguous, short, typos,
  mixed language, sarcastic). No LLM-generated ground truth — the whole
  point is a human-verified bar.
- **Phase 3 — eval engine.** Async test runner over the golden set, scoring
  on exact-category match, LLM-as-judge summary relevance (1-5), latency,
  and tokens. Diff logic against the last run: pass-rate delta,
  per-category delta, flipped cases. Warn at >3% delta, critical at >8%
  (configurable via `.env`).
- **Phase 4 — reporting & alerting.** HTML diff report (scorecard, regressed
  cases side-by-side, trend chart) plus a Slack webhook alert. Also a
  7-run moving average to catch slow drift that no single run trips.
- **Phase 5 — CI/CD.** GitHub Action on PRs touching `/prompts`, posts a
  summary comment, blocks merge on critical regressions. Dockerfile
  packaging the runner + dataset + reporting layer, configured entirely
  via env vars (`OPENAI_API_KEY`, `SLACK_WEBHOOK_URL`, thresholds).
- **Phase 6 — portfolio polish.** Loom walkthrough, writeup on why slow-drift
  detection is tracked separately from per-run regressions.
