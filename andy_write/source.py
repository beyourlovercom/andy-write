"""Source catalog and evidence ledger; distinct unverified/verified semantics."""
from __future__ import annotations
import re
from .io import hashtext, now

TOPICS = {
  "arrival": ("arriv", "tracking", "deliver", "production", "shipping", "factory photos", "order"),
  "unboxing": ("unbox", "box", "tape", "foam", "package", "wrapped", "carton", "plastic"),
  "handling": ("lift", "weight", "heavy", "thigh", "shoulder", "back straight", "legs", "move"),
  "inspection": ("inspect", "damage", "tear", "abrasion", "wires", "finger", "joint", "loose", "check"),
  "accessories": ("accessor", "kit", "spray", "sponge", "glue", "powder", "cotton", "oil"),
  "cleaning": ("clean", "bath", "wash", "soap", "rinse", "dry", "towel", "stain")
}
UNSAFE_ADVICE = ("heat gun", "hot knife", "baby oil", "mineral oil", "cornstarch", "super glue",
                 "body lotion", "ninety-degree", "90-degree")

def topic_for(paragraph: str) -> str:
    text = paragraph.lower()
    scores = {name: sum(text.count(w) for w in keywords) for name, keywords in TOPICS.items()}
    return max(scores, key=scores.get) if max(scores.values()) else "other"

def classify(source_text: str, reference_url: str) -> dict:
    paras = [p.strip() for p in re.split(r"\n\s*\n", source_text) if len(p.strip()) > 25]
    items = []
    for idx, p in enumerate(paras, start=1):
        txt = re.sub(r"</?b>|</?strong>", "", p).strip()
        items.append({"id": f"SEG-{idx:03}", "source_id": "SRC-REF-001", "source_url": reference_url,
                      "paragraph_number": idx, "topic": topic_for(txt), "sha256": hashtext(txt),
                      "excerpt": txt[:260], "requires_material_verification":
                      any(term in txt.lower() for term in UNSAFE_ADVICE)})
    groups = {name: [s["id"] for s in items if s["topic"] == name] for name in [*TOPICS, "other"]}
    return {"source_id": "SRC-REF-001", "source_type": "owner_supplied_reference",
            "source_url": reference_url, "source_sha256": hashtext(source_text),
            "collected_at": now(), "segments": items, "clusters": groups,
            "warning": "User supplied prose is writing reference, not automatically verified product guidance."}

def evidence(research_pack: dict, catalog: dict) -> dict:
    targets = [
      ("FTC-RECORDS", "Keep order confirmations and delivery information available when resolving an online order issue", "consumer.ftc.gov"),
      ("NIOSH-LIFTING", "Bulky or awkward objects can make handling risky; plan a lift and use assistance or lifting equipment", "cdc.gov"),
    ]
    claims = []
    for code, statement, domain in targets:
        candidates = [s for s in research_pack.get("sources", []) if domain in s.get("url", "")]
        # A live fetch is a real URL check, not proof that each sentence has been verified.
        claims.append({"id": code, "statement": statement,
                       "source_ids": [s["id"] for s in candidates if s.get("status") == "retrieved"],
                       "status": "needs_editorial_verification",
                       "notes": "Validate the exact statement against cited source before publishing."})
    return {"reference_id": catalog["source_id"], "claims": claims, "generated_at": now()}
