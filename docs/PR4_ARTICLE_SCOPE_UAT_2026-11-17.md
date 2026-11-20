# PR #4 — ANDY_WRITE_ARTICLE_SCOPE_V1 UAT

Date (Owner workspace): 2026-11-17. Environment: US Mac mini, isolated branch `feat/article-scope-v1` and private `.runs/pr4-uat` synthetic test materials only. No real article, paid model, WordPress or production writes.

## Real CLI Canary

| Case | Observed | Result |
|---|---|---|
| New full-size article with explicit Owner-like synthetic brief | `scope-init` produced `FROZEN`, revision 1, fingerprint; no research started | PASS |
| Independent torso article | A different job produced a separate frozen contract | PASS |
| Wrong original: torso H1 supplied to full-size brief | `SOURCE_PRODUCT_MISMATCH` before research | PASS for blocking |
| Contract creation on invalid first-run | Initially blocked **after** writing invalid contract | DEFECT FOUND |
| Same invalid first-run after fix, fresh job ID | `SOURCE_PRODUCT_MISMATCH`; `ls` confirmed **no** contract file created | PASS after fix |
| Change only frozen article subject | `ARTICLE_SCOPE_CHANGED`, and contract SHA-256 stayed identical before/after | PASS |

The first-run defect was repaired in the PR before acceptance: `ensure_article_scope` now validates the source heading against exclusions **before** exclusive contract creation. An explicit regression test verifies that invalid initial scopes do not leave a frozen file. The pre-fix synthetic invalid contract is retained privately as test evidence; it has not been normalized, deleted or committed.

## Automated checks

- `python3 -m unittest discover -s tests -q` on US Mac mini: **181/181 PASS** after the fix.
- GitHub CI matrix: offline-tests Python 3.11 and 3.12; owner-rules Python 3.11 and 3.12: PASS after the updated push (verify new run IDs before merge).
- QC unit tests cover 2022 against 2025 date window, wrong product and unapproved URL; benchmark returned only explicitly approved sample. These are mocked, no live website scraping.
- Both rewrite backends bind frozen scope fingerprint before any model call; no paid model was invoked during UAT.

## Remaining boundaries

1. This is deterministic scope/identity **gate** validation; nuanced semantic and factual drift inside article paragraphs still needs human claim-level review. PASS does not equal full editorial or publishing approval.
2. Every first-time job must carry a separate Owner-defined `article_scope`. Unscoped legacy jobs fail closed; no AI-generated default subject.
3. No self-service amendment or AI approval override. Future authorized scope changes need a separately logged Owner-approved change process. `.runs` contract hashes are integrity guards within the runtime, not cryptographic signatures of Owner approval.
4. PR targets full V1.2.3 feature branch only; `main` remains separate until an additional authorized release.

Acceptance: **PASS for PR #4's frozen per-article scope mechanism and safe merge to the V1.2.3 development branch; not approval to ship runtime to main or publish any article.**

Rollback: revert the PR merge on the development branch if needed; preserve prior feature baseline `aeeffe6` and current Owner policy on `main` (`ed831a5`).
