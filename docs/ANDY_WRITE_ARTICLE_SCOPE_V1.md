# ANDY_WRITE_ARTICLE_SCOPE_V1 — Owner P0 per-article scope

Status: feature-branch implementation; Owner UAT and merge approval pending.

## The rule

Every **new** writing job inherits `OWNER_P0` and freezes a **separate** Article Scope Contract before research. Any AI model, Skill, reference, image, search result or material that contradicts the initial Owner brief must be rejected. No unapproved widening, product substitution, date substitution, role substitution, factual evidence laundering, or paraphrase to conceal a conflict.

## Required new-job declaration

The `article_scope` object in a job JSON must be Owner-defined, not silently inferred:

```json
{
  "subject": "OWNER-SPECIFIED ARTICLE SUBJECT",
  "primary_product": "OWNER-SPECIFIED PRIMARY PRODUCT",
  "excluded_primary_products": [],
  "article_time_window": {"start": null, "end": null},
  "qc_time_window": {"start": null, "end": null},
  "qc_structure_urls": [],
  "allow_explicit_comparison": false
}
```

The job's `source_url` is the Owner original. `research_urls` may only be candidate independent factual sources. `qc_structure_urls` are structural comparators only; when nonempty, QC dates must be specific `YYYY-MM-DD` values. Each job ID must be distinct; old jobs without declaration fail closed until the Owner gives the missing task boundaries. An article about torsos can have `primary_product: "sex doll torso"`; an independent full-size article can exclude that category. These restrictions are **not** universal product bans.

## Creation and checking

- `python3 -m andy_write scope-init --job PATH`: generate an immutable private `.runs/_article_scopes/JOB_ID.json`, or verify its fingerprint if it already exists.
- `python3 -m andy_write run --job PATH`: performs the same scope initialization before any retrieval. `pipeline` also starts this way.
- Later job-based commands verify the same contract and the Owner original source hash; missing contracts or changed scope fail closed.
- Before both OpenAI and Codex CLI rewrites, the prepared prompt and run manifest must bind the same scope fingerprint; old prompts without it cannot be reused.
- Codex CLI is authorized **only** for rewriting the full existing Owner article. No Codex calls for coding, scope creation, research, QA, graphics, or web operations.
- QC benchmark samples are restricted to the contract's explicit URLs, publication period and product exclusions. Generated draft H1 is checked for obvious excluded-primary-product substitution. Human verification of semantic fidelity and claim evidence remains mandatory.

## Conflict and change procedure

On mismatch, report `job_id`, frozen version and fingerprint, offending source/field, observed value and expected constraint; stop only affected work. Never silently mutate the contract. To change it, the Owner must explicitly approve a logged change record containing previous scope/fingerprint, proposed scope, reason, affected artifacts and review date. The current implementation intentionally has **no** `--force-scope` or AI self-approval path; Owner-authorized amendments require a separately reviewed implementation and PR.

The private `.runs/` directory is gitignored. Contracts and full originals stay private. This guard enforces ordinary application paths but is not a cryptographic signature, and cannot replace protected GitHub branch approvals or human fact checking.

## Acceptance

- Same article reuses same frozen fingerprint; another article gets a different contract.
- Full-size job rejects a torso substituted as its primary title; independently scoped torso job remains valid; express comparison can be authorized.
- Wrong-year QC structural samples (e.g. 2022 against late-2025) fail; QC cannot impersonate the Owner original or automatically prove facts.
- Changing product, dates, source role, original text or scope cannot silently rewrite the frozen contract.
- New model prompts and draft output undergo scope checks; evidence/semantic final PASS remains human-controlled.

Branch strategy: PR into full-runtime feature branch first. GitHub `main` currently contains Owner P0 policy but not all V1.2.3 runtime; never merge the unreviewed full runtime into `main` by accident.
