# R10 — KissSelf cross-sample QC + manual Owner draft QC Dev UAT

**Date:** 2026-11-20 Asia/Hong_Kong. **Scope:** read-only current public
competitor content and synthetic offline Owner-draft regression. **No real
writer draft was rewritten or compared**, no Production/default pipeline change.

## Decision in under one minute

R9's P0 off-topic signals appeared on the R8 shower-toy benchmark **twice**
and on an independently collected KissSelf adult-toy cleaning article **zero
times**. Both articles still have P1 evidence checks: these are *review
candidates*, not human-confirmed false statements or precision/recall.
For Rule acceptance see [Owner five-item review](R10_OWNER_FAST_QC_REVIEW_2026-11-20.md).

## Frozen sources, roles and actual collection

| Frozen identity | R8 first article | R10 second article |
|---|---|---|
| KissSelf WP ID | 26268 | 26353 |
| First published | 2025-12-26 | 2026-01-09 |
| Current public revision | 2026-10-04 | 2026-07-28 |
| Source subject | Waterproof adult intimacy devices in shower | Cleaning/sanitizing adult toys |
| Frozen contract | [R9 first scope](r9_kissself_benchmark_scope.v1.json) | [R10 second scope](r10_kissself_cleaning_scope.v1.json) |
| Original published body independently verified | No | No |

Second public article:
[How to Properly Clean and Sanitize Your Sex Toys in 2026](https://kissself.com/how-to-properly-clean-and-sanitize-your-sex-toys-in-2026.html).
Actual public WP REST retrieval on US Mac mini 2026-11-20 returned post ID
26353, slug `how-to-properly-clean-and-sanitize-your-sex-toys-in-2026`, last
modified `2026-07-28T02:42:46`, rendered body SHA-256
`a3dc40ad6144eede73bf2e265b8cf67118aacdaa474b2ccc0c072a1f1f8f9363`.
Original Jan 2026 text was not available. Both posts are public competitors
for QC only, **not** Owner originals, citations proving product claims or
sources for a derivative rewrite. No localized SERP or Owner target keyword.

Reproducible second capture (exact publication range, default late-2025
fetch range left intact):

```sh
python3 scripts/fetch_public_wp_benchmark.py \
  --site https://kissself.com \
  --slug how-to-properly-clean-and-sanitize-your-sex-toys-in-2026 \
  --published-from 2026-01-01 --published-through 2026-12-31 \
  --out .runs/r10-kissself-20261120/second_current_wp.json
python3 -m andy_write qc-context \
  --post-json .runs/r10-kissself-20261120/second_current_wp.json \
  --scope docs/r10_kissself_cleaning_scope.v1.json \
  --report .runs/r10-kissself-20261120/second_context_report.json
```

## Real cross-sample comparison

| Actual machine output | R8 shower benchmark | R10 cleaning article |
|---|---:|---:|
| Sections inspected | 29 | 29 |
| P0 off-topic/audience candidates | 2 | **0** |
| P1 model/cleaning source candidates | 4 | 3 |
| P2 price/offer candidates | 1 | 0 |
| Total unconfirmed candidates | 7 | 3 |
| Qualified editor labels | 0 | 0 |
| Search Intent verdict | Unassessable | Unassessable |

The cleaning article's 3 P1 candidates are **on-topic** sections:
`Cleaning vs. Sanitizing`, `How Often to Clean`, and
`Can you use household cleaners on sex toys?` They indicate that exact
material/manufacturer support needs review, not that cleaning is off-topic.
This supports an exploratory **P0 negative control**, not a measured
false-positive rate or proof of machine semantic accuracy.

## R10 reusable changes and manual writing-QC pilot

1. The public WP read-only fetch now accepts both explicit publication dates
   for a later article. A wrong slug, outside-window date, bad redirect, or
   non-private destination fails closed; legacy R8 default remains late 2025.
2. New `qc-draft-context` Dev-only CLI checks an **existing** owner draft
   against its *actual previously frozen* Article Scope Contract. It flags
   section-level excluded primary-product substitution as a candidate, while
   respecting legitimate explicit comparisons. It cannot invent an Owner
   scope, retrieve a new article or auto-approve writing quality.
3. Synthetic offline integration: Owner scope `full size doll`, excluded
   `torso`; a section substantially substituting torso is marked P0 for human
   review; a short, negated comparison is not. The real article is untouched.
4. **No automatic insertion into Research/Source/Outline/Draft/Editor/Quality.**
   The selected Search Intent Skill is manual-pilot-only until independent
   Owner UAT. No claim of a real writing-model A/B quality improvement.

Manual command (requires actual frozen private Owner scope + existing draft):

```sh
python3 -m andy_write qc-draft-context \
  --job .runs/<job>/job.json --draft .runs/<job>/article.md \
  --report .runs/<job>/context-review.json
```

## Evidence and next gate

- Real Dev execution used US Mac mini isolated worktree
  `/Users/a/ai/worktrees/andy-write-r10-dev`; raw competitor source and
  full QC receipts remain Gitignored `.runs` and are not in the PR.
- Offline tests: **210/210 PASS** locally; real US Mac mini and GitHub CI
  must be rerun at the final PR commit (record result in the PR).
- Before/after is **detection instrumentation**, not writing quality or
  Google ranking effect. The first two articles are exploratory examples;
  the second is not an independently blinded, labeled holdout.
- Review/approval request: Owner confirms which of KS-01..KS-05 should
  remain standing QC rules; an independent editor verifies exact claims and
  linked source passages before labels are promoted to factual truth.
- A real Owner writing A/B still requires approved source article, frozen
  subject/keyword, two edited versions, independent blinded editorial review
  and a separate authorization for any rewrite. It has **not** happened.
- R10 is stacked after R9 Draft PR #9 and R8 Draft PR #8. GitHub main
  remains `57be56753e9578c2914eeeda852a2d80aeed2281`.
  Rollback: leave/close R10 Draft PR; no runtime default path modified.
