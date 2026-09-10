const ACTIVE = new Set(["researcher","quant","investor","scientist","systems","skeptic","contrarian","observer","governance"]);
const PERSPECTIVES = [
  ["researcher","RESEARCHER","Evidence-bound fundamental research"],["quant","QUANT","Quantitative and statistical interpretation"],["investor","INVESTOR","Investment thesis"],["scientist","SCIENTIST","Scientific and Epistemic Validity"],["systems","SYSTEMS","Systems risk"],["contrarian","CONTRARIAN","Strongest credible opposing case"],["skeptic","SKEPTIC","Evidence and assumption challenge"],["observer","OBSERVER","Outcome observation"],["governance","GOVERNANCE","CHARTER and Authority Boundary"]
];
const $=id=>document.getElementById(id);
function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));}
function listText(value, fallback="NOT AVAILABLE"){
  if(Array.isArray(value)) return value.length?value.join(" • "):fallback;
  if(value==null || value==="") return fallback;
  return String(value);
}
function riskText(value, fallback="NOT AVAILABLE"){
  if(Array.isArray(value)) return value.length?`${value.length} concern${value.length===1?"":"s"}`: "NONE IDENTIFIED";
  return value==null || value===""?fallback:String(value);
}
function pct(v){return v==null?"UNKNOWN":`${(Number(v)*100).toFixed(2)}%`;}
function money(v){return v==null?"UNKNOWN":Number(v).toLocaleString(undefined,{maximumFractionDigits:0});}
function metric(v, formatter=x=>x){return v==null?"UNKNOWN":formatter(v);}
function renderPerspectives(outputs=[], creAssessments=[]){
  const byId=Object.fromEntries(outputs.map(x=>[x.agent_id||x.agent?.agent_id,x]));
  const creById=Object.fromEntries((creAssessments||[]).map(x=>[x.perspective_id,x]));
  $("perspectives").innerHTML=PERSPECTIVES.map(([id,name,detail])=>{
    const active=ACTIVE.has(id), out=byId[id], cre=creById[id];
    const status=active?(out?"RETURNED":"ACTIVE"):"NOT YET ACTIVE";
    const signal=cre?.recommendation||out?.direction||"";
    const claim=cre?.economic_claim;
    return `<article class="agent ${active?"active":"inactive"}"><div class="agent-name"><span>${name}</span><span class="agent-status">${status}</span></div><div class="agent-detail">${esc(signal||claim||detail)}</div>${claim?`<div class="agent-economics">${esc(claim)}</div>`:""}</article>`;
  }).join("");
}
function renderMeta(meta={}){
  const has=meta && typeof meta === "object" && Object.keys(meta).length>0;
  $("meta-status").textContent=has?(meta.status||"EVALUATED").toUpperCase():"AWAITING ANALYSIS";
  $("meta-health").textContent=has?esc(meta.reasoning_health||"UNKNOWN"):"NOT AVAILABLE";
  $("meta-review").textContent=has&&meta.human_review_required!==false?"HUMAN REVIEW REQUIRED":"REVIEW STATUS NOT RETURNED";
  $("meta-consensus").textContent=has?riskText(meta.false_consensus_risk):"NOT AVAILABLE";
  $("meta-correlation").textContent=has?riskText(meta.correlated_reasoning_risk):"NOT AVAILABLE";
  $("meta-evidence").textContent=has?riskText(meta.evidence_quality_concern):"NOT AVAILABLE";
  $("meta-assumptions").textContent=has?riskText(meta.assumption_concentration):"NOT AVAILABLE";
  $("meta-conflicts").textContent=has?(Array.isArray(meta.unresolved_conflicts)?meta.unresolved_conflicts.length:riskText(meta.unresolved_conflicts,"0")):"0";
  $("meta-uncertainty").textContent=has?riskText(meta.uncertainty_concern):"NOT AVAILABLE";
  $("meta-regime").textContent=has?riskText(meta.regime_or_invalidation_concern):"NOT AVAILABLE";
  $("meta-blind-spots").textContent=has?(Array.isArray(meta.process_blind_spots)?meta.process_blind_spots.length:riskText(meta.process_blind_spots,"0")):"0";
  $("meta-next-step").textContent=has?(meta.recommended_next_step||"NOT AVAILABLE"):"AWAITING ANALYSIS";
  $("meta-observations").innerHTML=has?esc(listText(meta.observations,"No process observations returned.")).replace(/ • /g,"<br>"):"No Meta-Intelligence evaluation yet.";
}
function setDecision(value){
  const raw=String(value||"");
  const normalized=raw==="HOLD"||raw==="CONDITIONAL GO"?"INVESTIGATE":raw;
  const allowed=new Set(["NO DATA","INVESTIGATE","NO-GO","READY FOR IC REVIEW"]);
  const v=allowed.has(normalized)?normalized:"NO DATA";
  $("decision-state").textContent=v; $("ic-state").textContent=v;
}
function renderConflicts(conflicts=[],horizon=[],creConflicts=[]){
  const items=[...conflicts,...horizon,...(creConflicts||[])];
  $("conflict-count").textContent=`${items.length} ${items.length===1?"ITEM":"ITEMS"}`;
  $("conflicts").innerHTML=items.length?items.map(c=>{const r=c.conflict_record||c;const economics=r.economic_disagreement||r.description||r.unresolved_questions?.join(" • ");return `<div class="conflict-item"><strong>${esc(r.conflict_type||c.type||"CONFLICT")}</strong><span>${esc(r.severity||c.severity||"UNSPECIFIED")}</span><div class="question">${esc(economics||"Unresolved question not supplied.")}</div></div>`}).join(""):"NO CONFLICT DATA / NO DISAGREEMENT RETURNED";
}
function renderRisk(sim={}){
  const scenarios=Array.isArray(sim.scenarios)?Object.fromEntries(sim.scenarios.map(x=>[String(x.scenario).toLowerCase(),x])):(sim.scenarios||{});
  const names=["base","bull","bear","adversarial","tail_risk"];
  $("risk-grid").innerHTML=names.map(n=>{
    const x=scenarios[n]||scenarios[n.toUpperCase()];
    if(!x)return `<div class="risk-card"><span>${n.replace("_"," ").toUpperCase()}</span><strong>NOT AVAILABLE</strong><em>Backend metric not returned</em></div>`;
    return `<div class="risk-card"><span>${n.replace("_"," ").toUpperCase()}</span><strong>${esc(x.mean_terminal??x.mean_terminal_value??"NOT AVAILABLE")}</strong><em>loss ${x.probability_loss==null?"NOT AVAILABLE":esc(pct(x.probability_loss))} • drawdown ${x.max_drawdown_mean==null?"NOT AVAILABLE":esc(pct(x.max_drawdown_mean))}</em></div>`;
  }).join("");
  $("risk-note").textContent=sim.independent_of_agents===false?"INDEPENDENCE FLAG FAILED":"Independent simulation output. Agent conclusions do not determine these results.";
}
function renderCRE(cre={}){
  const m=cre.financial_model||{};
  const ctx=cre.context||{};
  const u=cre.underwriting||{};
  const status=m.status||"UNKNOWN";
  const items=[
    ["PURCHASE PRICE",money(ctx.purchase_price)], ["ANNUAL NOI",money(ctx.noi)], ["GOING-IN CAP",pct(m.going_in_cap_rate)], ["OCCUPANCY",pct(ctx.occupancy)],
    ["LTV",pct(ctx.financing_assumptions?.loan_to_value)], ["LOAN AMOUNT",money(ctx.financing_assumptions?.loan_amount)], ["INTEREST RATE",pct(ctx.interest_rate??ctx.financing_assumptions?.interest_rate)], ["DSCR",metric(m.dscr,x=>Number(x).toFixed(2)+"x")],
    ["DEBT YIELD",pct(m.debt_yield)], ["EQUITY REQUIRED",money(m.equity_requirement)], ["CASH-ON-CASH",pct(m.cash_on_cash)], ["EQUITY MULTIPLE",metric(m.equity_multiple,x=>Number(x).toFixed(2)+"x")],
    ["IRR",pct(m.irr)], ["EXIT VALUE",money(m.exit_value)], ["NET SALE PROCEEDS",money(m.net_sale_proceeds)], ["HOLD PERIOD",ctx.hold_period==null?"UNKNOWN":`${ctx.hold_period} yrs`]
  ];
  $("cre-grid").innerHTML=`<div class="model-status">MODEL STATUS <strong>${esc(status)}</strong></div>`+items.map(([label,value])=>`<div class="cre-metric"><span>${label}</span><strong>${esc(value)}</strong></div>`).join("");
  const breaks=[
    ["BREAK-EVEN OCCUPANCY",pct(m.break_even_occupancy)], ["BREAK-EVEN EXIT CAP",pct(m.break_even_exit_cap)],
    ["MAX PRICE @ TARGET CAP",money(m.max_purchase_price_at_target_cap)], ["MAX LOAN @ TARGET DSCR",money(m.max_loan_at_target_dscr)],
    ["MISSING INPUTS",listText(m.missing_inputs,"NONE")], ["UNDERWRITING",u.decision||status]
  ];
  $("cre-breaks").innerHTML=breaks.map(([label,value])=>`<div><span>${label}</span><strong>${esc(value)}</strong></div>`).join("");
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
function optionalNumber(id,scale=1){const value=$(id).value.trim();return value===""?undefined:Number(value)/scale;}
function buildCREContext(){
  const purchase=optionalNumber("purchase-price"), noi=optionalNumber("noi"), occupancy=optionalNumber("occupancy",100);
  if(purchase==null && noi==null) return undefined;
  const financing={}; const ltv=optionalNumber("ltv",100); if(ltv!=null) financing.loan_to_value=ltv;
  const rate=optionalNumber("rate",100); if(rate!=null) financing.interest_rate=rate;
  const exitCap=optionalNumber("exit-cap",100); const rentGrowth=optionalNumber("rent-growth",100); const expenseGrowth=optionalNumber("expense-growth",100); const hold=optionalNumber("hold");
  return {opportunity_id:"UI-OPPORTUNITY",property_id:"UI-PROPERTY",asset_type:$("asset").value.trim()||"UNKNOWN",location:$("market").value.trim()||"UNKNOWN",purchase_price:purchase,noi:noi,occupancy:occupancy,rent_growth:rentGrowth,expense_growth:expenseGrowth,interest_rate:rate,hold_period:hold,financing_assumptions:financing,exit_assumptions:exitCap==null?{}:{exit_cap_rate:exitCap},evidence:[],uncertainty:["CRE inputs supplied through read-only dashboard form; evidence has not been attached."],missing_inputs:[]};
}
async function runAnalysis(e){e.preventDefault();const b=$("run-button");b.disabled=true;b.classList.add("button-busy");b.textContent="RUNNING RESEARCH ANALYSIS…";$("research-state").textContent="RUNNING";setDecision("NO DATA");renderMeta({});$("core-question").textContent=$("question").value;try{const cre_context=buildCREContext();const payload={question:$("question").value,evidence:[],initial_value:Number($("initial-value").value),horizon_steps:Number($("horizon").value),paths:Number($("paths").value),seed:42};if(cre_context)payload.cre_context=cre_context;const r=await fetch("/analysis/run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});const data=await r.json();if(!r.ok)throw Error(data.detail||"Analysis failed");renderPerspectives(data.agents||[],data.cre?.perspectives||[]);renderCRE(data.cre||{});renderMeta(data.meta_intelligence||{});renderConflicts(data.conflicts||[],data.horizon_divergences||[],data.cre?.conflicts||[]);renderRisk(data.cre?.simulation||data.simulation||{});setDecision(data.synthesis?.verdict);if(data.cre?.decision){$("cre-decision").textContent=String(data.cre.decision.state||"UNKNOWN");$("decision-rationale").textContent=listText(data.cre.decision.rationale,"No CRE decision rationale returned.");}else{$("cre-decision").textContent="UNKNOWN";$("decision-rationale").textContent="No CRE context supplied. Enter purchase price and NOI to activate the CRE economic model.";}$("evidence-state").textContent=`${data.evidence?.count??0} VALIDATED / ${data.evidence?.usable_count??0} USABLE`;$("research-state").textContent="COMPLETE";await loadMemory();await loadLearning();}catch(err){$("research-state").textContent="ERROR";$("conflicts").textContent=esc(err.message);$("conflict-count").textContent="ERROR";renderMeta({status:"unavailable"});}finally{b.disabled=false;b.classList.remove("button-busy");b.textContent="RUN RESEARCH ANALYSIS";}}
$("analysis-form").addEventListener("submit",runAnalysis);$("load-memory").addEventListener("click",()=>{loadMemory();loadLearning();});renderPerspectives();renderMeta();renderCRE();renderRisk();health();loadMemory();loadLearning();
