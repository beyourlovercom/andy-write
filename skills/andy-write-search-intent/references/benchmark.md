# R3 Search Intent benchmark — exploratory snapshot, 2026-11-19

**Method:** public web-search results and on-page reading. Not a localized Google US organic top-10 export. All labels are provisional hand-annotated cases, not an independent blinded model score; rerun before publishing. The public sources are the **articles under test**, not recommendations for a writer to copy.

| Case | Target query | Page under test | Observed task / expected verdict |
|---|---|---|---|
| B01 | `how to clean a sex doll` | https://mmidoll.com/pages/how-to-clean-a-sex-doll | Step-by-step care guide; **Match**: practical cleaning/drying steps and material distinctions. |
| B02 | `tpe vs silicone sex doll` | https://www.dolladvisor.com/tpe-vs-silicone/ | Comparative buyer guide; **Match**: price, upkeep, material tradeoffs. |
| B03 | `best realistic sex dolls 2026` | https://www.innerbody.com/best-sex-dolls | Best-of ranked shortlist; **Match**: comparison/list format. |
| B04 | `full size silicone sex doll buy online` | https://yjldoll.com/collections/full-silicone-series | Filterable product collection with prices; **Match**: transactional category. |
| B05 | `sex doll discreet shipping how does it work` | https://doll.shop/en/knowledge-base/discreet-ordering/ | Privacy/shipping explainer; **Match**: answers packing and arrival questions. |
| B06 | `sex with sexual doll` | https://friskybusiness.sg/blogs/sex-dolls/5-things-to-think-about-before-having-sex-with-a-sex-doll | First-use guide, but preparation/aftercare dominate; **Partial**: may under-answer anticipated personal experience questions. Ambiguous wording; do not overstate certainty. |
| B07 | `how to clean a sex doll` | https://friskybusiness.sg/blogs/sex-dolls/5-things-to-think-about-before-having-sex-with-a-sex-doll | Correct guide type but cleaning is a secondary topic; **Partial**, not Mismatch. |
| B08 | `sex doll reviews real experience forum` | https://dollforum.com/forum/viewtopic.php?p=2527480 | Genuine owner's specific-product review; **Partial** for broad generic query because it is not a broad review directory. |
| B09 | `tpe vs silicone sex doll` | https://yjldoll.com/collections/full-silicone-series | Product grid cannot answer a balanced TPE/silicone comparison; **Mismatch**. |
| B10 | `realdoll official website` | https://www.dolladvisor.com/tpe-vs-silicone/ | Competing informational page for a navigational brand query; **Mismatch**. Official target found at https://www.realdoll.com/. |

## R3 expected controls

- Five positive, three `Partial`, two `Mismatch`; preserve these class distinctions in the skill output.
- `B06` and `B07` guard against the common failure of treating every article-topic discrepancy as a page-type mismatch.
- `B09` guards against recommending extra paragraphs instead of a different page type.
- `B10` guards against targeting a competitor's branded navigational query.
- For a generic search method, all cases must disclose `provisional` evidence and set unknown SERP features to `unknown`.
- A successful internal schema/unit test cannot replace a blind editorial evaluation or a localized Google SERP export. Do not declare independent R6 UAT PASS on this benchmark alone.

## Public Skills compared (R4)

| Source | Useful method | Limitation / V1 correction |
|---|---|---|
| https://github.com/search-atlas-group/amm-founding-circle/blob/main/skills/serp-intent-decoder/SKILL.md | SERP-first intent categorization, mixed intent, page-type filtering | Word-count recommendations and unverified AI Overview/CTR or unwinnability projections can overstate evidence. V1 uses topic depth and no unsupported numeric claims. |
| https://github.com/RomeoSEO/seo-skills/blob/main/skills/search-intent-match/SKILL.md | Separate Match / Partial / Mismatch; compare article with observable page type, stage and next click | Requires real source and target-market SERP; do not force a definitive verdict on partial, unlabeled search evidence. V1 adds `Unassessable`, evidence status and structured contract. |

Do **not** claim that either public Skill package was installed or executed via its own runtime. These examples follow their published procedures using accessible search evidence and manual cross-checks.
