# R7 Search Intent QC — isolated Dev integration contract

Status: **development candidate only**. Not merged, deployed, or Owner-UAT approved.

## R7.0 verified baseline (2026-11-19)

- Authoritative repository: `beyourlovercom/andy-write`.
- Runtime branch: `feat/r0-r2-research-writing-mvp`; audited latest source `a89b2dc`.
- GitHub `main` `ed831a5` contains Owner policy/tests, **not** the full CLI runtime.
- US Mac mini CLI workspace: `/Users/a/ai/andy-write`, clean at `3b2e987` when inspected;
  remote runtime branch had two later CI-only commits (`a89b2dc`).
- Real workflow: `andy_write/__main__.py:run()` calls `ensure_article_scope`, then
  `cached_research`, `classify` (Source), `evidence`, `section_plan` (Outline),
  and writes a prompt. `write()` is separately callable.
- Frozen scope: `andy_write/article_scope.py:ensure_article_scope()` persists
  `.runs/_article_scopes/<job_id>.json` and validates `scope_fingerprint`.
- Artifacts: `andy_write/io.py:outdir()` restricts to gitignored `.runs`.
- Existing process is a Python CLI; no authenticated Andy Write web Dev endpoint
  was established. A new UI or service is **not** implied by this branch.
- Separate historical Draft PR #5 covers KissSelf reverse QC; R7 does not merge it.

## R7.1 contract and Owner P0 rules

Search Intent V1.1 stays the decision producer. R7 does **not** infer a SERP,
label an article, invoke an LLM, rewrite a user document, or reimplement the
editorial classifier. A human/Skill run first deposits the following private
files in the exact job output directory:

1. `.runs/<job_id>/intent_contract.json` — validated Search Intent v1 contract.
2. `.runs/<job_id>/intent_report.md` — nonempty human-readable evidence report.

The job config must have an exact Owner-approved `target_keyword`, an explicit
`brand_domain` and `search_intent_scope` with `audience`, `market_country`,
`language`, `device`. No market is inferred from operator location.
`intent_contract.scope.owner_scope_contract_id` must equal the immutable
`scope_fingerprint` returned by `scope-init`. The keyword, brand domain and all
four intent scope fields must match **exactly** (site matching is case-insensitive).
Owner P0 `article_scope` remains immutable and takes precedence over SERP data.

The canonical V1.1 Skill files have been vendored **unchanged** for reproducible
validation (personal Skill source ID `6afeb909dcf0819189180369ed781e7b`):

| File | SHA-256 |
|---|---|
| `skills/andy-write-search-intent/SKILL.md` | `b74d8ab9f556712ce00dd734145552e060d922c17e65216a34c33b6d5bed3863` |
| `skills/andy-write-search-intent/scripts/validate_contract.py` | `0d8c026f3adcbb14bc762fef42a73c5e07b0afc5631152c64fabacedabc918fe` |
| `skills/andy-write-search-intent/scripts/grade_serp_evidence.py` | `0bd95bf573109dc180d32cbed1738d72d027f642ecbdc11f6de335c881d2eb0c` |

Decision matrix:

| Skill handoff | R7 action | Subsequent command |
|---|---|---|
| Schema valid + `PASS` + exact Owner scope | Continue to Source/Outline in Dev only | Allowed; **not publication approval** |
| `REVIEW` (including provisional evidence or Partial fit) | Record STOP and reason | No Source/Outline or `write` |
| `BLOCK` (including Mismatch/blocked evidence) | Record STOP and reason | No Source/Outline or `write` |
| Missing/invalid contract/report or Owner conflict | Fail-closed BLOCK | No Source/Outline or `write` |

There is deliberately **no self-service Owner override** in this pilot. An
exception requires a separately authorized Scope Contract revision and an
auditable new Skill contract. Evidence-level `provisional` never gains PASS
through an override. Never change `target_keyword` to fit the observed SERP.

For every evaluated input, `search-intent-decision.json` records the current
decision, source and report SHA-256, Owner fingerprint, stage, timestamp, and
`publish_ready=false`. Distinct evidence revisions are retained under
`search-intent-decisions/`; retrying identical input creates no duplicate receipt.

## R7.2 feature flag and boundaries

Disabled by default. For an isolated, intentional local Dev CLI run only:

```sh
ANDY_WRITE_ENV=dev ANDY_WRITE_SEARCH_INTENT_R7_ENABLED=1 \
  python3 -m andy_write run --job path/to/dev-job.json
```

When enabled, the gate runs **after Research, before Source/Outline**. It also
guards direct `write` and downstream job-based commands from consuming stale
artifacts after a REVIEW/BLOCK. Disabled path follows the former workflow.
Production code/config, WordPress data and already-approved article sources are
untouched. No Dev web server is built by this change.

## R7.3 evidence and R7.4 outstanding

- 12 new offline deterministic tests cover Dev guard, PASS, REVIEW, Mismatch,
  keyword/site/market/Owner fingerprint, redirected SERPs, official-domain
  lookalikes, fake PASS, missing files, retries, workflow stop and stale-write bypass.
- Canonical Skill self-tests: validator 9/9 and grader 5/5 PASS.
- All runtime tests and Owner P0 policy validator must pass before PR review.
- The tests use **synthetic fixtures**, not observed live SERP evidence.
- Real Dev-only end-to-end scenarios, actual UI progression and a working
  authenticated Dev URL remain **unverified**. A CLI cannot be described as a
  working authenticated web UI. Owner UAT is still required.

Rollback: leave `ANDY_WRITE_SEARCH_INTENT_R7_ENABLED=0` or revert this isolated
branch to `a89b2dca11537ccf9d35e84eeae1ce388cacba37`. No merge into
`main`, no Production deployment, no content/writer mutation is authorized.
