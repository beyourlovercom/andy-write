# R7.4 — Real OpenSEO REVIEW results in isolated Andy Write Dev

**Capture / test date:** 2026-11-20, Asia/Hong_Kong. **Environment:** US Mac mini, independent worktree `/Users/a/ai/worktrees/andy-write-r7-dev`. **Code:** `830bf543a5ef346edb3877c5ab99f6c1253afcf0` on `feat/search-intent-r7-dev`.

**Result:** Three real SERP-derived V1.1 contracts were accepted by the validator, then each stopped the real Dev CLI between Research and Source with `REVIEW / STOP`. **Technical REVIEW-path acceptance: PASS. Owner accepted this limited REVIEW-path UAT on 2026-11-20.** Full R7.4 acceptance is separate; this report does not establish a full real eligible PASS case or a working Dev UI.

## Evidence origin, without false verification claims

- Existing OpenSEO project: [Andy Write Search Intent QA (US)](https://app.openseo.so/p/6cbe5181-19be-49ed-a154-46928f85afef).
- Three provider reads per keyword at US / English / mobile. Observed position is OpenSEO `bestPosition`, never its merged `rank`. Some URLs and relevance remain independently unverified, so all three evidence statuses stay **`provisional`**, gates **`REVIEW`**.
- V1.1 `grade_serp_evidence.py` evaluated real normalized results, and `validate_contract.py` accepted all three handoff contracts. Content-fit `audit.verdict=Unassessable`: no real Owner article was given for this test.
- The Dev jobs deliberately use **synthetic, nonfactual source placeholders** and explicitly assumed audience `adult owners`; their frozen Article Scope fingerprints are test fixtures, **not actual editorial approval**. The `realdoll official website` case is an intentional competing-brand identity negative control in a PairDoll test context, not authorization to create that article.

## Actual Dev execution

| Real query | Raw / identifiable | Independently qualified on-topic + stable + publisher URL (required ≥5) | CLI exit | Saved gate / next stage | Research | Source / Outline / Draft |
|---|---:|---:|---:|---|---|---|
| `how to clean a sex doll` | 15 / 13 | 2 | 2 | `REVIEW / STOP` | Created | All absent |
| `best full size sex dolls` | 14 / 13 | 1 | 2 | `REVIEW / STOP` | Created | All absent |
| `realdoll official website` | 13 / 13 | 0 | 2 | `REVIEW / STOP` | Created | All absent |

For the brand query, independent first-party verification identified `realdoll.com` (contact page), but the captured provider set did **not** contain this official domain. Lookalike domains were not substituted for it.

The real command, issued once and then retried to test idempotency, was:

```bash
ANDY_WRITE_ENV=dev ANDY_WRITE_SEARCH_INTENT_R7_ENABLED=1 \
  python3 -m andy_write run --job .runs/r7-real-review-20261120/<case>/job.json
```

Each run reported `Andy Write error: Search Intent REVIEW: QC returned REVIEW; Owner review/evidence required`. A second invocation also returned exit 2. **Each case retained exactly one decision receipt** before and after retry. For all three, the saved `contract_sha256` and `report_sha256` matched the actual files; `publish_ready=false`; no `source-catalog.json`, `outline.md`, `article-v1.md`, or `run-manifest.json` exists. No WordPress interaction, real article mutation, writer messaging, PR creation, main merge, or Production release was performed.

## Inspectable Dev artifacts

Private ignored root on US Mac mini: `/Users/a/ai/worktrees/andy-write-r7-dev/.runs/r7-real-review-20261120/`

Each of the three subdirectories below contains:

- `job.json` and `synthetic-source.md` — explicitly artificial integration job.
- `intent_contract.json` — full, real SERP-derived 13-result V1.1 handoff, bound to frozen test scope.
- `intent_report.md` — observed intent, quality gaps, representative publisher links and Owner decision.
- `research-pack.json`, `search-intent-decision.json`, `search-intent-decisions/<sha>.json` — actual workflow output and idempotent decision receipt.

| Case subdirectory | Frozen test Article Scope fingerprint |
|---|---|
| `how_to_clean_a_sex_doll` | `3b92572309a0415f11b089e72cf18e8d694be685a41c17b5b291007855e031b5` |
| `best_full_size_sex_dolls` | `d3db77188e69641552140c6a94f8437ed79483f7bacb273141cf0defb948cfe5` |
| `realdoll_official_website` | `27148d6cc0fcebf6d4e6154472b9a9c80d370eb94b4aa76d71879686ef6f8389` |

Raw normalized SERP provider data and private run artifacts remain **outside GitHub** per `OWNER_P0` restrictions. Only this summary is committed.

## Owner acceptance — exact decision needed

- [x] Real `provisional` evidence was not promoted to `PASS`.
- [x] Real `REVIEW` stopped before Source, Outline, Draft, with actual exit/receipt proof.
- [x] Frozen test scope fingerprint checked, receipt hashes verified, retry idempotency preserved.
- [x] Independent branded official-domain ambiguity held for human review.
- [x] No production, real article or writer side effects.
- [x] **Owner personally confirmed REVIEW/STOP behavior and accepted this limited Dev technical evidence on 2026-11-20.** The exact Owner instruction was: “R7 真实 REVIEW Dev UAT PASS。继续补齐真实 PASS / Mismatch 场景；暂不授权合并和 Production 发布。”
- [ ] **R7.4 full-scope acceptance:** obtain at least one independently `verified` real eligible PASS case and a real article/audit Mismatch; determine whether an authenticated Dev UI is required. The current repository has a Python CLI, not an authenticated web dashboard.

**Owner scope of signoff:** REVIEW path only. Real PASS and Mismatch cases, full workflow UAT, any new UI, merge and Production release require distinct evidence or decisions; no broader authorization is implied.

**Rollback:** leave `ANDY_WRITE_SEARCH_INTENT_R7_ENABLED=0`; stable pre-R7 commit `a89b2dca11537ccf9d35e84eeae1ce388cacba37`. Do not merge to main or release to Production without a separate Owner decision.
