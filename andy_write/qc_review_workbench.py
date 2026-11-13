"""Private offline human labeling UI. No AI labels, no network, no publishing."""
from __future__ import annotations
import json
from pathlib import Path
from .io import ROOT
from .qc_calibration import REVIEW_DECLARATION, validate_packet

def build_workbench(packet:dict,source:str,draft:str)->str:
    cases=validate_packet(packet,source,draft)
    data={
        "source_sha256":packet["source_sha256"],
        "draft_sha256":packet["draft_sha256"],
        "declaration":REVIEW_DECLARATION,
        "options":packet["label_options"],
        "cases":[{
            "id":c["source_id"],"hash":c["source_sha256"],
            "source":c["source_text_for_private_review"],
            "hint":c.get("target_text_for_private_review",""),
            "state":c["machine_state"]
        } for c in cases],
        "draft":draft
    }
    safe=json.dumps(data,ensure_ascii=False).replace("<","\\u003c").replace(
        ">","\\u003e").replace("&","\\u0026")
    return """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Andy Write · 私有人工语义审核</title>
<style>
body{font-family:system-ui,sans-serif;max-width:1150px;margin:20px auto;padding:16px;background:#f5f6f7;color:#172033}
h1{font-size:24px}h2{font-size:18px}h3{font-size:15px}
header,section,aside{background:white;padding:18px;border:1px solid #dde0e5;border-radius:10px;margin-bottom:12px}
main{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:16px}
pre{white-space:pre-wrap;overflow:auto;max-height:260px;line-height:1.6;padding:12px;background:#f5f7fa;border-radius:8px}
#draft{max-height:680px}label{display:grid;gap:5px;margin:12px 0}
input,select,textarea,button{font:inherit;padding:8px;box-sizing:border-box;width:100%}
textarea{min-height:80px}button{border:0;border-radius:8px;background:#2455a5;color:white;cursor:pointer;margin:7px 0}
.warning{color:#ad421e}small{color:#627184}@media(max-width:820px){main{display:block}}
</style></head><body><header><h1>Andy Write · 12 项人工语义审核</h1>
<p>离线文件，不联网。必须本人对照原文和完整改写稿再填写标签，AI 不能代替审核。</p>
<p class="warning">文件内包含私有原文，不要上传公开平台。导出的 JSON 仍需独立 CLI 验证及 Owner 审核。</p>
<label>审核人姓名或内部代号<input id="reviewer"></label><strong id="progress"></strong>
</header><main><article id="cases"></article><aside><h2>完整改写稿</h2>
<pre id="draft"></pre><button id="export">完成并导出 JSON</button>
<button id="template">导出空白 JSON 模板</button><p id="message"></p></aside></main>
<script id="payload" type="application/json">""" + safe + """</script>
<script>
"use strict";
var data=JSON.parse(document.getElementById("payload").textContent);
document.getElementById("draft").textContent=data.draft;
function elem(t,txt){var x=document.createElement(t);if(txt!==undefined)x.textContent=txt;return x;}
var container=document.getElementById("cases");
data.cases.forEach(function(c,i){
 var s=elem("section");s.dataset.id=c.id;
 s.append(elem("h2",String(i+1)+"/12 · "+c.id));
 s.append(elem("small","机器状态："+c.state+"，不等于人工判断"));
 s.append(elem("h3","原文"));s.append(elem("pre",c.source));
 s.append(elem("h3","机器推荐查找位置"));s.append(elem("pre",c.hint||"未找到匹配；请从右侧全文寻找。"));
 [["label","人工语义标签","select"],["reason","判断理由（不少于24字符）","textarea"],
  ["target_quote","改写稿实际引用（正向标签必填）","textarea"]].forEach(function(spec){
  var lab=elem("label",spec[1]),field=elem(spec[2]);field.dataset.field=spec[0];
  if(spec[2]==="select"){var opt=elem("option","请选择");opt.value="";field.append(opt);
    data.options.forEach(function(v){var o=elem("option",v);o.value=v;field.append(o);});}
  field.addEventListener("input",update);lab.append(field);s.append(lab);
 });
 container.append(s);
});
function recordList(){
 var name=document.getElementById("reviewer").value.trim();
 return Array.from(document.querySelectorAll("section[data-id]")).map(function(s,i){
  function get(k){return s.querySelector('[data-field="'+k+'"]').value.trim();}
  return {source_id:data.cases[i].id,source_sha256:data.cases[i].hash,
          reviewer:name,reviewer_declaration:data.declaration,
          label:get("label")||null,reason:get("reason")||null,target_quote:get("target_quote")||null};
 });
}
function valid(x){
 if(!x.reviewer||x.reviewer.length<2||!x.label||!x.reason||x.reason.length<24)return false;
 if(x.label==="SEMANTICALLY_RETAINED"||x.label==="RETAINED_WITH_QUALIFICATIONS"){
   return x.target_quote&&x.target_quote.length>=20&&data.draft.includes(x.target_quote);
 }
 return !x.target_quote||data.draft.includes(x.target_quote);
}
function update(){
 var n=recordList().filter(valid).length;
 document.getElementById("progress").textContent=n+"/12 条完成字段核验；不是人工语义质量分";
}
function save(name,records){
 var b=new Blob([JSON.stringify(records,null,2)],{type:"application/json"});
 var url=URL.createObjectURL(b),a=document.createElement("a");
 a.href=url;a.download=name;document.body.append(a);a.click();a.remove();
 setTimeout(function(){URL.revokeObjectURL(url);},1000);
}
document.getElementById("reviewer").addEventListener("input",update);
document.getElementById("export").addEventListener("click",function(){
 var list=recordList(),missing=list.map(function(x,i){return valid(x)?null:i+1;}).filter(Boolean);
 if(missing.length){document.getElementById("message").textContent="缺少有效信息："+missing.join("、");return;}
 save("andy-write-human-12-annotations.json",list);
 document.getElementById("message").textContent="已本地导出；尚需 CLI 与 Owner 审核。";
});
document.getElementById("template").addEventListener("click",function(){
 save("andy-write-human-12-template.json",recordList());
});
update();
</script></body></html>
"""

def export_workbench(packet_path:Path,source:str,draft:str,
                     output_path:Path)->dict:
    root=(ROOT/".runs").resolve()
    if (not packet_path.resolve().is_relative_to(root)
        or not output_path.resolve().is_relative_to(root)):
        raise PermissionError("Private human review workbench must remain in .runs")
    if output_path.suffix.lower()!=".html":
        raise ValueError("Private review output must be HTML")
    packet=json.loads(packet_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(build_workbench(packet,source,draft),encoding="utf-8")
    return {"status":"PRIVATE_REVIEW_WORKBENCH_READY",
            "output_path":str(output_path),
            "sample_count":12,
            "human_labels_present":0,
            "network_requests_required":False,
            "owner_approval":"PENDING"}
