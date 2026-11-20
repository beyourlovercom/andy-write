# R9 — KissSelf scope-aware QC rule upgrade and actual US Mac mini Dev UAT

**Date:** 2026-11-20 (Asia/Hong_Kong). **Technical result:** DEV REAL-SNAPSHOT PASS.
**Editorial judgment:** `HUMAN_REVIEW_REQUIRED` — no human gold labels or publication approval.

## Owner decision (read this first)

R9 supplies a reusable *review-candidate* gate, not an automatic quality score.
The five R8 problem **types** are now surfaced at their actual product sections;
two additional water-rating evidence candidates also require review. Nothing
was written to WordPress, a writer, an Owner article, main or Production.

## Frozen task and benchmark

- Baseline: [R8 public KissSelf reverse-QC](R8_KISSSELF_REAL_QC_BASELINE_2026-11-20.md)
  and [the five-item candidate queue](r8_kissself_qc_review_queue.v1.json).
- Current public KissSelf post #26268: [shower waterproof toys article](https://kissself.com/how-to-boost-intimacy-using-waterproof-toys-in-the-shower.html).
- First public date 2025-12-26; last public revision 2026-10-04. The original
  December 2025 body has not been established. Scope is adult shower-intimacy
  products; the article is *competitor benchmark data*, not Owner original.
- Exact rendered body SHA-256: `f691c7f330bef6e15589c68b2ef231fabfc7a393f8f00f9acb38eb5c84f19af9`.
  The R9 contract pins post ID, link, modified date and hash; a changed revision
  fails before the analyzer can produce an apparently equivalent audit.
- No target keyword, target-country organic SERP or Owner draft has been supplied
  for this public sample. Search Intent verdict remains **UNASSESSABLE**.

## Before vs after (no fabricated quality metric)

| Check | R8 actual existing analyzer | R9 actual new Dev checker |
|---|---|---|
| Input | Exact private WP snapshot + unrelated structural control | Exact same private WP snapshot + immutable scoped signals |
| Result | `STRUCTURAL_REVIEW_REQUIRED` | `HUMAN_REVIEW_REQUIRED` |
| Product/audience section location | No independent context classifier | 2 P0 review candidates with product-level headings |
| Model / cleaning evidence triage | Broad language-pattern risks only | 4 P1 candidates including both R8 evidence issues |
| Time-sensitive table triage | Table count only | 1 P2 offer/freshness candidate |
| Human verified errors | 0 | **0** (still pending) |

## Real article, not synthetic-only, observed 2026-11-20

On the official BYL self-hosted DC OAuth connection, `us-macmini`, an isolated
clean checkout at `/Users/a/ai/worktrees/andy-write-r9-dev` ran:

```sh
python3 -m andy_write qc-context \
  --post-json .runs/r9-kissself-20261120/kissself_current_wp.json \
  --scope docs/r9_kissself_benchmark_scope.v1.json \
  --report .runs/r9-kissself-20261120/context_report.json
python3 -m unittest discover -s tests -q
python3 scripts/check_owner_rules.py
```

Real result: **7 derived candidates across 29 inspected section groupings**;
**P0 = 2, P1 = 4, P2 = 1**, `publish_ready=false`; actual tests passed
(204 at first Mac run, 205 after repeated-H4 regression test), Owner P0 PASS.
All full-article bytes and detailed private receipts remain Gitignored in `.runs`.

| R8 ID | R9 rule output and public section | Assessment |
|---|---|---|
| KS-01 | P0 `PRODUCT_OR_AUDIENCE_DRIFT_REVIEW`, [Couples’ Rings](https://kissself.com/how-to-boost-intimacy-using-waterproof-toys-in-the-shower.html#Couples_Rings) | Candidate surfaced; no factual verdict |
| KS-02 | P0 same rule, [Safety in Wet Environments](https://kissself.com/how-to-boost-intimacy-using-waterproof-toys-in-the-shower.html#Safety_in_Wet_Environments) | Candidate surfaced; source relevance still unverified |
| KS-03 | P1 `CLEANING_CLAIM_SOURCE_REVIEW`, [Cleaning and Care](https://kissself.com/how-to-boost-intimacy-using-waterproof-toys-in-the-shower.html#Cleaning_and_Care) | Actual manufacturer/manual passage still needed |
| KS-04 | P1 `MODEL_SPEC_PROVENANCE_REVIEW`, [Massage Wands](https://kissself.com/how-to-boost-intimacy-using-waterproof-toys-in-the-shower.html#Massage_Wands) | Exact model/IP rating support still needed |
| KS-05 | P2 `PRICE_OFFER_FRESHNESS_REVIEW`, [Suction Toys](https://kissself.com/how-to-boost-intimacy-using-waterproof-toys-in-the-shower.html#Suction_Toys) | Offer identity/date still needs independent verification |

Additional P1 model/spec provenance candidates: `Vibrators` and `Couples’ Rings`.
These two are **extra review work**, not two confirmed defects or a precision
estimate. The prior real-run false location "Pros and Cons" was corrected by
retaining the parent H3 product category across identical H4 headings.

## Generalized Skill change, regression and limits

- New offline `qc-context` CLI and `andy_write/qc_context.py`; no model, Codex,
  network fetch, writer, publishing, or change to the default R7 pipeline.
- Versioned Quality / Source / Search Intent Skill guidance, with an explicit
  per-benchmark signal contract separate from the Owner Article Scope Contract.
- Synthetic controls test all five issue classes, legitimate short comparisons,
  genuine cautionary language, tampered source/revision/role and repeated H4s.
- **Only manually specified cue terms and syntax-level claims are tested.**
  The algorithm cannot prove semantic drift, article relevance, factual truth,
  human-labeled recall/precision, quoted source entailment or search ranking.
  A clean report is not a PASS. Future benchmarks need independently frozen
  scope/signal contracts and a qualified human evidence review.

## PR boundaries, rollback, next Owner gate

- R9 feature branch `feat/r9-kissself-context-qc` is **stacked on R8** head
  `292c1120fd76a46c6d2a115d5e9d72a67a52a53a`, which remains Draft PR #8.
- GitHub main is the prior stable `57be56753e9578c2914eeeda852a2d80aeed2281`.
  No merge, default-path activation, deployment or article rewrite performed.
- Rollback is to leave/close the R9 Draft PR; pre-R9 checker and R7 Dev gate
  remain unchanged on R8 and main. This is an isolated additive CLI.
- **Owner editorial UAT:** confirm or reject each of the five R8 candidate
  issues with concrete source evidence; decide whether the two extra P1 items
  merit review. Only after real labels and a separate approval can the team
  measure false positives and authorize a further R10 closed-loop writing test.
