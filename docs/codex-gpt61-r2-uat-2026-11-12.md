# Andy Write R2 GPT-6.1 Terra UAT — 2026-11-12

## Environment and scope
- Authorized BYL self-hosted DC device: US Mac mini. No machine or browser restart.
- Official Codex CLI upgraded **0.149.0 → 0.167.2** via npm. Prior config backed up at ~/.codex/backup/config.pre-gpt61-20261112.toml.
- US Mac Codex default set to **gpt-6.1-terra**. Andy Write explicitly requests this model on every invocation.
- ChatGPT login retained; no independent OpenAI API key, and no USD cost reported for Codex Plus subscription usage.
- PairDoll source: owner-provided Notion original. No change to WordPress, Notion, PairDoll production or KissSelf.

## End-to-end real run
- Input: 73 locally classified Notion source segments, six question-H2 outline, curated public URLs and OpenAlex metadata (not Google SERP).
- Command: python3 -m andy_write pipeline --job examples/jobs/pairdoll-unboxing.json --provider codex --model gpt-6.1-terra --target-words 1000 --tolerance 0.07 --max-revisions 1
- Draft: **1,140 English words**, model call succeeded.
- Editor: **1,036 English words**, model call succeeded.
- Final accepted range 930–1,070 words; actual 1,036 => **WORD LIMIT PASS**, no extra tightening call required.
- Six question-form H2s + literal Conclusion; local deterministic quality: **RULE_CHECK_PASS**. User / brand / product fact verification remains **PENDING**.
- Read-only generated example: [PairDoll GPT-6.1 Terra review candidate](../examples/output/pairdoll-unboxing-gpt61-terra-review.md), not published.

## Actual usage (from real JSONL events)

| Step | Input Tokens | Cached input | Output Tokens | Reasoning output (already included in output) | Duration |
|---|---:|---:|---:|---:|---:|
| Draft | 17,799 | 12,160 | 1,351 | 20 | 27.84s |
| Edit | 16,642 | 12,160 | 1,262 | 42 | 25.59s |
| **Total** | **34,441** | **24,320** | **2,613** | **62** | **53.43s** |

### Idempotence and durability
- Second write execution with identical inputs: both draft and edit cache hits were true. Ledger remained at **2 completed calls**, no new model usage, final article SHA-256 unchanged.
- Every new real model call appends a usage JSON line to the local ignored per-job ledger, including model/version, stage, timestamp, prompt hash, response hash, input/cached/output/reasoning tokens, duration, word count, success/failure. Failures do not produce fake usage.
- Original Notion article, raw CLI JSONL, full reference content and local ledger are not committed to GitHub.
- Model change, task prompt change, source modifications or --force will invalidate the relevant cached step, causing a new billable-quota call.

### Remaining manual work
- Source-level fact validation, internal links and independently checked external citations.
- Media generation and WordPress/Notion publishing remain outside approved R0–R2 scope.
- Plus five-hour or weekly remaining quota cannot be inferred from token JSONL; this report is measured per invocation, not a validated future throughput capacity.
