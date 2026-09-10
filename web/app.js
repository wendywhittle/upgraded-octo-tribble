const ACTIVE = new Set(["researcher","quant","skeptic","contrarian"]);
const PERSPECTIVES = [
  ["researcher","RESEARCHER","Evidence-bound fundamental research"],["quant","QUANT","Quantitative and statistical interpretation"],["investor","INVESTOR","Investment thesis"],["scientist","SCIENTIST","Scenario analysis"],["systems","SYSTEMS","Systems risk"],["contrarian","CONTRARIAN","Strongest credible opposing case"],["skeptic","SKEPTIC","Evidence and assumption challenge"],["observer","OBSERVER","Outcome observation"],["meta-intelligence","META-INTELLIGENCE","Reasoning-process examination"],["governance","GOVERNANCE","CHARTER and authority boundary"]
];
const $=id=>document.getElementById(id);
function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));}
function renderPerspectives(outputs=[]){
  const byId=Object.fromEntries(outputs.map(x=>[x.agent_id||x.agent?.agent_id,x]));
  $("perspectives").innerHTML=PERSPECTIVES.map(([id,name,detail])=>{
    const active=ACTIVE.has(id), out=byId[id];
    const status=active?(out?"RETURNED":"ACTIVE"):"NOT YET ACTIVE";
    const signal=out?.direction||out?.recommendation||"";
    return `<article class="agent ${active?"active":"inactive"}"><div class="agent-name"><span>${name}</span><span class="agent-status">${status}</span></div><div class="agent-detail">${esc(signal||detail)}</div></article>`;
  }).join("");
}
function setDecision(value){
  const allowed=new Set(["NO DATA","INVESTIGATE","NO-GO","READY FOR IC REVIEW"]);
  const v=allowed.has(String(value||""))?String(value):"NO DATA";
  $("decision-state").textContent=v; $("ic-state").textContent=v;
}
function renderConflicts(conflicts=[]){
  $("conflict-count").textContent=`${conflicts.length} ${conflicts.length===1?"ITEM":"ITEMS"}`;
  $("conflicts").innerHTML=conflicts.length?conflicts.map(c=>`<div class="conflict-item"><strong>${esc(c.conflict_type||c.type||"CONFLICT")}</strong><span>${esc(c.severity||"UNSPECIFIED")}</span><div class="question">${esc(c.unresolved_questions?.join(" • ")||c.description||"Unresolved question not supplied.")}</div></div>`).join(""):"NO CONFLICT DATA / NO DISAGREEMENT RETURNED";
}
function renderRisk(sim={}){
  const scenarios=sim.scenarios||sim.results||{};
  const names=["base","bull","bear","adversarial"];
  $("risk-grid").innerHTML=names.map(n=>{
    const x=scenarios[n];
    if(!x)return `<div class="risk-card"><span>${n.toUpperCase()}</span><strong>NOT AVAILABLE</strong><em>Backend metric not returned</em></div>`;
    const value=x.final_value??x.mean??x.expected_value??x.median;
    return `<div class="risk-card"><span>${n.toUpperCase()}</span><strong>${value==null?"AVAILABLE":esc(value)}</strong><em>${x.probability_of_loss==null?"Distribution returned":`loss probability ${esc(x.probability_of_loss)}`}</em></div>`;
  }).join("");
  $("risk-note").textContent=sim.independent_of_agents===false?"INDEPENDENCE FLAG FAILED":"Independent simulation output. Agent conclusions do not determine these results.";
}
function renderMemory(records=[]){
  const r=records.at(-1); if(!r)return;
  $("memory-belief").textContent=r.question||"NOT AVAILABLE";
  $("memory-why").textContent=r.evidence?.length?`${r.evidence.length} evidence item(s)`:"NOT AVAILABLE";
  $("memory-decision").textContent=r.synthesis?.verdict||"NOT AVAILABLE";
  $("memory-outcome").textContent=r.outcome?.status||"PENDING";
  $("memory-lesson").textContent=r.lesson||"AWAITING OUTCOME";
}
async function health(){try{const r=await fetch("/health");if(!r.ok)throw Error();$("api-dot").className="status-dot online";$("api-status").textContent="API ONLINE";}catch{$("api-dot").className="status-dot offline";$("api-status").textContent="API UNAVAILABLE";}}
async function loadMemory(){try{const r=await fetch("/memory");if(!r.ok)throw Error();const data=await r.json();renderMemory(Array.isArray(data)?data:data.records||[]);}catch{$("memory-outcome").textContent="UNAVAILABLE";}}
async function runAnalysis(e){e.preventDefault();const b=$("run-button");b.disabled=true;b.classList.add("button-busy");b.textContent="RUNNING RESEARCH ANALYSIS…";$("research-state").textContent="RUNNING";setDecision("NO DATA");$("core-question").textContent=$("question").value;try{const r=await fetch("/analysis/run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:$("question").value,evidence:[],initial_value:Number($("initial-value").value),horizon_steps:Number($("horizon").value),paths:Number($("paths").value),seed:42})});const data=await r.json();if(!r.ok)throw Error(data.detail||"Analysis failed");renderPerspectives(data.agents||data.perspectives||[]);renderConflicts(data.conflicts||[]);renderRisk(data.simulation||{});setDecision(data.synthesis?.verdict||data.decision||"INVESTIGATE");$("evidence-state").textContent=(data.evidence?.length||0)+" SUPPLIED";$("research-state").textContent="COMPLETE";await loadMemory();}catch(err){$("research-state").textContent="ERROR";$("conflicts").textContent=esc(err.message);$("conflict-count").textContent="ERROR";}finally{b.disabled=false;b.classList.remove("button-busy");b.textContent="RUN RESEARCH ANALYSIS";}}
$("analysis-form").addEventListener("submit",runAnalysis);$("load-memory").addEventListener("click",loadMemory);renderPerspectives();renderRisk();health();loadMemory();
