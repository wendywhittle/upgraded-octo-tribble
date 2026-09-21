const form=document.querySelector("#deal-form");
const result=document.querySelector("#result");
const pipeline=document.querySelector("#pipeline-list");

const money=v=>v==null?"—":new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:0}).format(v);
const pct=v=>v==null?"—":(v*100).toFixed(2)+"%";
const val=v=>v==null?"—":typeof v==="number"?Number.isInteger(v)?v:v.toFixed(3):v;

function metric(label,value){return '<div class="metric"><span>'+label+'</span><strong>'+value+'</strong></div>'}

function renderResult(d){
  const x=d.derived||{};
  const noi=d.original_inputs.noi ?? (d.original_inputs.egi!=null&&d.original_inputs.operating_expenses!=null ? d.original_inputs.egi-d.original_inputs.operating_expenses : null);
  result.classList.remove("hidden");
  result.innerHTML='<div class="section-head"><p class="eyebrow">03 / DEAL RESULT</p><h2>'+d.original_inputs.name+'</h2><p><span class="status">'+d.deal_id+' · '+d.status+'</span> · Based on the information you provided.</p></div>'+
  '<div class="result-grid">'+
  metric("Purchase price",money(d.original_inputs.purchase_price))+
  metric("NOI",money(noi))+
  metric("Cap rate",pct(x.cap_rate))+
  metric("DSCR",val(x.dscr))+
  metric("Initial equity",money(x.initial_equity))+
  metric("Annual cash flow",money(x.annual_cash_flow))+
  metric("Cash-on-cash",pct(x.cash_on_cash))+
  metric("Exit value",money(x.exit_value))+
  metric("IRR",pct(x.irr))+
  metric("Equity multiple",x.equity_multiple?x.equity_multiple.toFixed(2)+"x":"—")+
  '</div>'+
  (d.missing.length?'<div class="missing"><strong>Missing / unavailable:</strong> '+d.missing.join(", ")+'</div>':"")+
  '<div class="actions"><a class="primary" href="/api/deals/'+d.deal_id+'/excel">DOWNLOAD EXCEL</a><a class="primary" href="#pipeline">VIEW PIPELINE</a></div>';
}

form.addEventListener("submit",async e=>{
  e.preventDefault();
  const data=Object.fromEntries(new FormData(form));
  for(const k of Object.keys(data)){
    if(data[k]==="") data[k]=null;
    else if(["purchase_price","noi","egi","operating_expenses","occupancy","ltv","interest_rate","amortization_years","hold_years","exit_cap_rate","closing_costs"].includes(k)) data[k]=Number(data[k]);
  }
  const r=await fetch("/api/deals",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
  if(!r.ok){alert(await r.text());return}
  const d=await r.json();
  renderResult(d);
  form.reset();
  loadPipeline();
  result.scrollIntoView({behavior:"smooth"});
});

async function loadPipeline(){
  const r=await fetch("/api/deals");
  const ds=await r.json();
  pipeline.innerHTML=ds.length ? ds.map(d=>
    '<article class="deal-card"><div><div class="status">'+d.deal_id+' · '+d.status+'</div><h3>'+d.original_inputs.name+'</h3><div class="muted">'+d.original_inputs.asset_type+' · '+d.original_inputs.location+' · '+money(d.original_inputs.purchase_price)+' · Cap '+pct(d.derived.cap_rate)+'</div></div><div class="actions">'+
    '<button onclick="changeStatus(\''+d.deal_id+'\',\'REVIEWING\')">REVIEW</button>'+
    '<button onclick="changeStatus(\''+d.deal_id+'\',\'PURSUE\')">PURSUE</button>'+
    '<button onclick="changeStatus(\''+d.deal_id+'\',\'HOLD\')">HOLD</button>'+
    '<button onclick="changeStatus(\''+d.deal_id+'\',\'PASS\')">PASS</button>'+
    '</div></article>'
  ).join(""):'<p class="muted">No deals yet. Enter the first one above.</p>';
}

async function changeStatus(id,status){
  await fetch("/api/deals/"+id+"/status",{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({status})});
  loadPipeline();
}

loadPipeline();
