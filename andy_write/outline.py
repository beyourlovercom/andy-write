"""R2 outline: question-based sections with traceable source topics."""
from __future__ import annotations
from .source_outline import source_hierarchy_plan

UNBOXING_SECTIONS = [
  ("What should you prepare before the package arrives?", "arrival",
   "Compare the exact order confirmation with options, delivery window and size; clear the route and prepare a supported surface."),
  ("What should you check before you open the carton?", "arrival",
   "Record carton and label condition, protect order details and keep packaging until inspection is complete."),
  ("How can you unpack and move the doll safely?", "handling",
   "Follow product-specific handling guidance, use an assistant for heavy or awkward loads, never lift by delicate parts."),
  ("What belongs on the first inspection checklist?", "inspection",
   "Compare components and accessories with order, observe accessible surfaces and fittings without forcing joints."),
  ("What if something is missing or damaged?", "inspection",
   "Photograph observations, preserve originals, contact seller without unapproved repair or cleaning that erases evidence."),
  ("When should you clean and set up the doll?", "cleaning",
   "Check material and manufacturer-specific care directions, do not generalize oils, solvents, heat tools or glue.")
]
TOPIC_TITLES = {
 "arrival": "What should you confirm before delivery?",
 "unboxing": "How should you unpack the package?",
 "handling": "How can you handle the product safely?",
 "inspection": "What needs checking before first use?",
 "accessories": "Which accessories or supplies are relevant?",
 "cleaning": "Which care steps do the manufacturer instructions allow?"
}

def section_plan(job: dict, catalog: dict, original: str | None = None) -> list[dict]:
    if job.get("outline_mode") == "source_hierarchy_v1":
        if not isinstance(original, str):
            raise ValueError("Original complete article required for source hierarchy outline")
        return source_hierarchy_plan(job,catalog,original)
    if "unboxing" in job["topic"].lower():
        raw = UNBOXING_SECTIONS
    else:
        raw = [(TOPIC_TITLES[t], t, f"Answer reader questions about {t} using reference material.")
               for t in TOPIC_TITLES if catalog["clusters"].get(t)]
    if not raw:
        raise RuntimeError("Source contains no topic-bearing sections; cannot build grounded outline")
    return [{"id": f"SEC-{i:02}", "heading": title, "topic": topic, "brief": brief,
             "reference_segment_ids": catalog["clusters"].get(topic, [])[:8]}
            for i, (title, topic, brief) in enumerate(raw, start=1)]

def markdown_outline(job: dict, sections: list[dict], ledger: dict) -> str:
    if job.get("outline_mode") == "source_hierarchy_v1":
        return source_hierarchy_markdown(job, sections, ledger)
    out = [
      f'# {job["target_title"]}', '',
      '[image: existing or Owner-supplied asset ONLY; never generate]', '',
      '## Introduction (three-part editorial plan)', '',
      '1. **Opening:** name the delivery-day reader problem without generic promotional language.',
      '2. **Concise answer:** one natural bold paragraph addressing the main checklist.',
      '3. **Transition:** explain what the article covers and what is model/manufacturer-specific.', '',
      '## Table of Contents', ''
    ]
    for item in sections:
        out.append(f'- [{item["heading"]}](#{item["id"].lower()})')
    out += ['', '## Claim slots (editorial, not publishable as placeholders)', '']
    for claim in ledger["claims"]:
        out.append(f'[Claim: {claim["id"]}] {claim["statement"]} — {claim["status"]} (do not assert without verification)')
    out.append('')
    for idx, item in enumerate(sections):
        out += [f'## {item["heading"]}', f'<!-- {item["id"]}: {item["topic"]}; source segments: {", ".join(item["reference_segment_ids"])} -->', '',
          f'1. Opening: {item["brief"]}',
          '2. **Direct answer:** give a concrete answer in natural US English; not mechanical three-paragraph padding.',
          '3. Detail: explain decisions, exceptions and limits based on the actual source.',
          '[image: optional existing or Owner-supplied asset; generation prohibited]', '']
        if idx == 1 or idx == 3:
            out.append(f'[Claim: {ledger["claims"][0 if idx==1 else 1]["id"]}] (verify source before copywriting)\n')
    out += ['## Conclusion', '', 'Close with the practical delivery-day decision, not a generic sales pitch.', '',
            '## Link plan', '', '- Internal: existing PairDoll first-time owner guide (verify URL).',
            '- External: FTC shopping records, CDC/NIOSH ergonomic handling (verify relevance; do not link to shops).', '']
    return '\n'.join(out)


def source_hierarchy_markdown(job:dict,sections:list[dict],ledger:dict)->str:
    """Instructional plan from genuine Owner source headings, not benchmark prose."""
    out=[
        "# "+job["target_title"],"",
        "## Introduction planning",
        "Directly answer the reader intent using the provided original article.",
        "Do not invent product specifications, safety guarantees or testimonials.","",
        "## Source-grounded table of contents","",
    ]
    for item in sections:
        out.append("- "+item["heading"])
    out += ["","## Per-section source evidence and semantic review",""]
    for item in sections:
        out += [
            "## "+item["heading"],
            "Source H2: "+item["source_heading"],
            "Evidence status: "+item["source_segment_status"]+
                "; linked original segments: "+(", ".join(item["reference_segment_ids"]) or "NONE"),
            "Editorial mode: rewrite Owner original, not compose from competitor benchmark.",
        ]
        for h3 in item["subheadings"]:
            out.append("### "+h3)
            out.append("Review the source for accuracy and safety. Retain, revise or omit only with documented reason; never generalize.")
        if item["manufacturer_material_review"]:
            out.append("MANUFACTURER CHECK REQUIRED: source section contains product-care or safety-related advice; never assert as universal.")
        out += ["","No generated images or videos; existing media must be reviewed.",""]
    out += [
        "## Conclusion","",
        "Condense source-grounded decisions without unsupported claims.","",
        "## Independent QC release gates","",
        "- Full source coverage and source-to-draft fidelity review.",
        "- Verify material/manufacturer advice and link-to-claim relevance.",
        "- Do not copy benchmark article structure mechanically or match its word count.",
        "- Owner editorial approval before any publishing.",
    ]
    return "\n".join(out)+"\n"
