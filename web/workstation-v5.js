/* AletheiaTelos workstation v5. Integration/usability verification layer. No backend semantics. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const q = (s, root = document) => Array.from(root.querySelectorAll(s));
  const text = el => (el?.textContent || '').trim();
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function announce(message) {
    let el = $('workstation-announcer');
    if (!el) { el = document.createElement('div'); el.id = 'workstation-announcer'; el.className = 'sr-only'; el.setAttribute('aria-live', 'polite'); document.body.appendChild(el); }
    el.textContent = message;
  }

  function styles() {
    if ($('workstation-v5-styles')) return;
    const s = document.createElement('style'); s.id = 'workstation-v5-styles';
    s.textContent = `
      .stage.v5-current{outline:2px solid var(--cyan,#54d6ff);outline-offset:2px;box-shadow:0 0 0 1px rgba(84,214,255,.16)}
      .recent-item.v5-active,.agent.v5-active,.risk-card.v5-active,.conflict-item.v5-active{outline:1px solid var(--cyan,#54d6ff);background:rgba(84,214,255,.07)}
      .v5-inspector{margin-top:12px;padding:12px;border:1px solid rgba(84,214,255,.2);background:rgba(5,14,22,.8)}
      .v5-inspector-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:10px}
      .v5-cell{border:1px solid rgba(255,255,255,.08);padding:10px;min-width:0}.v5-cell span{display:block;font-size:9px;letter-spacing:.1em;color:var(--muted,#8293a3);margin-bottom:5px}.v5-cell strong{display:block;font-size:12px;overflow-wrap:anywhere}.v5-list{margin:8px 0 0;padding-left:18px}.v5-list li{margin:5px 0;color:#b7c4ce}
      .v5-state{font-size:10px;letter-spacing:.1em;color:var(--cyan,#54d6ff);text-transform:uppercase}
      @media(max-width:760px){.v5-inspector-grid{grid-template-columns:1fr}.v5-inspector{font-size:13px}}
    `;
    document.head.appendChild(s);
  }

  function context(stage, detail) {
    const label = $('v4-stage-label'); const info = $('v4-stage-detail');
    if (label) label.textContent = stage;
    if (info) info.textContent = detail || 'Current workstation context';
    q('.stage').forEach(x => x.classList.toggle('v5-current', text(x.querySelector('.stage-name')).toLowerCase() === String(stage).toLowerCase()));
  }

  const stageMap = {
    opportunity:['OPPORTUNITY','active-analysis'], evidence:['EVIDENCE','evidence'], underwriting:['UNDERWRITING','underwriting-workspace'],
    perspectives:['PERSPECTIVES','perspective-summary'], conflict:['CONFLICT','conflict-intelligence'], risk:['INDEPENDENT RISK','independent-risk'],
    contrarian:['CONTRARIAN','perspective-summary'], case:['INVESTMENT CASE','investment-case'], gate:['DECISION GATE','decision-gate'], observer:['OBSERVER','observer'], learning:['LEARNING','learning']
  };

  function activate(name, detail) {
    const key = String(name || '').toLowerCase();
    const meta = stageMap[key] || [String(name || 'WORKSTATION').toUpperCase(), null];
    context(meta[0], detail || meta[0]);
    const target = $(meta[1]); if (target) target.scrollIntoView({behavior:'smooth', block:'start'});
    announce(`Active workstation context: ${meta[0]}`);
  }

  function stageName(stage) {
    return (text(stage.querySelector('.stage-name')) || '').trim().toLowerCase();
  }

  function wireStages() {
    const pipeline = $('pipeline-stages'); if (!pipeline || pipeline.dataset.v5Bound) return;
    pipeline.dataset.v5Bound = '1';
    pipeline.addEventListener('click', e => {
      const stage = e.target.closest('.stage'); if (!stage || !pipeline.contains(stage)) return;
      e.preventDefault();
      activate(stageName(stage), stage.querySelector('.stage-desc') ? text(stage.querySelector('.stage-desc')) : 'Lifecycle stage selected');
    });
  }

  function wireRecent() {
    const root = $('recent-analyses'); if (!root || root.dataset.v5Bound) return;
    root.dataset.v5Bound = '1';
    root.addEventListener('click', e => {
      const item = e.target.closest('.recent-item'); if (!item) return;
      q('.recent-item').forEach(x => x.classList.remove('v5-active')); item.classList.add('v5-active');
      const question = text($('active-question')) || text(item);
      activate('opportunity', `ACTIVE ANALYSIS: ${question}`);
      announce(`Active analysis selected: ${question}`);
    });
  }

  function valueFor(id, fallback='NOT EXPOSED') { return text($(id)) || fallback; }

  function inspector(title, subtitle, body) {
    let box = $('v5-inspector');
    if (!box) {
      box = document.createElement('section'); box.id='v5-inspector'; box.className='v5-inspector';
      const anchor = $('perspective-summary') || document.querySelector('.primary-column');
      anchor?.appendChild(box);
    }
    box.innerHTML = `<div class="v5-state">${esc(subtitle)}</div><h3>${esc(title)}</h3>${body}`;
    box.scrollIntoView({behavior:'smooth',block:'nearest'});
  }

  function inspectGate() {
    const gate = window.latestAnalysis?.decision_gate || {};
    const readiness = window.latestAnalysis?.decision_readiness || {};
    const stops = Array.isArray(gate.hard_stops) ? gate.hard_stops : [];
    const blockers = Array.isArray(gate.blocking_reasons) ? gate.blocking_reasons : [];
    const mandatory = Array.isArray(readiness.mandatory_conditions) ? readiness.mandatory_conditions : [];
    const evidence = gate.evidence_status || {};
    const cells = [
      ['READINESS', readiness.status || gate.state || valueFor('gate-substate')],
      ['EVIDENCE', `${evidence.count ?? 'NOT EXPOSED'} VALIDATED / ${evidence.usable_count ?? 'NOT EXPOSED'} USABLE`],
      ['CONFLICT', `${(gate.unresolved_conflicts || []).length} UNRESOLVED`],
      ['INDEPENDENT RISK', gate.independent_risk ? 'RETURNED' : 'NO DATA'],
      ['CONTRARIAN', gate.contrarian_review_status || 'NOT EXPOSED'],
      ['HUMAN AUTHORITY', gate.human_decision_required === true ? 'REQUIRED' : 'NOT EXPOSED']
    ];
    inspector('Decision Gate','GOVERNANCE INSPECTOR',`<div class="v5-inspector-grid">${cells.map(c=>`<div class="v5-cell"><span>${esc(c[0])}</span><strong>${esc(c[1])}</strong></div>`).join('')}</div>${stops.length?`<p><b>HARD STOPS</b></p><ul class="v5-list">${stops.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`:''}${blockers.length?`<p><b>BLOCKING REASONS</b></p><ul class="v5-list">${blockers.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`:''}${mandatory.length?`<p><b>MANDATORY CONDITIONS</b></p><ul class="v5-list">${mandatory.map(x=>`<li>${esc(typeof x==='string'?x:JSON.stringify(x))}</li>`).join('')}</ul>`:''}<p>READY FOR HUMAN AUTHORITY ≠ AUTHORIZED ≠ EXECUTED. This interface cannot authorize or execute an investment decision.</p>`);
  }

  function inspectRisk() {
    const sim = window.latestAnalysis?.simulation || {};
    const scenarios = Array.isArray(sim.scenarios) ? sim.scenarios : Object.values(sim.scenarios || {});
    const body = scenarios.length ? `<div class="v5-inspector-grid">${scenarios.map(x=>`<div class="v5-cell"><span>${esc(x.scenario || 'SCENARIO')}</span><strong>MEAN TERMINAL: ${esc(x.mean_terminal ?? 'NOT AVAILABLE')}</strong><small>LOSS: ${esc(x.probability_loss ?? 'NOT AVAILABLE')} • DRAWDOWN: ${esc(x.max_drawdown_mean ?? 'NOT AVAILABLE')}</small></div>`).join('')}</div><p>Simulation output is displayed from the returned analysis result. It remains independent of agent conclusions.</p>` : '<p>NO DATA. No returned simulation scenarios are available for the active analysis.</p>';
    inspector('Independent Risk','SIMULATION INSPECTOR',body);
  }

  function inspectConflicts() {
    const data = window.latestAnalysis || {};
    const items = [...(data.conflicts || []), ...(data.horizon_divergences || [])];
    const body = items.length ? items.map((x,i)=>{const r=x.conflict_record || x; const questions=Array.isArray(r.unresolved_questions)?r.unresolved_questions.join(' • '):r.unresolved_questions || 'UNRESOLVED QUESTION NOT EXPOSED'; return `<div class="v5-cell"><span>CONFLICT ${i+1} / ${esc(r.conflict_type || x.type || 'CONFLICT')}</span><strong>${esc(r.severity || x.severity || 'UNSPECIFIED')}</strong><p>${esc(questions)}</p></div>`;}).join('') : '<p>NO DATA / NO DISAGREEMENT RETURNED. Conflict is never manufactured by the interface.</p>';
    inspector('Conflict Intelligence','DISAGREEMENT INSPECTOR',body);
  }

  function inspectPerspective(card) {
    const id = card?.dataset?.perspective;
    const data = (window.latestAnalysis?.agents || []).find(x => (x.agent_id || x.agent?.agent_id) === id);
    const name = text(card?.querySelector('.agent-name span')) || String(id || 'PERSPECTIVE').toUpperCase();
    q('.agent').forEach(x=>x.classList.remove('v5-active')); card?.classList.add('v5-active');
    if (!data) { inspector(name,'PERSPECTIVE INSPECTOR','<p>NO DATA. This perspective is registered or active, but no returned output is available for the active analysis.</p>'); return; }
    const fields = Object.entries(data).filter(([k])=>!['agent','raw_response'].includes(k)).slice(0,14);
    inspector(name,'PERSPECTIVE INSPECTOR',`<div class="v5-inspector-grid">${fields.map(([k,v])=>`<div class="v5-cell"><span>${esc(k.replaceAll('_',' ').toUpperCase())}</span><strong>${esc(typeof v==='object'?JSON.stringify(v):v)}</strong></div>`).join('')}</div>`);
  }

  function wirePerspectiveDelegation() {
    const root=$('perspectives'); if(!root || root.dataset.v5Bound) return;
    root.dataset.v5Bound='1';
    root.addEventListener('click',e=>{const card=e.target.closest('.agent'); if(card) inspectPerspective(card);});
    root.addEventListener('keydown',e=>{const card=e.target.closest('.agent'); if(card && (e.key==='Enter'||e.key===' ')){e.preventDefault();inspectPerspective(card);}});
  }

  function wireRiskDelegation() {
    const root=$('risk-grid'); if(!root || root.dataset.v5Bound) return;
    root.dataset.v5Bound='1';
    root.addEventListener('click',e=>{const card=e.target.closest('.risk-card');if(!card)return;q('.risk-card').forEach(x=>x.classList.remove('v5-active'));card.classList.add('v5-active');const label=text(card.querySelector('span'));const scenario=(window.latestAnalysis?.simulation?.scenarios||[]);const raw=Array.isArray(scenario)?scenario.find(x=>String(x.scenario||'').toLowerCase()===label.toLowerCase()):scenario[label.toLowerCase()];inspector(label,'RISK SCENARIO INSPECTOR',raw?`<div class="v5-inspector-grid">${Object.entries(raw).map(([k,v])=>`<div class="v5-cell"><span>${esc(k.replaceAll('_',' ').toUpperCase())}</span><strong>${esc(typeof v==='object'?JSON.stringify(v):v)}</strong></div>`).join('')}</div>`:'<p>NO DATA. This scenario has no returned backend record.</p>');});
  }

  function wireConflictDelegation() {
    const root=$('conflicts'); if(!root || root.dataset.v5Bound) return;
    root.dataset.v5Bound='1'; root.addEventListener('click',e=>{const item=e.target.closest('.conflict-item');if(item){q('.conflict-item').forEach(x=>x.classList.remove('v5-active'));item.classList.add('v5-active');inspectConflicts();}});
  }

  function wireActions() {
    $('view-gate-details')?.addEventListener('click',inspectGate);
    $('open-simulation')?.addEventListener('click',()=>{activate('risk','Independent risk simulation');inspectRisk();});
    $('view-conflicts')?.addEventListener('click',()=>{activate('conflict','Conflict and coexistence inspection');inspectConflicts();});
    $('open-analysis')?.addEventListener('click',()=>activate('opportunity','Active analytical question'));
    $('open-learning')?.addEventListener('click',()=>activate('learning','Outcome-dependent institutional learning'));
  }

  function exposeLatestAnalysis() {
    // app.js keeps latestAnalysis private. Mirror it without changing backend semantics.
    if (typeof latestAnalysis !== 'undefined') window.latestAnalysis = latestAnalysis;
  }

  function observer() {
    exposeLatestAnalysis();
    const root=document.querySelector('.primary-column');
    if (!root || root.dataset.v5Observed) return;
    root.dataset.v5Observed='1';
    new MutationObserver(exposeLatestAnalysis).observe(root,{childList:true,subtree:true});
  }

  function init() {
    styles(); wireStages(); wireRecent(); wirePerspectiveDelegation(); wireRiskDelegation(); wireConflictDelegation(); wireActions(); observer();
    announce('AletheiaTelos V5 integration workstation active');
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true}); else init();
})();
