const ACTIVE = new Set(["researcher","quant","investor","systems","skeptic","contrarian"]);
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
  const raw=String(value||"");
  const normalized=raw==="HOLD"||raw==="CONDITIONAL GO"?"INVESTIGATE":raw;
  const allowed=new Set(["NO DATA","INVESTIGATE","NO-GO","READY FOR IC REVIEW"]);
  const v=allowed.has(normalized)?normalized:"NO DATA";
  $("decision-state").textContent=v; $("ic-state").textContent=v;
}
function renderConflicts(conflicts=[],horizon=[]){
  const items=[...conflicts,...horizon];
  $("conflict-count").textContent=`${items.length} ${items.length===1?"ITEM":"ITEMS"}`;
  $("conflicts").innerHTML=items.length?items.map(c=>{const r=c.conflict_record||c;return `<div class="conflict-item"><strong>${esc(r.conflict_type||c.type||"CONFLICT")}</strong><span>${esc(r.severity||c.severity||"UNSPECIFIED")}</span><div class="question">${esc(r.unresolved_questions?.join(" • ")||c.description||"Unresolved question not supplied.")}</div></div>`}).join(""):"NO CONFLICT DATA / NO DISAGREEMENT RETURNED";
}
function renderRisk(sim={}){
  const scenarios=Array.isArray(sim.scenarios)?Object.fromEntries(sim.scenarios.map(x=>[x.scenario,x])):(sim.scenarios||{});
  const names=["base","bull","bear","adversarial"];
  $("risk-grid").innerHTML=names.map(n=>{
    const x=scenarios[n];
    if(!x)return `<div class="risk-card"><span>${n.toUpperCase()}</span><strong>NOT AVAILABLE</strong><em>Backend metric not returned</em></div>`;
    return `<div class="risk-card"><span>${n.toUpperCase()}</span><strong>${esc(x.mean_terminal??"NOT AVAILABLE")}</strong><em>loss ${x.probability_loss==null?"NOT AVAILABLE":esc(x.probability_loss)} • drawdown ${x.max_drawdown_mean==null?"NOT AVAILABLE":esc(x.max_drawdown_mean)}</em></div>`;
  }).join("");
  $("risk-note").textContent=sim.independent_of_agents===false?"INDEPENDENCE FLAG FAILED":"Independent simulation output. Agent conclusions do not determine these results.";
}
function renderMemory(records=[]){
  const r=records.at(-1); if(!r)return;
  $("memory-belief").textContent=r.question||"NOT AVAILABLE";
  const evidence=r.evidence||{};
  $("memory-why").textContent=evidence.count==null?"NOT AVAILABLE":`${evidence.count} evidence item(s)`;
  $("memory-decision").textContent=r.synthesis?.verdict||"NOT AVAILABLE";
  $("memory-outcome").textContent=r.outcome?.status||"PENDING";
  $("memory-lesson").textContent=r.lesson||"AWAITING OUTCOME";
}
async function health(){try{const r=await fetch("/health");if(!r.ok)throw Error();$("api-dot").className="status-dot online";$("api-status").textContent="API ONLINE";}catch{$("api-dot").className="status-dot offline";$("api-status").textContent="API UNAVAILABLE";}}
async function loadMemory(){try{const r=await fetch("/memory");if(!r.ok)throw Error();const data=await r.json();renderMemory(data.records||[]);}catch{$("memory-outcome").textContent="UNAVAILABLE";}}
async function loadLearning(){try{const r=await fetch("/observer/learning",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({bins:10})});if(!r.ok)throw Error();const data=await r.json();if(Array.isArray(data.lessons)&&data.lessons.length){$("memory-lesson").textContent=data.lessons.join(" • ");}}catch{$("memory-lesson").textContent="LEARNING DATA UNAVAILABLE";}}
async function runAnalysis(e){e.preventDefault();const b=$("run-button");b.disabled=true;b.classList.add("button-busy");b.textContent="RUNNING RESEARCH ANALYSIS…";$("research-state").textContent="RUNNING";setDecision("NO DATA");$("core-question").textContent=$("question").value;try{const r=await fetch("/analysis/run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:$("question").value,evidence:[],initial_value:Number($("initial-value").value),horizon_steps:Number($("horizon").value),paths:Number($("paths").value),seed:42})});const data=await r.json();if(!r.ok)throw Error(data.detail||"Analysis failed");renderPerspectives(data.agents||[]);renderConflicts(data.conflicts||[],data.horizon_divergences||[]);renderRisk(data.simulation||{});setDecision(data.synthesis?.verdict);$("evidence-state").textContent=`${data.evidence?.count??0} VALIDATED / ${data.evidence?.usable_count??0} USABLE`;$("research-state").textContent="COMPLETE";await loadMemory();await loadLearning();}catch(err){$("research-state").textContent="ERROR";$("conflicts").textContent=esc(err.message);$("conflict-count").textContent="ERROR";}finally{b.disabled=false;b.classList.remove("button-busy");b.textContent="RUN RESEARCH ANALYSIS";}}
$("analysis-form").addEventListener("submit",runAnalysis);$("load-memory").addEventListener("click",()=>{loadMemory();loadLearning();});renderPerspectives();renderRisk();health();loadMemory();loadLearning();
