---
name: andy-write-draft
description: "Source-grounded English long-form writing with Codex CLI GPT-6.1 Terra, versioned drafts, usage ledger and bounded word counts."
---
# Andy Write Draft — R2

PairDoll requires a user-provided reference. Read the R1 source catalog and evidence ledger before drafting. Never invent personal testing, customer stories, factory ownership, warranties, materials compatibility, health claims or specific numeric results.

Default writer is Codex CLI GPT-6.1 Terra on US Mac mini. Minimum Codex version 0.159.0. Use the versioned and audited CLI rather than an ad-hoc shell prompt.

Execute:

    python3 -m andy_write write --job examples/jobs/pairdoll-unboxing.json --provider codex --model gpt-6.1-terra --target-words 1000 --tolerance 0.07 --max-revisions 1

The full pipeline also runs Research, Source and Outline first:

    python3 -m andy_write pipeline --job examples/jobs/pairdoll-unboxing.json --provider codex --model gpt-6.1-terra --target-words 1000

Safeguards:
1. Always explicitly request a real model; use ChatGPT-authenticated Codex CLI in a read-only sandbox. Never invent success if the CLI fails or quota is exhausted.
2. Save local draft, edited draft, optional length-control draft and final candidate separately; retain original material untouched.
3. Count words outside the model and use at most 1 optional rewrite by default. If the final remains out of range, status must be REVIEW_REQUIRED, not PASS.
4. Append the actual per-call token usage and timings to the local Git-ignored ledger. Stage cache hits must not add token counts.
5. Never publish, change an existing WordPress Post, or claim human factual approval. The final article is for local editorial review.

The OpenAI Responses API adapter remains optional and requires a separate OPENAI_API_KEY.
