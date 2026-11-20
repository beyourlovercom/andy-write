# R8.1 — KissSelf real-public-article reverse-QC frozen baseline

**Captured / audited:** 2026-11-20 (Asia/Hong_Kong). **Status:** REAL SOURCE CAPTURE + DETERMINISTIC QC **TECHNICAL PASS**; editorial case labels and Search Intent SERP verification **PENDING**. **No WordPress, author, article, model or Production writes.**

## 1. Locked benchmark scope and source roles

- **Benchmark ID:** `R8-KS-26268-CURRENT-20261120`.
- **Source:** KissSelf public WordPress post **26268**, [How to Boost Intimacy Using Waterproof Toys in the Shower](https://kissself.com/how-to-boost-intimacy-using-waterproof-toys-in-the-shower.html); [public REST record](https://kissself.com/wp-json/wp/v2/posts/26268).
- **Publication:** 2025-12-26 07:47:52; **public revision:** 2026-10-04 15:03:30. The actual **December 2025 original is NOT verified**; all findings concern the current 2026 revision.
- **Primary subject:** consensual **adult** couple intimacy and choosing, using and caring for waterproof adult toys **in a shower**. A smart fitness/health ring or a child flotation device is not an interchangeable product identity.
- **Source roles:** KissSelf = independently observed **public QC benchmark**, **not** Owner article, owner-approved source text or manufacturer evidence. Outbound links = candidate claim support requiring independent relevance review. Existing PairDoll unboxing draft = historical **cross-topic structural control only**, not a matched quality A/B.
- **Query/market limits:** No Owner-supplied target search keyword, market-specific SERP export or owner article; Google organic position, search intent majority, rankings and a full `Match` verdict are **UNASSESSABLE / not claimed**. No scope amendment or publication approval follows from this baseline.

## 2. Actual read-only collection and reproducibility

On US Mac mini, isolated clean Dev worktree `/Users/a/ai/worktrees/andy-write-r7-dev` (runtime code `830bf543`, identical QC analyzer to merged `main` `57be5675`), executed the existing versioned tools:

```sh
python3 scripts/fetch_public_wp_benchmark.py --site https://kissself.com --slug how-to-boost-intimacy-using-waterproof-toys-in-the-shower --out .runs/r8-kissself-20261120/kissself_current_wp.json
python3 -m andy_write qc-profile --post-json .runs/r8-kissself-20261120/kissself_current_wp.json --draft examples/output/pairdoll-unboxing-editor-quality-v2.md --draft-url https://pairdoll.com/ --report .runs/r8-kissself-20261120/qc_profile.json
```

Both actual commands completed successfully on **2026-11-20**; the CLI returned **`STRUCTURAL_REVIEW_REQUIRED`**, never article quality PASS. Private ignored snapshot JSON SHA-256: `6ae8aa3dd2e8929d3e38e42abd21175a8a4fb3c42a235256c56740214c32ffd7`. Parsed `content.rendered` SHA-256 reported by analyzer: `f691c7f330bef6e15589c68b2ef231fabfc7a393f8f00f9acb38eb5c84f19af9`. Private raw article and full profile stay in `.runs/r8-kissself-20261120/` **outside GitHub**.

The pre-existing cross-topic structural control is displayed only because `qc-profile` requires a draft argument. Its counts **must not** be interpreted as a quality superiority test or as an authorized rewriting reference.

## 3. Actual machine-observed baseline — current public revision only

| Metric | Exact derived finding |
|---|---:|
| Approximate words from rendered HTML (TOC included) | 5,938 |
| H2 / H3 / H4 | 7 / 27 / 10 |
| Tables / paragraph tags / list items | 9 / 109 / 116 |
| Images in WP article HTML / with nonempty Alt | 2 / 2 |
| Internal / external link instances | 59 / 16 (15 external domains) |
| Pattern-flagged paragraphs | **49 of 109** |
| Material/safety reason hits | 39 |
| Broad/universal phrasing reason hits | 19 |
| Verified factual errors or human editorial labels | **Not measured; 0 verified labels** |

The 39 and 19 reason-category counts **overlap**; 49 are only heuristic REVIEW candidates, not 49 proven errors. Heading counts, links, word count and image counts do not establish usefulness, Google rankings or correctness. Table of contents and embedded formatting can inflate HTML list/word metrics.

## 4. First five observed editorial QC candidates (AI/operator triage, NOT human gold labels)

| ID / priority | Source section and observed issue | Existing checker behavior | R9 required reusable gate |
|---|---|---|---|
| **KS-01 P0** | [Couples' Rings](https://kissself.com/how-to-boost-intimacy-using-waterproof-toys-in-the-shower.html/#Couples_Rings) describes metal health-tracking wearable features, 5ATM and >10-day battery life within an adult intimate-toy category. **Likely unrelated product-class contamination.** | No product-identity/context semantic validator; generic material-word alerts cannot resolve the mismatch. | `andy-write-quality` + `andy-write-source`: subject / product-class / table-cell coherence against frozen task scope |
| **KS-02 P0** | [Safety in Wet Environments](https://kissself.com/how-to-boost-intimacy-using-waterproof-toys-in-the-shower.html/#Safety_in_Wet_Environments) diverts into baby neck floats and child supervision. Linked [CDC drowning prevention](https://www.cdc.gov/drowning/prevention/index.html) discusses drowning, **not adult toy or manufacturer waterproof safety**. | No section-level subject-drift or source-role mismatch verdict. | `andy-write-quality`: exclude tangential safety material from primary adult user job and flag source-purpose drift |
| **KS-03 P1** | [Cleaning and Care](https://kissself.com/how-to-boost-intimacy-using-waterproof-toys-in-the-shower.html/#Cleaning_and_Care) recommends a general household vinegar treatment for plastic surfaces and links a baby bath-toy cleaning URL, without matching a specific adult toy/model manual. **Claim-to-source suitability requires checking.** | Material/safety risk patterns exist; cannot validate that the cited page supports the product-specific recommendation. | `andy-write-source` + `andy-write-quality`: sentence → exact source passage → manufacturer/model evidence or `NEEDS_REVIEW` |
| **KS-04 P1** | [Massage Wands](https://kissself.com/how-to-boost-intimacy-using-waterproof-toys-in-the-shower.html/#Massage_Wands) has generic IPX7/submersion and runtime/battery comparison claims without an unambiguous manufacturer's exact model. **Device-specific proof pending.** | A safety-term flag is only a candidate, not citation fit, product identity or spec verification. | Block unsupported exact device specs and allow genuine model-specific sources |
| **KS-05 P2** | [Suction Toys](https://kissself.com/how-to-boost-intimacy-using-waterproof-toys-in-the-shower.html/#Suction_Toys) price table includes an unnamed “Limited Time Offer” price row and time-sensitive prices without a dated comparable offer audit. | Counts tables; does not grade product-row identity or price freshness. | Conditional structured-table source/validity check; no numerical SEO quotas |

**Important confidence boundary:** KS-01/02 are strong *topic-mismatch candidates*, not adjudicated Owner/editor labels. KS-03/04/05 are evidence/freshness questions, not substantiated claims that the products are dangerous or facts false. Failed third-party link fetches must remain **unverified**, never counted as proof of a claim.

## 5. Existing Skills caught vs missed

- **Working, observed:** exact public WP article identity and revision, rendered-content snapshot hash, structural metrics, 49 pattern REVIEW flags, link-domain inventory, six general improvement tickets and `STRUCTURAL_REVIEW_REQUIRED`; no LLM/Codex, WordPress or image generation.
- **Not implemented as an independent semantic verdict:** primary product-class swap (KS-01), unrelated audience/task detour (KS-02), passage-level link relevance and exact manufacturer model support (KS-03/04), offer freshness and anonymous table rows (KS-05).
- **Not claimed:** independently scored recall/precision, 49 factual errors, SEO ranking effect, current localized Search Intent PASS, independent human gold-standard labels, or higher quality of the unrelated PairDoll output.

## 6. Frozen R9 test contract (next change only after separate R9 implementation)

1. **P0 coherence:** detect/flag a product-type or audience switch inside an otherwise on-topic subsection **without changing the frozen Owner task**, explain the affected section; avoid forcing Mismatch for a brief, relevant mention.
2. **P1 source-to-claim:** label product-specific waterproof, compatibility, cleaning and material claims as `SUPPORTED` only with an independently checked relevant exact source; otherwise `NEEDS_REVIEW`.
3. **P2 useful format:** detect anonymous product/price rows and stale time-sensitive offers, never require a fixed H3 count, tables, words or outbound links.
4. **Review policy:** AI findings remain candidates. A real human/editor must validate the case labels before calculating false positives/negatives or tuning thresholds. No competitor text copying into a new article.

**R8 acceptance:** capture, hashed reproducible structural baseline and first actionable QC queue **COMPLETE**; human truth labels **PENDING**. R9 Skill implementation, PR review/merge and any Production work are **not authorized by this R8-only baseline**.
