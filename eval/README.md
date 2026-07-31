# Golden Set Evaluation

Start the backend on port 8001 from the repository root:

```bash
uvicorn --app-dir codebase/backend app:app --reload --port 8001
```

Validate the golden-set structure without making any model request:

```bash
python eval/run_eval.py --dry-run
```

Run all cases against the local backend:

```bash
python eval/run_eval.py --base-url http://127.0.0.1:8001
```

The runner waits 2.5 seconds between requests by default, keeping the run below
the free-plan request-per-minute limit. Change it only when your account's
limits permit it, for example `--delay-seconds 4`.

Each run writes a timestamped raw JSON artifact and Markdown summary to
`eval/results/`. The JSON records the exact request, raw response, model used,
latency, deterministic failures, and dimensions requiring semantic review.

The runner automatically checks response schema, selected term preservation,
confidence enum and required clarification, output length, acronym expansion,
evidence-span grounding, and selected confidence expectations. It does not
claim to score contextual meaning, beginner clarity, example correctness, or
the usefulness of a refusal. Those dimensions require an LLM judge or human
review and are listed per case in the output.

## Semantic Judge

After a real-model run, use a Groq model to judge only the semantic dimensions.
The default judge is `llama-3.1-8b-instant`, which is available to this project
and differs from the normal target model `llama-3.3-70b-versatile`:

```bash
python eval/run_judge.py eval/results/run-<timestamp>.json
```

The judge waits 12 seconds between calls by default because its long rubric
prompt can hit the free model's token-per-minute limit. On a Groq 429 response,
it waits and retries the same case up to two times.

The judge skips local fallback outputs and request errors. Such cases remain
failed and make the combined score provisional; fix the LLM/backend failure
and rerun the complete golden set before comparing the score to the quality
bar. Verify eligible cases without spending tokens with:

```bash
python eval/run_judge.py eval/results/run-<timestamp>.json --dry-run
```
