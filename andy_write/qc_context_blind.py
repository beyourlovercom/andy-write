"""Private, two-stage blind review of frozen public-context QC receipts.

Stage 1: reviewers label *every source section* before seeing either model's
candidates. Stage 2: only after source labels are sealed, show shuffled,
version-masked paired notices. This tool never manufactures human labels.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import json
import secrets

from .qc_context import SectionReader, validate_contract
from .io import hashtext

VERSION = "andy-write-context-qc-blind/v1"
CODES = frozenset({
    "PRODUCT_OR_AUDIENCE_DRIFT_REVIEW",
    "MODEL_SPEC_PROVENANCE_REVIEW",
    "CLEANING_CLAIM_SOURCE_REVIEW",
    "PRICE_OFFER_FRESHNESS_REVIEW",
})


def _digest(value: object) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode()).hexdigest()


def build_source_packet(cases: list[tuple[dict, dict]]) -> dict:
    """Create private, complete section inventory, with NO machine predictions."""
    if len(cases) < 2:
        raise ValueError("At least two independent frozen articles required")
    sources, items = [], []
    seen_sources = set()
    for source, contract in cases:
        validate_contract(contract, source)
        pid = source["id"]
        if pid in seen_sources:
            raise ValueError("Duplicate frozen source")
        seen_sources.add(pid)
        source_sha = hashtext(source["content"]["rendered"])
        sources.append({
            "post_id": pid, "url": source["link"],
            "modified": source["modified"], "content_sha256": source_sha,
            "source_role": contract["source"]["source_role"],
            "benchmark_id": contract["benchmark_id"],
        })
        reader = SectionReader()
        reader.feed(source["content"]["rendered"])
        grouped = defaultdict(list)
        for block in reader.blocks:
            grouped[(block["heading"], block["anchor"])].append(block)
        for (heading, anchor), blocks in grouped.items():
            key = (pid, heading, anchor)
            items.append({
                "id": "SRC-" + _digest(key)[:16], "post_id": pid,
                "heading": heading, "anchor": anchor,
                "url": source["link"] + ("#" + anchor if anchor else ""),
                # Remains ONLY in ignored .runs; never publish or commit this packet.
                "frozen_section_text": "\n".join(b["text"] for b in blocks),
                "block_hashes": [hashtext(b["text"]) for b in blocks],
            })
    items.sort(key=lambda x: (x["post_id"], x["anchor"], x["heading"]))
    identity = {"sources": sources, "section_ids": [i["id"] for i in items]}
    return {
        "schema": VERSION + "/source-only", "sources": sources,
        "source_lock": _digest(identity), "issue_codes": sorted(CODES),
        "instructions": "Independent source-only review. Mark every section; [] means no actionable QC review. Do not open any machine candidate or pair packet until both reviewers seal labels. Labels mean review-worthy gap, NOT proven factual falsehood.",
        "sections": items, "human_labels_present": 0,
        "status": "WAITING_FOR_TWO_INDEPENDENT_EDITORS",
    }


def blank_source_review(packet: dict) -> dict:
    return {"schema": VERSION + "/source-labels", "source_lock": packet["source_lock"],
            "reviewer_id": None,
            "sections": [{"id": s["id"], "issue_codes": None, "rationale": None}
                         for s in packet["sections"]]}


def _validate_source_labels(packet: dict, review: dict) -> dict:
    if review.get("schema") != VERSION + "/source-labels" or review.get("source_lock") != packet["source_lock"]:
        raise ValueError("SOURCE_LOCK_MISMATCH")
    if not isinstance(review.get("reviewer_id"), str) or len(review["reviewer_id"].strip()) < 2:
        raise ValueError("Real reviewer identity required")
    rows = review.get("sections")
    expected = {s["id"] for s in packet["sections"]}
    if not isinstance(rows, list) or len(rows) != len(expected):
        raise ValueError("Every source section must be independently labeled")
    labels = {}
    for row in rows:
        codes = row.get("issue_codes")
        if (row.get("id") not in expected or row["id"] in labels
            or not isinstance(codes, list) or len(codes) != len(set(codes))
            or any(c not in CODES for c in codes)):
            raise ValueError("Missing, duplicate, or invalid human section label")
        if codes and (not isinstance(row.get("rationale"), str)
                      or len(row["rationale"].strip()) < 12):
            raise ValueError("Positive human labels need specific rationale")
        labels[row["id"]] = frozenset(codes)
    if set(labels) != expected:
        raise ValueError("Missing source section label")
    return labels


def seal_source_gold(packet: dict, review_a: dict, review_b: dict,
                     owner_adjudication: dict | None = None) -> dict:
    """Require 2 separate human reviewers; fail closed on unresolved conflicts."""
    a, b = _validate_source_labels(packet, review_a), _validate_source_labels(packet, review_b)
    if review_a["reviewer_id"].strip().casefold() == review_b["reviewer_id"].strip().casefold():
        raise ValueError("Two distinct human reviewers required")
    disagreements = sorted(i for i in a if a[i] != b[i])
    if disagreements:
        if (not isinstance(owner_adjudication, dict)
            or not owner_adjudication.get("owner_id")
            or owner_adjudication.get("source_lock") != packet["source_lock"]):
            raise ValueError("OWNER_ADJUDICATION_REQUIRED: " + ",".join(disagreements))
        decisions = owner_adjudication.get("decisions")
        if (not isinstance(decisions, dict) or set(decisions) != set(disagreements)
            or any(not isinstance(x, list) or len(x) != len(set(x))
                   or any(code not in CODES for code in x) for x in decisions.values())):
            raise ValueError("Owner must resolve every disagreement against the same source lock")
    else:
        decisions = {}
    final = {i: sorted(decisions[i] if i in decisions else a[i]) for i in a}
    return {"schema": VERSION + "/sealed-source-gold", "source_lock": packet["source_lock"],
            "reviewer_ids": [review_a["reviewer_id"], review_b["reviewer_id"]],
            "owner_adjudicated": bool(disagreements), "disagreement_count": len(disagreements),
            "labels": final, "status": "SEALED_HUMAN_REVIEW_OPPORTUNITIES_NOT_FACT_TRUTH",
            "publish_ready": False}


def _candidate_index(report: dict, source: dict) -> dict:
    for field, expected in (("source_url", source["url"]), ("source_post_id", source["post_id"]),
                            ("source_modified", source["modified"]),
                            ("source_content_sha256", source["content_sha256"]),
                            ("source_role", source["source_role"]),
                            ("benchmark_id", source["benchmark_id"])):
        if report.get(field) != expected:
            raise ValueError("BLIND_SOURCE_CONTRACT_MISMATCH: " + field)
    if (report.get("status") != "HUMAN_REVIEW_REQUIRED" or report.get("publish_ready") is not False
        or report.get("human_labels_present") != 0 or report.get("validated_truth_errors") is not None):
        raise ValueError("Machine report must not already contain human truth/publish approval")
    indexed = {}
    for c in report["candidates"]:
        key = (c["heading"], c["anchor"], c["code"])
        if (key in indexed or c["code"] not in CODES
            or c.get("editorial_verdict") != "NEEDS_HUMAN_REVIEW"
            or c.get("verified_fact_error") is not False):
            raise ValueError("Duplicate, unknown or falsely verified candidate")
        indexed[key] = c
    return indexed


def _visible(candidate: dict | None) -> dict:
    if candidate is None:
        return {"emitted": False, "notice": "NO_CANDIDATE"}
    return {"emitted": True, "priority": candidate["priority"],
            "reason": candidate["reason"],
            "signal_terms": candidate.get("signal_terms", []),
            "review_details": candidate.get("review_details", {}),
            "editorial_verdict": "NEEDS_HUMAN_REVIEW"}


def build_blind_pairs(packet: dict, gold: dict,
                      report_pairs: list[tuple[dict, dict]]) -> tuple[dict, dict]:
    """Random left/right masking; sealed mapping MUST NOT go to reviewers."""
    if gold.get("source_lock") != packet["source_lock"] or gold.get("status") != "SEALED_HUMAN_REVIEW_OPPORTUNITIES_NOT_FACT_TRUTH":
        raise ValueError("Seal complete independent source-only gold before exposing alerts")
    if len(report_pairs) != len(packet["sources"]):
        raise ValueError("One baseline/current pair per frozen source required")
    sections = {(s["post_id"], s["heading"], s["anchor"]): s["id"] for s in packet["sections"]}
    pairs, mapping, predictions = [], {}, {"baseline": [], "upgraded": []}
    rng = secrets.SystemRandom()
    for source, (baseline, upgraded) in zip(packet["sources"], report_pairs):
        old, new = _candidate_index(baseline, source), _candidate_index(upgraded, source)
        for key in sorted(set(old) | set(new)):
            section_id = sections.get((source["post_id"], key[0], key[1]))
            if not section_id:
                raise ValueError("Candidate section not in frozen source-only inventory")
            opaque = "PAIR-" + secrets.token_hex(10)
            swapped = rng.choice([True, False])
            left_version, right_version = (("upgraded", "baseline") if swapped
                                           else ("baseline", "upgraded"))
            versions = {"baseline": _visible(old.get(key)), "upgraded": _visible(new.get(key))}
            pairs.append({"id": opaque, "section_id": section_id,
                          "post_id": source["post_id"], "heading": key[0],
                          "anchor": key[1], "issue_code": key[2],
                          "left": versions[left_version], "right": versions[right_version]})
            mapping[opaque] = {"section_id": section_id, "post_id": source["post_id"],
                               "issue_code": key[2], "left": left_version, "right": right_version}
            for version in ("baseline", "upgraded"):
                if versions[version]["emitted"]:
                    predictions[version].append([section_id, key[2]])
    rng.shuffle(pairs)
    blind = {"schema": VERSION + "/pairs", "source_lock": packet["source_lock"],
             "instructions": "Two independent editors grade whether each anonymous notice is actionable (0=no, 1=weak, 2=useful, 3=clear); left/right versions concealed. Do not access sealed mapping.",
             "pairs": pairs, "status": "WAITING_FOR_TWO_BLIND_PAIR_REVIEWS"}
    sealed = {"schema": VERSION + "/mapping", "source_lock": packet["source_lock"],
              "mapping": mapping, "predictions": predictions,
              "status": "PRIVATE_EVALUATOR_ONLY"}
    return blind, sealed


def blank_pair_review(blind: dict) -> dict:
    return {"schema": VERSION + "/pair-labels", "source_lock": blind["source_lock"],
            "reviewer_id": None,
            "pairs": [{"id": p["id"], "left_actionability": None,
                       "right_actionability": None, "rationale": None}
                      for p in blind["pairs"]]}


def _offline_html(title: str, payload: dict, javascript: str) -> str:
    """Offline-only reviewer UI. Source and ratings never leave the browser."""
    safe = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c").replace(
        ">", "\\u003e").replace("&", "\\u0026")
    return ("<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>" + title + "</title><style>"
            "body{font:15px system-ui,sans-serif;color:#172333;max-width:1030px;margin:20px auto;padding:16px;background:#f3f6fa}"
            "header,section{background:white;border:1px solid #d8e0ea;padding:16px;border-radius:12px;margin-bottom:12px}"
            "h1{font-size:24px}h2{font-size:17px}p{line-height:1.6}"
            "pre{white-space:pre-wrap;word-break:break-word;line-height:1.7;background:#f8fafc;padding:12px;border-radius:8px}"
            "label{display:block;margin:10px 0}input,select,textarea,button{font:inherit}"
            "input[type=text],textarea,select{box-sizing:border-box;width:100%;padding:9px}"
            "textarea{min-height:70px}button{border:0;border-radius:9px;background:#2856a5;color:white;padding:12px;cursor:pointer}"
            ".muted{color:#65758a}.columns{display:grid;grid-template-columns:1fr 1fr;gap:12px}"
            ".notice{border:1px solid #dbe4ed;border-radius:8px;padding:10px}"
            "@media(max-width:750px){.columns{display:block}}"
            "</style></head><body><header><h1>" + title + "</h1>"
            "<p>完全离线、只读。须由两位不同真人独立完成。页面包含冻结竞品原文，禁止外传。"
            "导出 JSON 后须由离线 CLI 校验，未自动产生事实真值或 Owner 验收。</p>"
            "<label>审稿人真实姓名或内部代号<input id='reviewer' type='text' autocomplete='off'></label>"
            "<p id='progress' class='muted'></p><button id='export'>检查完整性并导出 JSON</button>"
            "<p id='message'></p></header><main id='items'></main>"
            "<script type='application/json' id='payload'>" + safe + "</script>"
            "<script>\"use strict\";" + javascript + "</script></body></html>")


_JS_HELPERS = r'''
const data=JSON.parse(document.getElementById('payload').textContent);
const root=document.getElementById('items');
function el(tag,t){const n=document.createElement(tag);if(t!==undefined)n.textContent=t;return n;}
function label(name,field){const l=el('label',name);l.append(field);return l;}
function save(data,name){const b=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
 const u=URL.createObjectURL(b),a=el('a');a.href=u;a.download=name;document.body.append(a);a.click();a.remove();
 setTimeout(()=>URL.revokeObjectURL(u),1000);}
function markProgress(done,total){document.getElementById('progress').textContent=done+'/'+total+' 项有效完成';}
'''


def render_source_workbench(packet: dict) -> str:
    if packet.get("schema") != VERSION + "/source-only":
        raise ValueError("Real frozen source-only packet required")
    javascript = _JS_HELPERS + r'''
data.sections.forEach((s,i)=>{
 const box=el('section');box.dataset.id=s.id;
 box.append(el('h2',(i+1)+' / '+data.sections.length+' · #'+s.post_id+' · '+s.heading));
 box.append(el('p','冻结段落（不是机器提醒）：'));
 box.append(el('pre',s.frozen_section_text));
 const checked=el('input');checked.type='checkbox';checked.dataset.field='reviewed';
 box.append(label('已完整查看本节并作出判断（无问题也必须勾选）',checked));
 data.issue_codes.forEach(code=>{
  const c=el('input');c.type='checkbox';c.dataset.code=code;
  box.append(label(code,c));
 });
 const reason=el('textarea');reason.dataset.field='rationale';reason.placeholder='正向标签：至少12字具体原因。无问题可留空。';
 box.append(label('依据／原因',reason));root.append(box);
 box.addEventListener('input',update);
});
function collect(){return Array.from(root.querySelectorAll('section')).map(s=>({
 id:s.dataset.id, reviewed:s.querySelector('[data-field=reviewed]').checked,
 issue_codes:Array.from(s.querySelectorAll('[data-code]:checked')).map(x=>x.dataset.code),
 rationale:s.querySelector('[data-field=rationale]').value.trim()||null
}));}
function valid(x){return x.reviewed&&(!x.issue_codes.length||(x.rationale&&x.rationale.length>=12));}
function update(){markProgress(collect().filter(valid).length,data.sections.length);}
document.getElementById('export').addEventListener('click',()=>{
 const reviewer=document.getElementById('reviewer').value.trim(),rows=collect();
 if(reviewer.length<2||rows.some(x=>!valid(x))){
  document.getElementById('message').textContent='请填写身份，并逐项完成全部段落与正向原因。';return;}
 save({schema:'andy-write-context-qc-blind/v1/source-labels',source_lock:data.source_lock,
       reviewer_id:reviewer,sections:rows.map(({id,issue_codes,rationale})=>({id,issue_codes,rationale}))},
      'r12-source-labels-'+reviewer.replace(/[^\w-]/g,'_')+'.json');
 document.getElementById('message').textContent='完成离线导出；请单独交给评测管理员，勿交换另一位的标签。';
});update();
'''
    return _offline_html("Andy Write R12 · 原文独立盲评", packet, javascript)


def render_pair_workbench(blind: dict) -> str:
    if blind.get("schema") != VERSION + "/pairs":
        raise ValueError("Anonymized pair packet required")
    javascript = _JS_HELPERS + r'''
function card(data,side){const n=el('div');n.className='notice';n.append(el('h3',side));
 n.append(el('pre',data.emitted?data.reason+'\n'+JSON.stringify(data.review_details,null,2):'未触发提醒'));
 return n;}
data.pairs.forEach((p,i)=>{
 const box=el('section');box.dataset.id=p.id;
 box.append(el('h2',(i+1)+' / '+data.pairs.length+' · '+p.heading+' · '+p.issue_code));
 const pair=el('div');pair.className='columns';
 ['left','right'].forEach(side=>{const n=card(p[side],side==='left'?'方案 A':'方案 B');
  const s=el('select');s.dataset.field=side+'_actionability';
  [{v:'',t:'请独立评分'},{v:'0',t:'0 · 无用/误导'},{v:'1',t:'1 · 很弱'},
   {v:'2',t:'2 · 有用'},{v:'3',t:'3 · 清晰可执行'}].forEach(o=>{
    const opt=el('option',o.t);opt.value=o.v;s.append(opt);});
  n.append(label('可操作性',s));pair.append(n);});box.append(pair);
 const notes=el('textarea');notes.dataset.field='rationale';notes.placeholder='可选：评价理由';
 box.append(label('评价理由',notes));root.append(box);box.addEventListener('input',update);
});
function collect(){return Array.from(root.querySelectorAll('section')).map(s=>{
 const get=k=>s.querySelector('[data-field='+k+']').value;
 return {id:s.dataset.id,left_actionability:get('left_actionability')===''?null:Number(get('left_actionability')),
 right_actionability:get('right_actionability')===''?null:Number(get('right_actionability')),
 rationale:get('rationale')||null};});}
function valid(x){return Number.isInteger(x.left_actionability)&&Number.isInteger(x.right_actionability);}
function update(){markProgress(collect().filter(valid).length,data.pairs.length);}
document.getElementById('export').addEventListener('click',()=>{
 const reviewer=document.getElementById('reviewer').value.trim(),rows=collect();
 if(reviewer.length<2||rows.some(x=>!valid(x))){
  document.getElementById('message').textContent='请填写身份并完成每组 A/B 的两项评分。';return;}
 save({schema:'andy-write-context-qc-blind/v1/pair-labels',source_lock:data.source_lock,
       reviewer_id:reviewer,pairs:rows},'r12-pair-labels-'+reviewer.replace(/[^\w-]/g,'_')+'.json');
 document.getElementById('message').textContent='已导出；评测管理员在两份评分到齐后才揭盲。';
});update();
'''
    return _offline_html("Andy Write R12 · 匿名提醒 A/B", blind, javascript)


def score_blind_review(blind: dict, mapping: dict, gold: dict,
                       review_a: dict, review_b: dict) -> dict:
    lock = blind["source_lock"]
    if any(x.get("source_lock") != lock for x in (mapping, gold, review_a, review_b)):
        raise ValueError("SOURCE_LOCK_MISMATCH")
    if mapping.get("status") != "PRIVATE_EVALUATOR_ONLY" or gold.get("status") != "SEALED_HUMAN_REVIEW_OPPORTUNITIES_NOT_FACT_TRUTH":
        raise ValueError("Missing sealed mapping or genuine gold labels")
    pair_ids = {p["id"] for p in blind["pairs"]}
    if pair_ids != set(mapping["mapping"]):
        raise ValueError("Blinded pair mapping incomplete")
    reconstructed = {"baseline": set(), "upgraded": set()}
    for pair in blind["pairs"]:
        record = mapping["mapping"][pair["id"]]
        if (record["section_id"] != pair["section_id"]
            or record["issue_code"] != pair["issue_code"]
            or {record["left"], record["right"]} != {"baseline", "upgraded"}):
            raise ValueError("Sealed left/right mapping conflicts with visible pair")
        for side in ("left", "right"):
            if pair[side]["emitted"]:
                reconstructed[record[side]].add((pair["section_id"], pair["issue_code"]))
    for version in reconstructed:
        if reconstructed[version] != {tuple(x) for x in mapping["predictions"][version]}:
            raise ValueError("Sealed predictions conflict with version-masked cards")
    grades = {}
    for review in (review_a, review_b):
        if review.get("schema") != VERSION + "/pair-labels" or not isinstance(review.get("reviewer_id"), str) or len(review["reviewer_id"].strip()) < 2:
            raise ValueError("Independent identified blind reviewer required")
        if review["reviewer_id"].casefold() in grades:
            raise ValueError("Two distinct blind reviewers required")
        rows = review.get("pairs")
        if not isinstance(rows, list) or len(rows) != len(pair_ids):
            raise ValueError("All blinded pairs require two real ratings")
        by_id = {}
        for row in rows:
            if row.get("id") not in pair_ids or row["id"] in by_id:
                raise ValueError("Duplicate or unknown blinded pair")
            for side in ("left_actionability", "right_actionability"):
                if type(row.get(side)) is not int or row[side] not in range(4):
                    raise ValueError("Actionability grades must be real integers 0..3")
            by_id[row["id"]] = row
        if set(by_id) != pair_ids:
            raise ValueError("Incomplete blind ratings")
        grades[review["reviewer_id"].casefold()] = by_id

    truth = {(section_id, code) for section_id, codes in gold["labels"].items() for code in codes}
    all_sections = set(gold["labels"])
    metrics = {}
    for version in ("baseline", "upgraded"):
        predicted = {tuple(x) for x in mapping["predictions"][version]}
        if any(section_id not in all_sections or code not in CODES for section_id, code in predicted):
            raise ValueError("Prediction outside reviewed source inventory")
        tp, fp, fn = len(predicted & truth), len(predicted - truth), len(truth - predicted)
        metrics[version] = {"tp": tp, "fp": fp, "fn": fn,
                            "review_opportunity_precision": round(tp/(tp+fp), 4) if tp+fp else None,
                            "review_opportunity_recall": round(tp/(tp+fn), 4) if tp+fn else None}
    per_version = {"baseline": [], "upgraded": []}
    for pair in blind["pairs"]:
        versions = mapping["mapping"][pair["id"]]
        for rows in grades.values():
            row = rows[pair["id"]]
            for side in ("left", "right"):
                per_version[versions[side]].append(row[side + "_actionability"])
    mean = {v: round(sum(x)/len(x), 3) if x else None for v, x in per_version.items()}
    return {"schema": VERSION + "/score", "source_lock": lock,
            "human_source_reviewers": gold["reviewer_ids"],
            "human_pair_reviewers": [review_a["reviewer_id"], review_b["reviewer_id"]],
            "source_disagreements_owner_resolved": gold["owner_adjudicated"],
            "source_section_count": len(all_sections), "blind_pair_count": len(pair_ids),
            "review_opportunity_confusion": metrics,
            "mean_notice_actionability_out_of_3": mean,
            "true_factual_error_count": None, "search_intent_verdict": "UNASSESSABLE",
            "status": "HUMAN_LABELED_EXPLORATORY_PENDING_OWNER_UAT", "publish_ready": False,
            "limitations": "Human labels concern actionable QC review opportunities, not manufacturer fact truth; small two-article sample, no writing-quality inference."}
