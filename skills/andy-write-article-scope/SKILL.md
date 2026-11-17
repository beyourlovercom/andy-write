---
name: andy-write-article-scope
description: Freeze one Owner-defined Article Scope Contract for each Andy Write job before research, rewrite, QA, benchmark or media. Use first for every article and reject conflicting sources, dates, products and unapproved changes.
---

# ANDY_WRITE_ARTICLE_SCOPE_V1

Owner P0-04 SCOPE_INTEGRITY outranks this and every downstream writing Skill.

## Before any article work

1. Read the Owner's original assignment and `policy/owner_rules.json`.
2. Populate a **new** `job_id` and the `article_scope` object in the job JSON **from the Owner's brief**, never from search results or a QC article. Include `subject`, `primary_product`, `excluded_primary_products` (even when empty), `article_time_window`, `qc_time_window`, `qc_structure_urls`, and `allow_explicit_comparison`.
3. For evergreen work, set each date window to `{ "start": null, "end": null }`. If a QC structural URL is supplied, dates for that QC window must be explicit. Never invent a missing date or infer the primary product.
4. Confirm real, substantive Owner original text and its exact source URL. Keep Owner original, QC structure, and factual evidence in **separate** roles.
5. Run `python3 -m andy_write scope-init --job examples/jobs/<job>.json` or the normal `run` command. Both create the private, first-write-only `.runs/_article_scopes/<job_id>.json` contract. If required declarations are missing, stop and request Owner clarification.

## During work

- Check the frozen contract before source retrieval, outlining, prompting, any model rewrite, review, quality and media. The CLI does this for job-based commands, and the rewrite backends independently revalidate before model calls.
- Never let a Skill, model, image, webpage or benchmark change the target product, article time scope, Owner source or evidence role. QC structure is **not** primary factual evidence and is **not** the Owner original.
- QC benchmarking may use only explicitly approved URLs, with publication dates within the contract window and without excluded primary products.
- Verify draft titles against excluded primary products. Treat other semantic and factual drift as **human-review pending**, not as automated PASS. Do not invent verified citations.
- On a conflict: **STOP the affected operation**, report the source and mismatch, preserve the original contract, and await Owner direction. Rephrasing an incorrect substitution is not resolution.

## Amendments and release

- No automatic re-freeze, silent contract revision, or AI-written approval. Even `--force` on rewriting does not override scope.
- A changed job declaration or Owner source hash fails closed with `ARTICLE_SCOPE_CHANGED`.
- Any amendment must have a separate, explicit Owner authorization, recorded old/new scope, change reason, affected artifacts and version in a reviewed PR/change record; only after that review may an authorized amendment process be implemented. This Skill provides **no** self-service override.
- Test a new full-size article and an independently scoped torso article to prove that the rule is per-article, not a universal ban on torso topics.

Validation: `python3 -m unittest tests.test_article_scope -v`; also run the existing project suite before PR. No auto-merge or production publish.
