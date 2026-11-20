# R7.4 — Dev CLI integration evidence / Owner UAT pending

Date: 2026-11-20 (Asia/Hong_Kong). Stage: **Technical simulation PASS, real Owner UAT NOT PASS**.

## Test control and limitations

- Isolated new-job synthetic cases only. No existing article, Mary task,
  Production WordPress data, real order, API credit or writer message touched.
- Inputs are deliberately artificial. `example.invalid` is a fake Owner
  source; six `publisher*.example.com` URLs are **not observed Google rankings**.
- Therefore the `verified` contract is a **validator fixture**, not credible
  search evidence. Its pipeline `PASS` proves control flow, **not** editorial
  correctness or a real evidence-quality PASS.
- Command exercised for each case: `ANDY_WRITE_ENV=dev
  ANDY_WRITE_SEARCH_INTENT_R7_ENABLED=1 python3 -m andy_write run --job <synthetic-job>`.
- The job-specific `scope-init` creates a real immutable test fingerprint;
  the generated handoff must match it. Temporary artifacts are isolated under
  `.runs/` and cleaned after tests.

## Observable before / after behavior

| Synthetic Dev case | Input contract | Actual CLI result | Source catalog | Outline | Publication |
|---|---|---|---|---|---|
| Informational guide control | Valid V1 shape with 6 fabricated stable-looking results; `PASS` | Exit 0, gate `PASS`, progresses | Created | Created | Untouched, no draft |
| Incomplete evidence | `provisional` + `REVIEW` | Exit 2, gate `REVIEW`, explicit error | Not created | Not created | Untouched |
| Wrong buyer stage | Audit `Mismatch` + `BLOCK` | Exit 2, gate `BLOCK`, explicit error | Not created | Not created | Untouched |

Extra regression: when `ANDY_WRITE_ENV=production` with feature flag on,
the CLI refuses **before** potentially networked Research. The existing
production/default-off path is unchanged. Every evaluated decision records
the Owner fingerprint, input hashes and `publish_ready=false`.

## Pending Owner acceptance (do not falsely close)

1. Feed **real** V1.1 Search Intent outputs from an authorized US/en/mobile
   capture; verify final publisher URLs and capture stability before any
   factual `verified` decision. At least one eligible real PASS case is needed.
2. Run real examples representing guide alignment, commercial page-type
   Mismatch and provisional REVIEW, recording sources and chosen stage.
3. Decide how Owner will inspect/approve: the existing application is a Python
   CLI, not an authenticated web dashboard. Any new UI and access method must
   be separately designed/authorized; do not invent a Dev URL.
4. Owner inspects preserved scope, contract/report, receipt and branch CI.
   Only then consider a separate PR/merge/release request. Production remains off.

Rollback baseline: `a89b2dca11537ccf9d35e84eeae1ce388cacba37` on
`feat/r0-r2-research-writing-mvp`. R7 candidate branch is separate;
the default flag remains off.
