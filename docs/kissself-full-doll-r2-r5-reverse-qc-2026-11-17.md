# Andy Write V1.3 — Owner-approved KissSelf sex-doll reverse QC

**Date:** 2026-11-17 (Hong Kong). **Stage:** R2–R5 engineering review; human factual/semantic UAT PENDING. **Base/rollback:** `3b2e987b889ba80889dcebb8171e181eb9a65b6b`. **Target:** development branch only, never `main`.

## R1 approved benchmark and roles

- Owner explicitly approved https://kissself.com/how-to-experiment-with-sex-skills-and-intimacy-preferences-using-a-sex-doll.html (WP ID `26242`) for reverse QC.
- Published **2025-12-20**, updated **2026-07-28**. Current `content.rendered` SHA-256: `aedf52ff634da9d1470c74d44df45d24b8fca3ebe758220659bacc2edc0c11c1`. The original 2025 body has **not** been recovered.
- The article concerns sex dolls and full-body contexts but does not expressly identify 150–170 cm full-size models. Its role is `QC_STRUCTURE_ONLY`, NOT Owner original, verified product evidence, or permission to rewrite the competitor's prose.
- `ANDY_WRITE_QC_SCOPE_V1` records this experiment, NOT a newly issued `ANDY_WRITE_ARTICLE_SCOPE_V1` writing job. No Torso official benchmark, new article, sealed cross-industry holdout or media generation.
- Raw public benchmark body and private Owner/reviewer source stay under ignored `.runs`; no full articles enter GitHub.

## R2 structural observations

| Observable signal | KissSelf current | Legacy edit | V2 output | Editor-quality V2 |
|---|---:|---:|---:|---:|
| Approximate English words | 3,734 | 1,036 | 1,422 | 1,007 |
| H2 | 8 | 7 | 7 | 7 |
| H3 | 26 | 0 | 0 | 0 |
| Tables | 6 | 0 | 1 | 0 |

The competitor targets **skills/preferences/care**; existing Owner outputs target **Unboxing**. All comparisons are `CROSS_INTENT_STRUCTURE_ONLY`. They do not show competitor superiority, ranking gain, or a desirable H3/table quota. The three Owner artifacts are revisions of **one** existing article, not three independent articles.

## R2 information-value and evidence gap matrix

| Dimension | Evidence | Skill-level improvement | Unproven claim / limitation |
|---|---|---|---|
| Intent | Different reader questions in the same broad product family | Declare both intents and compare structure only when mismatched | No competing outline transplant |
| Section value | 26 H3s and 6 tables in benchmark | Human review of source-backed decisions, caveats and subsection information gain | No numeric quota or automatic benefit |
| Repetition | 0 exact substantial cross-H2 duplicates across three Owner outputs | Hash-only sentence repetition review plus counterexample | Repeated safety cautions may legitimately help |
| Citation relevance | 32 external link instances across 21 domains | Match specific claim to evidence role, never link-count as proof | No cited factual claim was human-approved in this experiment |
| Model/safety language | 12/78 public paragraphs flagged, including 8 material/safety and 4 universal-language candidates (overlap possible) | Require appropriate manufacturer/model evidence and human review | Language candidates are NOT 12 established errors |
| Media/length | Article length and media volume vary | Keep media/word metrics descriptive only | Generating images/videos remains forbidden |

## R3 reusable delta

1. Add `qc_scope.py` and an exact approved contract: URL, WP post ID, current body hash, publication/revision dates, source roles, excluded primary topics, Owner draft URL and declared reader intents are verified fail-closed.
2. Add `qc-profile --qc-contract`; legacy invocation still works but reports `UNDECLARED_LEGACY_QC_SCOPE` and cannot imply Owner approval or create an Article Scope Contract.
3. Return `intent_relation` in every structural comparison; even matching declared intent is not an automatic quality PASS.
4. Add `CROSS_SECTION_REPETITION_REVIEW`: only sentence hash and H2 names enter the derived report, and actual value remains a human judgment.
5. Upgrade Source, Outline, Draft, Editor and Quality Skills. No competitor-prose rewrite, Codex QC or automatic article change.

## R4 negative controls and actual offline evaluation

- Approved current KissSelf WP snapshot fetched read-only, with frozen contract validation. Three existing Unboxing output versions passed bounded `qc-profile` execution with `STRUCTURAL_REVIEW_REQUIRED` and `CROSS_INTENT_STRUCTURE_ONLY`.
- Synthetic tests reject changed URL, ID, revision/body hash, source role, no approval, Torso-as-primary and empty intent. Synthetic repeated/unique sentences demonstrate review signal on/off without treating duplicate prose as factual error.
- **187/187 local tests PASS**; `scripts/check_owner_rules.py` **PASS**. Three output versions are one Owner article lineage: no independent human quality improvement can be inferred.

## R5 review and rollback boundary

- Target PR base is `feat/r0-r2-research-writing-mvp` ONLY. No `main` merge, WordPress/Notion mutation, Codex CLI, paid API or media generation.
- Engineering safeguards and tests: PASS. Human semantic/factual article approval: **PENDING**, as is Owner final PR acceptance.
- Before merge: close the PR and retain the base commit `3b2e987b889ba80889dcebb8171e181eb9a65b6b`. After any later approved development merge: revert the exact Skill Delta merge commit, keeping Owner P0 and Article Scope V1 intact.
- Reproduce from repo root: `python3 -m unittest discover -s tests -q` and `python3 scripts/check_owner_rules.py`. Fetch approved public WP article into ignored `.runs` with `scripts/fetch_public_wp_benchmark.py`; run `qc-profile` with the frozen `examples/qc-scopes/kissself-full-doll-2026-11-17.json` contract.
