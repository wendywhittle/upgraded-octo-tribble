/* AletheiaTelos Institutional Workstation. Single presentation/interaction layer. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const q = (s, root = document) => Array.from(root.querySelectorAll(s));
  const text = el => (el?.textContent || '').trim();
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  const state = {
    activeCase: null, activeWorkspace: 'opportunity', activeStage: 'OPPORTUNITY',
    activePerspective: null, activeConflict: null, activeRiskScenario: null,
    activeEvidence: null, activeAnalysis: null, history: []
  };

  const stageMap = {
    opportunity:['OPPORTUNITY','active-analysis','opportunity'],
    evidence:['EVIDENCE','evidence','evidence'],
    underwriting:['UNDERWRITING','underwriting-workspace','underwriting'],
    perspectives:['PERSPECTIVES','perspective-summary','perspectives'],
    conflict:['CONFLICT','conflict-intelligence','conflict'],
    risk:['INDEPENDENT RISK','independent-risk','risk'],
    contrarian:['CONTRARIAN','perspective-summary','contrarian'],
    case:['INVESTMENT CASE','investment-case','case'],
    gate:['DECISION GATE','decision-gate','gate'],
    human:['HUMAN AUTHORITY',null,'human'],
    'decision record':['DECISION RECORD',null,'decision-record'],
    outcome:['OUTCOME',null,'outcome'],
    observer:['OBSERVER','observer','observer'],
    attribution:['ATTRIBUTION',null,'attribution'],
    disposition:['DISPOSITION',null,'disposition'],
    learning:['LEARNING','learning','learning'],
    memory:['EPISTEMIC MEMORY','memory','memory']
  };

  const navMap = {
    dashboard:'opportunity', analyses:'opportunity', opportunities:'opportunity', evidence:'evidence', perspectives:'perspectives',
    simulation:'risk', 'investment cases':'case', 'decision gate':'gate', observer:'observer', learning:'learning',
    'capital engine':'opportunity', 'asset engine':'opportunity', 'epistemic memory':'memory', reports:'memory',
    'system status':'opportunity'
  };

  function announce(message) {
    let el = $('workstation-announcer');
    if (!el) { el = document.createElement('div'); el.id = 'workstation-announcer'; el.className = 'sr-only'; el.setAttribute('aria-live','polite'); document.body.appendChild(el); }
    el.textContent = message;
  }

  function exposeLatestAnalysis() {
    if (typeof latestAnalysis !== 'undefined') window.latestAnalysis = latestAnalysis;
    state.activeAnalysis = window.latestAnalysis || state.activeAnalysis || null;
  }

  function ensureContext() {
    const intro = document.querySelector('.workspace-intro');
    if (!intro || $('workstation-context')) return;
    const bar = document.createElement('div');
    bar.id = 'workstation-context';
    bar.className = 'workstation-statusline';
    bar.innerHTML = '<span class="ws-label">ACTIVE CASE</span><b id="workstation-case">NO ACTIVE CASE</b><span class="ws-sep">/</span><span class="ws-label">WORKSPACE</span><b id="workstation-stage">OPPORTUNITY</b><span class="ws-sep">/</span><i id="workstation-stage-detail">Select a lifecycle stage to inspect its workspace.</i>';
    intro.appendChild(bar);
  }

  function ensureContextPanel() {
    const right = document.querySelector('.right-column');
    if (!right || $('workstation-context-panel')) return;
    const panel = document.createElement('section');
    panel.id = 'workstation-context-panel';
    panel.className = 'panel workstation-context-panel';
    panel.innerHTML = '<div class="panel-head"><span>INSTITUTIONAL CONTEXT</span><span>LIVE</span></div><div class="ws-question">WHAT DOES THE INSTITUTION NEED TO KNOW RIGHT NOW?</div><div id="workstation-context-body"><p>Current workspace state will appear here.</p></div>';
    right.insertBefore(panel, right.firstChild);
  }

  function setActiveTarget(target) {
    q('.workstation-active-workspace').forEach(el => el.classList.remove('workstation-active-workspace'));
    if (!target) return;
    target.classList.add('workstation-active-workspace');
    if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex','-1');
    try { target.focus({preventScroll:true}); } catch (_) { target.focus(); }
  }

  function visibleWorkspaceTargets() {
    return ['active-analysis','evidence','underwriting-workspace','perspective-summary','conflict-intelligence','independent-risk','investment-case','decision-gate','observer','learning','memory'];
  }

  function setWorkspaceVisibility(key, targetId) {
    const targets = visibleWorkspaceTargets();
    targets.forEach(id => {
      const el = $(id);
      if (!el) return;
      const isTarget = id === targetId;
      el.classList.toggle('workstation-hidden', !isTarget);
      el.setAttribute('aria-hidden', isTarget ? 'false' : 'true');
    });
  }

  function updateContext(key, detail) {
    const body = $('workstation-context-body');
    if (!body) return;
    const prompts = {
      opportunity:['CASE STATE','What is the question being investigated?'],
      evidence:['EVIDENCE TRACEABILITY','What evidence is validated, usable, missing, or unresolved?'],
      underwriting:['ECONOMIC LOGIC','What assumptions drive the underwriting?'],
      perspectives:['KALEIDOSCOPE','Where do analytical lenses converge, diverge, or remain uncertain?'],
      conflict:['CONFLICT / COEXISTENCE','What disagreement remains unresolved?'],
      risk:['INDEPENDENT RISK','Where is the distribution most fragile?'],
      contrarian:['THESIS DESTRUCTION','What could make this case wrong?'],
      case:['INVESTMENT CASE','What does the assembled analytical case actually establish?'],
      gate:['DECISION READINESS','What prevents or supports readiness for human review?'],
      human:['HUMAN AUTHORITY','What requires human judgment?'],
      'decision-record':['DECISION RECORD','Has a formal human decision record actually been persisted?'],
      outcome:['OUTCOME','What has actually happened since the decision?'],
      observer:['OBSERVATION','What has actually been observed?'],
      attribution:['ATTRIBUTION','What realized result can actually be attributed?'],
      disposition:['DISPOSITION','What is known about the terminal holding phase?'],
      learning:['LEARNING','What has actually been learned from resolved outcomes?'],
      memory:['EPISTEMIC MEMORY','What institutional history is actually available?']
    };
    const p = prompts[key] || ['WORKSTATION','Inspect the returned analytical state.'];
    body.innerHTML = `<div class="ws-context-state">${esc(p[0])}</div><strong>${esc(p[1])}</strong><p>${esc(detail || 'Only information returned by the current system is displayed.')}</p>`;
    if (state.activeCase?.case_id) body.innerHTML += `<div class="ws-context-id"><span>CASE ID</span><b>${esc(state.activeCase.case_id)}</b></div>`;
  }

  function syncCase() {
    exposeLatestAnalysis();
    const candidate = window.latestAnalysis?.institutional_investment_case;
    if (candidate && (candidate.case_id || candidate.case_version)) state.activeCase = candidate;
    const caseEl = $('workstation-case');
    if (caseEl) caseEl.textContent = state.activeCase?.case_id ? `${state.activeCase.case_id}${state.activeCase.case_version ? ` / v${state.activeCase.case_version}` : ''}` : 'NO ACTIVE CASE';
  }

  function activate(name, detail, meta = {}) {
    const key = String(name || '').toLowerCase().trim();
    const mapped = stageMap[key] || [String(name || 'WORKSTATION').toUpperCase(), null, key];
    const previous = state.activeWorkspace;
    if (previous && previous !== key) state.history.push(previous);
    state.activeWorkspace = key;
    state.activeStage = mapped[0];
    Object.assign(state, meta);
    syncCase();

    document.body.dataset.activeWorkspace = key;
    document.body.dataset.activeStage = mapped[0].toLowerCase();
    const label = $('workstation-stage');
    const info = $('workstation-stage-detail');
    if (label) label.textContent = mapped[0];
    if (info) info.textContent = detail || mapped[0];

    q('.stage').forEach(x => {
      const n = text(x.querySelector('.stage-name')).toLowerCase();
      x.classList.toggle('workstation-current', n === mapped[0].toLowerCase());
      x.setAttribute('aria-current', n === mapped[0].toLowerCase() ? 'step' : 'false');
    });
    q('.nav-item').forEach(item => {
      const labelText = text(item).replace(/\s+NOT EXPOSED$/i,'').trim().toLowerCase();
      const navKey = navMap[labelText];
      item.classList.toggle('active', navKey === key);
    });

    setWorkspaceVisibility(key, mapped[1]);
    const target = $(mapped[1]);
    setActiveTarget(target);
    updateContext(key, detail);
    announce(`Active workstation context: ${mapped[0]}`);

    if (!target && ['human','decision-record','outcome','attribution','disposition'].includes(key)) {
      inspectBox(mapped[0], 'BOUNDARY / MATURITY INSPECTOR', unavailableMessage(key));
    }
  }

  function unavailableMessage(key) {
    const messages = {
      human:'HUMAN DECISION WORKFLOW NOT YET OPERATIONAL. Human authority remains outside this interface.',
      'decision-record':'DECISION RECORD NOT YET OPERATIONAL. Recent analytical runs are not represented as historical human decisions.',
      outcome:'OUTCOME NOT YET OPERATIONAL. No realized outcome is manufactured by the workstation.',
      attribution:'ATTRIBUTION NOT YET OPERATIONAL. No realized performance attribution is manufactured.',
      disposition:'DISPOSITION NOT YET OPERATIONAL. This interface does not execute or authorize disposal.'
    };
    return `<p>${esc(messages[key] || 'NOT YET OPERATIONAL')}</p>`;
  }

  function interceptLegacyNavigation() {
    const stop = event => {
      const stage = event.target.closest?.('.stage');
      if (stage) { event.preventDefault(); event.stopImmediatePropagation(); activate(text(stage.querySelector('.stage-name')), text(stage.querySelector('.stage-desc')) || 'Lifecycle stage selected'); }
    };
    $('pipeline-stages')?.addEventListener('click', stop, true);
    q('.nav-item[href^="#"]').forEach(item => item.addEventListener('click', event => {
      if (item.classList.contains('disabled')) return;
      const label = text(item).replace(/\s+NOT EXPOSED$/i,'').trim().toLowerCase();
      if (!navMap[label]) return;
      event.preventDefault(); event.stopImmediatePropagation(); activate(navMap[label], `Workspace: ${text(item)}`);
    }, true));
  }

  function wireNavigation() {
    q('.nav-item[href^="#"]').forEach(item => {
      if (item.dataset.workstationBound) return;
      item.dataset.workstationBound = '1';
      item.addEventListener('click', event => {
        if (item.classList.contains('disabled')) return;
        const label = text(item).replace(/\s+NOT EXPOSED$/i,'').trim().toLowerCase();
        if (!navMap[label]) return;
        event.preventDefault(); activate(navMap[label], `Workspace: ${text(item)}`);
      });
    });
  }

  function wireStages() {
    const pipeline = $('pipeline-stages');
    if (!pipeline || pipeline.dataset.workstationBound) return;
    pipeline.dataset.workstationBound = '1';
    pipeline.addEventListener('click', event => {
      const stage = event.target.closest('.stage'); if (!stage) return;
      event.preventDefault(); event.stopPropagation();
      activate(text(stage.querySelector('.stage-name')), text(stage.querySelector('.stage-desc')) || 'Lifecycle stage selected');
    });
  }

  function inspectBox(title, subtitle, body) {
    let box = $('workstation-inspector');
    if (!box) {
      box = document.createElement('section'); box.id = 'workstation-inspector'; box.className = 'workstation-inspector';
      (document.querySelector('.primary-column') || document.body).appendChild(box);
    }
    box.innerHTML = `<div class="workstation-state">${esc(subtitle)}</div><h3>${esc(title)}</h3>${body}`;
    box.hidden = false; box.setAttribute('tabindex','-1');
    try { box.focus({preventScroll:true}); } catch (_) { box.focus(); }
  }

  function inspectGate() {
    exposeLatestAnalysis(); const gate = window.latestAnalysis?.decision_gate || {}; const readiness = window.latestAnalysis?.decision_readiness || {};
    const stops = Array.isArray(gate.hard_stops) ? gate.hard_stops : []; const blockers = Array.isArray(gate.blocking_reasons) ? gate.blocking_reasons : [];
    const mandatory = Array.isArray(readiness.mandatory_conditions) ? readiness.mandatory_conditions : []; const evidence = gate.evidence_status || {};
    const cells = [['READINESS',readiness.status || gate.state || text($('gate-substate')) || 'NO DATA'],['EVIDENCE',`${evidence.count ?? 'NOT EXPOSED'} VALIDATED / ${evidence.usable_count ?? 'NOT EXPOSED'} USABLE`],['CONFLICT',`${(gate.unresolved_conflicts || []).length} UNRESOLVED`],['INDEPENDENT RISK',gate.independent_risk ? 'RETURNED' : 'NO DATA'],['CONTRARIAN',gate.contrarian_review_status || 'NOT EXPOSED'],['HUMAN AUTHORITY',gate.human_decision_required === true ? 'REQUIRED' : 'NOT EXPOSED']];
    const list=(title,values)=>values.length?`<p><b>${title}</b></p><ul class="workstation-list">${values.map(x=>`<li>${esc(typeof x==='string'?x:JSON.stringify(x))}</li>`).join('')}</ul>`:'';
    inspectBox('Decision Gate','GOVERNANCE INSPECTOR',`<div class="workstation-grid">${cells.map(c=>`<div class="workstation-cell"><span>${esc(c[0])}</span><strong>${esc(c[1])}</strong></div>`).join('')}</div>${list('HARD STOPS',stops)}${list('BLOCKING REASONS',blockers)}${list('MANDATORY CONDITIONS',mandatory)}<p>READY FOR HUMAN AUTHORITY ≠ AUTHORIZED ≠ EXECUTED. This interface cannot authorize or execute an investment decision.</p>`);
  }

  function inspectRisk() {
    exposeLatestAnalysis(); const sim=window.latestAnalysis?.simulation||{}; const scenarios=Array.isArray(sim.scenarios)?sim.scenarios:Object.values(sim.scenarios||{});
    const body=scenarios.length?`<div class="workstation-grid">${scenarios.map(x=>`<div class="workstation-cell"><span>${esc(x.scenario||'SCENARIO')}</span><strong>MEAN TERMINAL: ${esc(x.mean_terminal??'NOT AVAILABLE')}</strong><small>LOSS: ${esc(x.probability_loss??'NOT AVAILABLE')} • DRAWDOWN: ${esc(x.max_drawdown_mean??'NOT AVAILABLE')}</small></div>`).join('')}</div><p>Simulation output is displayed from the returned analysis result and remains independent of agent conclusions.</p>`:'<p>NO DATA. No returned simulation scenarios are available for the active analysis.</p>';
    inspectBox('Independent Risk','SIMULATION INSPECTOR',body);
  }

  function inspectConflicts() {
    exposeLatestAnalysis(); const data=window.latestAnalysis||{}; const items=[...(data.conflicts||[]),...(data.horizon_divergences||[])];
    const body=items.length?items.map((x,i)=>{const r=x.conflict_record||x;const questions=Array.isArray(r.unresolved_questions)?r.unresolved_questions.join(' • '):r.unresolved_questions||'UNRESOLVED QUESTION NOT EXPOSED';return `<div class="workstation-cell"><span>CONFLICT ${i+1} / ${esc(r.conflict_type||x.type||'CONFLICT')}</span><strong>${esc(r.severity||x.severity||'UNSPECIFIED')}</strong><p>${esc(questions)}</p></div>`}).join(''):'<p>NO DATA / NO DISAGREEMENT RETURNED. Conflict is never manufactured by the interface.</p>';
    inspectBox('Conflict Intelligence','DISAGREEMENT INSPECTOR',body);
  }

  function inspectPerspective(card) {
    exposeLatestAnalysis(); const id=card?.dataset?.perspective; const data=(window.latestAnalysis?.agents||[]).find(x=>(x.agent_id||x.agent?.agent_id)===id); const name=text(card?.querySelector('.agent-name span'))||String(id||'PERSPECTIVE').toUpperCase();
    q('.agent').forEach(x=>x.classList.remove('workstation-active')); card?.classList.add('workstation-active'); state.activePerspective=id;
    if(!data){inspectBox(name,'PERSPECTIVE INSPECTOR','<p>NO DATA. No returned output is available for this perspective.</p>');return;}
    const fields=Object.entries(data).filter(([k])=>!['agent','raw_response'].includes(k)).slice(0,14);
    inspectBox(name,'PERSPECTIVE INSPECTOR',`<div class="workstation-grid">${fields.map(([k,v])=>`<div class="workstation-cell"><span>${esc(k.replaceAll('_',' ').toUpperCase())}</span><strong>${esc(typeof v==='object'?JSON.stringify(v):v)}</strong></div>`).join('')}</div>`);
  }

  function wireInspectors() {
    const perspectives=$('perspectives'); if(perspectives&&!perspectives.dataset.workstationBound){perspectives.dataset.workstationBound='1';perspectives.addEventListener('click',e=>{const card=e.target.closest('.agent');if(card)inspectPerspective(card)});perspectives.addEventListener('keydown',e=>{const card=e.target.closest('.agent');if(card&&(e.key==='Enter'||e.key===' ')){e.preventDefault();inspectPerspective(card)}});}
    const risk=$('risk-grid'); if(risk&&!risk.dataset.workstationBound){risk.dataset.workstationBound='1';risk.addEventListener('click',e=>{const card=e.target.closest('.risk-card');if(!card)return;q('.risk-card').forEach(x=>x.classList.remove('workstation-active'));card.classList.add('workstation-active');const label=text(card.querySelector('span'));state.activeRiskScenario=label;exposeLatestAnalysis();const scenarios=window.latestAnalysis?.simulation?.scenarios||[];const raw=Array.isArray(scenarios)?scenarios.find(x=>String(x.scenario||'').toLowerCase()===label.toLowerCase()):null;inspectBox(label,'RISK SCENARIO INSPECTOR',raw?`<div class="workstation-grid">${Object.entries(raw).map(([k,v])=>`<div class="workstation-cell"><span>${esc(k.replaceAll('_',' ').toUpperCase())}</span><strong>${esc(typeof v==='object'?JSON.stringify(v):v)}</strong></div>`).join('')}</div>`:'<p>NO DATA. This scenario has no returned backend record.</p>')});}
    const conflicts=$('conflicts'); if(conflicts&&!conflicts.dataset.workstationBound){conflicts.dataset.workstationBound='1';conflicts.addEventListener('click',e=>{const item=e.target.closest('.conflict-item');if(item){q('.conflict-item').forEach(x=>x.classList.remove('workstation-active'));item.classList.add('workstation-active');state.activeConflict=text(item);inspectConflicts()}});}
  }

  function wireRecent() {
    const root = $('recent-analyses'); if (!root || root.dataset.workstationBound) return;
    root.dataset.workstationBound='1'; root.addEventListener('click',event=>{const item=event.target.closest('.recent-item');if(!item)return;q('.recent-item').forEach(x=>x.classList.remove('workstation-active'));item.classList.add('workstation-active');const question=text($('active-question'))||text(item);activate('opportunity',`ACTIVE ANALYSIS: ${question}`)});
  }

  function wireActions() {
    $('view-gate-details')?.addEventListener('click',()=>{activate('gate','Decision Gate readiness and human authority requirements');inspectGate()});
    $('open-simulation')?.addEventListener('click',()=>{activate('risk','Independent risk simulation');inspectRisk()});
    $('view-conflicts')?.addEventListener('click',()=>{activate('conflict','Conflict and coexistence inspection');inspectConflicts()});
    $('open-analysis')?.addEventListener('click',()=>activate('opportunity','Active analytical question'));
    $('open-learning')?.addEventListener('click',()=>activate('learning','Outcome-dependent institutional learning'));
  }

  function wireSearch() {
    const input=$('global-search'); if(!input||input.dataset.workstationBound)return; input.dataset.workstationBound='1';
    let box=$('workstation-search-results'); if(!box){box=document.createElement('div');box.id='workstation-search-results';box.className='workstation-search-results';box.hidden=true;input.closest('.search')?.appendChild(box);}
    const groups=[['ANALYSES','.recent-item','opportunity'],['OPPORTUNITIES','.stage','opportunity'],['PERSPECTIVES','.agent','perspectives'],['CONFLICT','.conflict-item','conflict'],['ACTIVITY','.activity-item','observer']];
    input.setAttribute('placeholder','Search loaded analytical data...');
    input.addEventListener('input',()=>{const term=input.value.trim().toLowerCase();if(!term){box.hidden=true;return;}let html='',n=0;groups.forEach(([label,selector])=>{const hits=q(selector).filter(el=>text(el).toLowerCase().includes(term));if(!hits.length)return;html+=`<div class="workstation-search-group">${label}</div>`;hits.slice(0,8).forEach(el=>{const id=`r${n++}`;el.dataset.workstationResult=id;html+=`<button type="button" class="workstation-search-result" data-result="${id}">${esc(text(el).slice(0,100)||'Untitled')}<small>${label}</small></button>`})});box.innerHTML=html||'<div class="workstation-search-group">NO MATCHING RETURNED WORKSTATION DATA</div>';box.hidden=false;q('.workstation-search-result',box).forEach(btn=>btn.addEventListener('click',()=>{const el=document.querySelector(`[data-workstation-result="${CSS.escape(btn.dataset.result)}"]`);if(el){activate(el.classList.contains('stage')?text(el.querySelector('.stage-name')):el.closest('.agent')?'perspectives':el.closest('.conflict-item')?'conflict':el.closest('.activity-item')?'observer':'opportunity',text(el));}box.hidden=true;input.blur()}))});
    document.addEventListener('click',e=>{if(!input.closest('.search')?.contains(e.target))box.hidden=true});
  }

  function addStyles() {
    if($('workstation-styles'))return;
    const s=document.createElement('style'); s.id='workstation-styles'; s.textContent=`
      .workstation-hidden{display:none!important}
      .stage.workstation-current{outline:2px solid var(--cyan,#54d6ff);outline-offset:2px;box-shadow:0 0 0 1px rgba(84,214,255,.16)}
      .workstation-active-workspace{outline:1px solid rgba(84,214,255,.25);outline-offset:2px}
      .recent-item.workstation-active,.agent.workstation-active,.risk-card.workstation-active,.conflict-item.workstation-active{outline:1px solid var(--cyan,#54d6ff);background:rgba(84,214,255,.07)}
      .workstation-statusline{display:grid;grid-template-columns:auto minmax(0,1fr) auto auto minmax(0,2fr);gap:10px;align-items:center;margin-top:12px;padding:9px 12px;border:1px solid rgba(84,214,255,.2);background:rgba(5,14,22,.88);font-size:10px;text-transform:uppercase;letter-spacing:.08em}
      .workstation-statusline b{color:var(--cyan,#54d6ff);overflow:hidden;text-overflow:ellipsis}.workstation-statusline i{color:var(--muted,#8293a3);font-style:normal;overflow:hidden;text-overflow:ellipsis}.ws-label,.ws-sep{color:var(--muted,#8293a3);font-size:9px}.ws-sep{opacity:.5}
      .workstation-context-panel{border-color:rgba(84,214,255,.2)}.ws-question{font-size:11px;letter-spacing:.09em;line-height:1.45;margin:4px 0 12px}.ws-context-state{font-size:9px;letter-spacing:.12em;color:var(--cyan,#54d6ff);margin-bottom:5px}.ws-context-id{display:flex;justify-content:space-between;gap:8px;border-top:1px solid rgba(255,255,255,.08);margin-top:12px;padding-top:9px;font-size:9px}.ws-context-id span{color:var(--muted,#8293a3)}
      .workstation-inspector{margin-top:12px;padding:14px;border:1px solid rgba(84,214,255,.2);background:rgba(5,14,22,.88)}.workstation-inspector h3{margin:5px 0 10px}.workstation-state{font-size:10px;letter-spacing:.1em;color:var(--cyan,#54d6ff);text-transform:uppercase}.workstation-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.workstation-cell{border:1px solid rgba(255,255,255,.08);padding:10px;min-width:0}.workstation-cell span{display:block;font-size:9px;letter-spacing:.1em;color:var(--muted,#8293a3);margin-bottom:5px}.workstation-cell strong{display:block;font-size:12px;overflow-wrap:anywhere}.workstation-list{margin:8px 0;padding-left:18px}.workstation-list li{margin:5px 0;color:#b7c4ce}
      .workstation-search-results{position:absolute;top:calc(100% + 7px);left:0;right:0;z-index:900;background:#07111a;border:1px solid rgba(84,214,255,.28);max-height:min(65vh,520px);overflow:auto;box-shadow:0 18px 45px rgba(0,0,0,.5)}.workstation-search-group{padding:8px 10px 4px;color:var(--cyan,#54d6ff);font-size:9px;letter-spacing:.12em}.workstation-search-result{display:block;width:100%;text-align:left;background:transparent;border:0;border-top:1px solid rgba(255,255,255,.05);color:inherit;padding:11px 12px;cursor:pointer;min-height:44px}.workstation-search-result:hover,.workstation-search-result:focus{background:rgba(84,214,255,.08)}.workstation-search-result small{display:block;color:var(--muted,#8293a3);margin-top:3px}
      @media(max-width:1100px){.workstation-statusline{grid-template-columns:auto 1fr;}.ws-sep{display:none}.workstation-statusline i{grid-column:2}}
      @media(max-width:760px){.workstation-grid{grid-template-columns:1fr}.workstation-statusline{align-items:start;grid-template-columns:1fr}.workstation-statusline i{grid-column:1}.workstation-inspector{font-size:13px}.workstation-search-results{position:fixed;left:8px;right:8px;top:70px;max-height:70vh}.right-column{margin-top:12px}}
      @media(hover:none){.workstation-search-result:hover{background:transparent}}
    `; document.head.appendChild(s);
  }

  function observeDynamicContent(){
    ['pipeline-stages','recent-analyses','perspectives','risk-grid','conflicts'].map($).filter(Boolean).forEach(root=>new MutationObserver(()=>{exposeLatestAnalysis();syncCase();wireNavigation();wireInspectors()}).observe(root,{childList:true,subtree:true}));
  }

  function init(){
    addStyles(); ensureContext(); ensureContextPanel(); wireNavigation(); wireStages(); interceptLegacyNavigation(); wireRecent(); wireInspectors(); wireActions(); wireSearch(); exposeLatestAnalysis(); syncCase(); observeDynamicContent();
    activate('opportunity','Current analytical workspace');
    announce('AletheiaTelos institutional intelligence workstation ready');
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
