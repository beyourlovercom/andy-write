# R7.4 — Real positive and negative Search Intent Dev CLI evidence

**Tested:** 2026-11-20 (Asia/Hong_Kong). **Runtime:** independent US Mac mini worktree `/Users/a/ai/worktrees/andy-write-r7-dev`, code `830bf543a5ef346edb3877c5ab99f6c1253afcf0`, Dev-only `ANDY_WRITE_ENV=dev ANDY_WRITE_SEARCH_INTENT_R7_ENABLED=1`.

**Technical outcome: PASS / BLOCK control flow verified against real observed evidence. Owner acceptance of these additional scenarios: PENDING.** Only the prior real REVIEW-path UAT was explicitly approved by Andy. Nothing here authorizes a merge or release.

## 1. Real evidence-qualified positive case — prebrief PASS

**Keyword:** `tpe vs silicone sex doll`. OpenSEO US / English / mobile, November 20, three reads; `bestPosition` is the observed per-read position, **never** the merged `rank`.

- The **unfiltered** merged OpenSEO capture contains 19 organic rows and grades `provisional / REVIEW` because 7 low-stability/other rows retain unclear relevance. This status is preserved; it was **not silently relabeled** verified.
- Applying the explicit objective filter **`seenIn >= 2`** yields all 8 repeatedly observed organic results. Their actual pages and final publisher URLs were independently inspected; 7 are on-topic, direct, HTTP 200, 1 French-language / mini-doll page is not suitable for the English full-size comparison.
- The canonical `grade_serp_evidence.py` run on the **complete 8-row, independently reviewed stable cohort** yields `verified / PASS-ELIGIBLE`: 7 on-topic, 7 stable on-topic, 7 publisher final URLs, 0 unclear. The 11 excluded one-read rows and original unfiltered result are retained privately. This is **not** proof of a complete or individually ordered Google top ten.
- Validated V1.1 `prebrief` contract: `evidence.status=verified`, `intent.primary=commercial-investigation`, 6 comparison pages + 1 on-topic forum, `audit.verdict=Unassessable` (no real Owner article), `gate=PASS`. Exact keyword and frozen synthetic test scope were preserved. The result authorizes **only Dev Source/Outline progression**, never publishing.
- Representative independently read publisher pages: [Sex Toy Insider material comparison](https://www.sextoyinsider.com/tpe-vs-silicone-love-doll/) and [AcmeJoy material comparison](https://acmejoy.com/blogs/all-blog/which-material-is-more-suitable-for-sex-dolls). Complete result-level evidence is in private `intent_contract.json`.

**Real Dev CLI result:** exit **0**, saved decision `PASS / SOURCE`; `research-pack.json`, `source-catalog.json`, `outline.md` and `run-manifest.json` exist. **No `article-v1.md`**. Manifest `wordpress_status=UNTOUCHED`. There were 5 reference segments and 3 outline sections, but their input is an explicitly **synthetic comparative source fixture**, not published editorial work.

**Idempotency:** a second complete CLI run also exited 0. There was still **one** decision receipt; `outline.md` SHA-256 was unchanged, and the input contract/report hashes matched its receipt. Frozen synthetic scope fingerprint: `06ccc61e7a0f4fbff1e23372d799365e75e68c39dddd26f00d7c0e5a4318c9ce`.

## 2. Real public benchmark negative case — audit Mismatch

**Target keyword:** `how to clean a sex doll`. **Actually inspected public page:** [Innerbody — Best and Most Realistic Sex Dolls in 2026](https://www.innerbody.com/best-sex-dolls). It leads with top picks, manufacturers, cost and customization comparisons. Its incidental care references do not answer an existing owner's primary cleaning-how-to job.

The live article was fetched read-only to a private ~55k-character extract. V1.1 `audit.article_page_type=review-list`, `audit.verdict=Mismatch`, `evidence.status=provisional` (original cleaning SERP still has only two independently qualified results), therefore **`gate=BLOCK`**. No claim of verified evidence was made for this case.

**Real Dev CLI result:** exit **2**, `Search Intent BLOCK: QC returned BLOCK`, saved decision `BLOCK / STOP`; Research present, Source catalog / Outline / Draft all absent; `publish_ready=false`. On retry, decision receipts remained **one**, the contract/report SHA-256 checks passed, and the frozen synthetic scope fingerprint stayed `5c271a331bd9c5fa6bc6507c804f960704403e0176250232e601d3302692f6c1`.

This is a **public benchmark fixture**, not an Owner-supplied article. No third-party page or PairDoll/Mary content was modified.

## 3. Direct comparison of observed Dev behavior

| Case | Evidence status | Editorial audit | Gate / CLI exit | Research | Source | Outline | Draft / Production |
|---|---|---|---|---|---|---|---|
| Real stable TPE-vs-silicone **cohort** | `verified` on the 8-row reviewed cohort; full unfiltered capture remains `provisional` | `Unassessable` prebrief | `PASS` / 0 | Created | Created | Created | No draft; WP `UNTOUCHED` |
| Real public Innerbody buying-list vs cleaning how-to | `provisional` | `Mismatch` | `BLOCK` / 2 | Created | Absent | Absent | No draft; no publishing path reached |
| Three previously tested real OpenSEO keywords | `provisional` | `Unassessable` prebrief | `REVIEW` / 2 | Created | Absent | Absent | No draft; no publishing path reached |

## 4. Test, provenance and rollback

- US Mac mini Dev runtime: **199 / 199 Python tests PASS**; `scripts/check_owner_rules.py` **Owner P0 PASS**; canonical V1.1 self-tests **9 / 9 validator + 5 / 5 grader PASS**.
- Private ignored root: `/Users/a/ai/worktrees/andy-write-r7-dev/.runs/r7-real-cases-20261120/`. Cases: `pass_tpe_vs_silicone`, `mismatch_innerbody_vs_cleaning`. Each has `job.json`, validated `intent_contract.json`, `intent_report.md`, and workflow decisions/receipts.
- Full unfiltered raw SERP, the 8-row reviewed cohort and benchmark article extract remain private, outside GitHub. No secrets, customer data, article originals or raw provider event records are committed.
- The R7 feature flag remains **off by default**, only valid when `ANDY_WRITE_ENV=dev`. The base before R7 was `a89b2dca11537ccf9d35e84eeae1ce388cacba37`; rollback is disable the flag or revert the isolated feature branch. No `main` merge, PR, authenticated Dev web UI, or Production release was performed.

## 5. Exact Owner acceptance requested

- [x] Real REVIEW path — **Owner explicitly signed PASS on November 20**.
- [x] Positive stable reviewed cohort — **Dev technical PASS**; no real authored article and no publication.
- [x] Negative public benchmark Mismatch — **Dev technical PASS**, deterministic `BLOCK`.
- [x] Scope, hashes, idempotent retries, absence of Draft/Production writes checked.
- [ ] **Andy signs these positive/negative Dev cases after reviewing limitations, especially stable cohort vs unfiltered raw SERP.**
- [ ] **Owner chooses whether CLI evidence is adequate for R7.4 closure or an authenticated read-only Dev UI is required.** The current application has no web dashboard, and no Dev URL is claimed.

**Suggested narrow signoff, if acceptable:** “R7 真实 PASS / Mismatch Dev UAT PASS，接受稳定样本的限定验证范围；继续最终 R7 收尾。未授权 GitHub main 合并或 Production 发布。”
