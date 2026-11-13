---
name: andy-write-draft
description: "Rewrite only an existing user-provided full article using source evidence and Codex CLI in read-only mode."
---
# Andy Write Draft — supplied-article rewrite ONLY

Codex CLI has exactly one permitted job: rewriting the real article supplied by the user.

1. Read the original article from the approved local source file and verify provenance/SHA-256. No source, no Codex invocation.
2. Complete Research / Source classification / Markdown Outline using the local DC/Python pipeline, NOT Codex.
3. Call Codex CLI only to rewrite/adapt the supplied article, then optionally edit English prose or selectively rewrite existing H2 sections. The model must not search, call tools, write code, produce images or videos, check external resources, upload media or publish.
4. Preserve the original source, record real tokens in a gitignored ledger, and do not fabricate evidence, originality or quality claims.
5. Independent Python performs all structural/SEO/quality checks. Codex only rewrites text in response to specific editorial changes.
6. WordPress and Notion publication is not authorized here.

Run local research/source/outline first, then rewrite with an existing owner source:

    python3 -m andy_write run --job examples/jobs/pairdoll-unboxing.json
    python3 -m andy_write write --job examples/jobs/pairdoll-unboxing.json --provider codex --model gpt-6.1-terra --target-words 1000

The old draft and ImageGen UAT examples are retained as historical results only. Current project policy supersedes older instructions.
