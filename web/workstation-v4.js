/* AletheiaTelos workstation v4. Presentation/interaction layer only. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const q = (s, root=document) => Array.from(root.querySelectorAll(s));
  const text = el => (el?.textContent || '').trim();
  const esc = v => String(v ?? '').replace(/[&<>\"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
  let activeStage = 'opportunity';

  function announce(message) {
    let el = $('workstation-announcer');
    if (!el) { el = document.createElement('div'); el.id = 'workstation-announcer'; el.className = 'sr-only'; el.setAttribute('aria-live','polite'); document.body.appendChild(el); }
    el.textContent = message;
  }

  function addStyles() {
    if ($('workstation-v4-styles')) return;
    const s = document.createElement('style'); s.id = 'workstation-v4-styles';
    s.textContent = `
      .stage.v4-current{outline:2px solid var(--cyan,#54d6ff);outline-offset:2px;box-shadow:0 0 0 1px rgba(84,214,255,.18),0 8px 28px rgba(0,0,0,.24)}
      .recent-item.v4-active,.agent.selected,.conflict-item.v4-selected,.risk-card.v4-selected{outline:1px solid var(--cyan,#54d6ff);background:rgba(84,214,255,.07)}
      .v4-context{display:flex;gap:12px;align-items:center;justify-content:space-between;margin:10px 0 0;padding:9px 12px;border:1px solid rgba(84,214,255,.18);background:rgba(5,14,22,.75);font-size:11px;text-transform:uppercase;letter-spacing:.08em}
      .v4-context b{color:var(--cyan,#54d6ff)} .v4-context span{color:var(--muted,#8293a3)}
      .v4-modal-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.68);z-index:1000;display:flex;align-items:flex-start;justify-content:flex-end;padding:18px}
      .v4-modal{width:min(620px,100%);max-height:calc(100vh - 36px);overflow:auto;background:#07111a;border:1px solid rgba(84,214,255,.35);box-shadow:0 24px 70px rgba(0,0,0,.55);padding:20px;color:inherit}
      .v4-modal-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;border-bottom:1px solid rgba(255,255,255,.08);padding-bottom:14px;margin-bottom:16px}
      .v4-modal h2{margin:0;font-size:17px}.v4-modal .v4-kicker{font-size:10px;letter-spacing:.12em;color:var(--cyan,#54d6ff);margin-bottom:5px}.v4-close{border:1px solid rgba(255,255,255,.14);background:transparent;color:inherit;width:40px;height:40px;font-size:22px;cursor:pointer}
      .v4-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.v4-cell{border:1px solid rgba(255,255,255,.08);padding:11px}.v4-cell span{display:block;font-size:9px;color:var(--muted,#8293a3);letter-spacing:.1em;margin-bottom:5px}.v4-cell strong{font-size:12px;overflow-wrap:anywhere}.v4-body{line-height:1.55;color:#b7c4ce;font-size:13px}.v4-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}
      .v4-search-results{position:absolute;top:calc(100% + 7px);left:0;right:0;z-index:900;background:#07111a;border:1px solid rgba(84,214,255,.28);max-height:min(65vh,520px);overflow:auto;box-shadow:0 18px 45px rgba(0,0,0,.5)}
      .v4-search-group{padding:8px 10px 4px;color:var(--cyan,#54d6ff);font-size:9px;letter-spacing:.12em}.v4-search-result{display:block;width:100%;text-align:left;background:transparent;border:0;border-top:1px solid rgba(255,255,255,.05);color:inherit;padding:10px 12px;cursor:pointer}.v4-search-result:hover,.v4-search-result:focus{background:rgba(84,214,255,.08)}.v4-search-result small{display:block;color:var(--muted,#8293a3);margin-top:3px}
      @media(max-width:760px){.v4-modal-backdrop{padding:0;align-items:stretch}.v4-modal{width:100%;max-height:100vh}.v4-grid{grid-template-columns:1fr}.v4-context{align-items:flex-start;flex-direction:column}}
    `; document.head.appendChild(s);
  }

  function contextBar() {
    const intro = document.querySelector('.workspace-intro'); if (!intro || $('v4-context')) return;
    const bar = document.createElement('div'); bar.id='v4-context'; bar.className='v4-context';
    bar.innerHTML='<span>ACTIVE WORKSTATION CONTEXT</span><b id="v4-stage-label">OPPORTUNITY</b><span id="v4-stage-detail">Select a lifecycle stage to inspect its workspace.</span>';
    intro.appendChild(bar);
  }

  const stageMeta = {
    opportunity:['OPPORTUNITY','Active analytical question and opportunity context','active-analysis'], evidence:['EVIDENCE','Validated inputs, provenance and usable evidence','evidence'], underwriting:['UNDERWRITING','Existing CRE underwriting workspace','underwriting-workspace'], perspectives:['PERSPECTIVES','Competing analytical perspectives','perspective-summary'], conflict:['CONFLICT','Disagreement and unresolved questions','conflict-intelligence'], risk:['INDEPENDENT RISK','Independent scenario simulation','independent-risk'], contrarian:['CONTRARIAN','Adversarial review represented by returned perspective data','perspective-summary'], case:['INVESTMENT CASE','Investment case state from the existing system','investment-case'], gate:['DECISION GATE','Readiness boundary and human authority requirements','decision-gate'], observer:['OBSERVER','Real-world observation and recent activity','observer'], learning:['LEARNING','Outcome-dependent institutional learning','learning']
  };

  function activateStage(name, target) {
    const meta=stageMeta[name] || [String(name).toUpperCase(),'Existing workstation context',target]; activeStage=name;
    q('.stage').forEach(x=>x.classList.toggle('v4-current', text(x.querySelector('.stage-name')).toLowerCase()===name));
    $('v4-stage-label').textContent=meta[0]; $('v4-stage-detail').textContent=meta[1];
    const panel=$(meta[2]||target); if(panel) panel.scrollIntoView({behavior:'smooth',block:'start'});
    announce(`Active workstation context: ${meta[0]}`);
  }

  function wireStages() {
    q('.stage').forEach(stage => stage.addEventListener('click', () => {
      const name=(stage.querySelector('.stage-name')?.textContent||'').trim().toLowerCase(); activateStage(name, stage.dataset.target);
    }));
  }

  function wireRecent() {
    const root=$('recent-analyses'); if(!root) return;
    const bind=()=>q('.recent-item, #recent-analyses button, #recent-analyses [role="button"]',root).forEach(item=>{
      if(item.dataset.v4Bound) return; item.dataset.v4Bound='1';
      item.addEventListener('click',()=>setTimeout(()=>{
        q('.recent-item').forEach(x=>x.classList.remove('v4-active')); item.classList.add('v4-active');
        const question=text($('active-question')); if(question) { $('v4-stage-detail').textContent=`Active analysis: ${question}`; }
        activateStage('opportunity','active-analysis');
      },30));
    });
    bind(); new MutationObserver(bind).observe(root,{childList:true,subtree:true});
  }

  function modal(title,kicker,body,actions=[]) {
    q('.v4-modal-backdrop').forEach(x=>x.remove());
    const backdrop=document.createElement('div'); backdrop.className='v4-modal-backdrop';
    backdrop.innerHTML=`<section class="v4-modal" role="dialog" aria-modal="true" aria-label="${esc(title)}"><div class="v4-modal-head"><div><div class="v4-kicker">${esc(kicker)}</div><h2>${esc(title)}</h2></div><button class="v4-close" aria-label="Close">×</button></div><div class="v4-body">${body}</div><div class="v4-actions">${actions.map(a=>`<button class="secondary" data-v4-action="${esc(a.id)}">${esc(a.label)}</button>`).join('')}</div></section>`;
    document.body.appendChild(backdrop); backdrop.querySelector('.v4-close').focus();
    backdrop.addEventListener('click',e=>{if(e.target===backdrop)backdrop.remove();}); backdrop.querySelector('.v4-close').addEventListener('click',()=>backdrop.remove());
    actions.forEach(a=>backdrop.querySelector(`[data-v4-action="${CSS.escape(a.id)}"]`)?.addEventListener('click',()=>{a.run?.();backdrop.remove();}));
    return backdrop;
  }

  function inspectGate() {
    const vals=[['READINESS',text($('gate-substate'))||'NO DATA'],['EVIDENCE',text($('gate-evidence'))||'NOT AVAILABLE'],['CONFLICT',text($('gate-conflict'))||'NOT AVAILABLE'],['INDEPENDENT RISK',text($('gate-risk'))||'NOT AVAILABLE'],['CONTRARIAN',text($('gate-contrarian'))||'NOT AVAILABLE'],['HARD STOPS',text($('hard-stops'))||'NONE RETURNED'],['AUTHORIZATION','HUMAN REQUIRED']];
    modal('Decision Gate','HUMAN AUTHORITY BOUNDARY',`<div class="v4-grid">${vals.map(v=>`<div class="v4-cell"><span>${esc(v[0])}</span><strong>${esc(v[1])}</strong></div>`).join('')}</div><p>The gate is an inspection surface only. READY FOR HUMAN AUTHORITY does not authorize or execute an investment decision.</p>`);
  }

  function inspectRisk() {
    const cards=q('.risk-card').map(x=>({name:text(x.querySelector('span')),value:text(x.querySelector('strong')),detail:text(x.querySelector('em'))}));
    modal('Independent Risk','SIMULATION INSPECTOR',cards.length?`<div class="v4-grid">${cards.map(c=>`<div class="v4-cell"><span>${esc(c.name)}</span><strong>${esc(c.value)}</strong><small>${esc(c.detail)}</small></div>`).join('')}</div><p>These displayed scenario results are the current simulation output. They are analytically separate from agent conclusions.</p>`:'<p>NO DATA. No returned scenario results are available for the active analysis.</p>');
  }

  function inspectConflicts() {
    const items=q('.conflict-item');
    modal('Conflict Intelligence','DISAGREEMENT INSPECTOR',items.length?items.map((x,i)=>`<div class="v4-cell"><span>CONFLICT ${i+1}</span><strong>${esc(text(x))}</strong></div>`).join(''):'<p>NO DATA / NO DISAGREEMENT RETURNED. The system does not manufacture conflict.</p>');
  }

  function wireActions() {
    const actions={
      'open-analysis':()=>{activateStage('opportunity','active-analysis'); $('active-analysis')?.scrollIntoView({behavior:'smooth',block:'start'});},
      'open-simulation':()=>{activateStage('risk','independent-risk');inspectRisk();},
      'view-conflicts':()=>{activateStage('conflict','conflict-intelligence');inspectConflicts();},
      'view-gate-details':()=>{activateStage('gate','decision-gate');inspectGate();},
      'open-learning':()=>{activateStage('learning','learning');}
    };
    Object.entries(actions).forEach(([id,fn])=>$(id)?.addEventListener('click',fn));
  }

  function wirePerspectiveInspector() {
    const root=$('perspectives'); if(!root)return;
    const bind=()=>q('.agent',root).forEach(card=>{if(card.dataset.v4Bound)return;card.dataset.v4Bound='1';card.setAttribute('aria-label',`${text(card.querySelector('.agent-name span'))||'Perspective'} inspector`);});
    bind();new MutationObserver(bind).observe(root,{childList:true,subtree:true});
  }

  function buildSearchResults() {
    const input=$('global-search'); if(!input)return;
    const searchWrap=input.closest('.search'); if(!searchWrap)return;
    searchWrap.style.position='relative';
    const box=document.createElement('div'); box.id='v4-search-results';box.className='v4-search-results';box.hidden=true;searchWrap.appendChild(box);
    const groups=[['ANALYSES','.recent-item','active-analysis'],['OPPORTUNITIES','.stage','pipeline'],['PERSPECTIVES','.agent','perspective-summary'],['CONFLICT','.conflict-item','conflict-intelligence'],['ACTIVITY','.activity-item','observer']];
    input.addEventListener('input',()=>{const term=input.value.trim().toLowerCase(); if(!term){box.hidden=true;return;} let html='',count=0; groups.forEach(([label,selector,target])=>{const hits=q(selector).filter(el=>text(el).toLowerCase().includes(term));if(!hits.length)return;html+=`<div class="v4-search-group">${label}</div>`;hits.slice(0,8).forEach((el,i)=>{const id=`r${count++}`;html+=`<button class="v4-search-result" data-result="${id}">${esc(text(el).slice(0,100)||'Untitled')}<small>${label}</small></button>`;el.dataset.v4Result=id;});});box.innerHTML=html||'<div class="v4-search-group">NO MATCHING RETURNED WORKSTATION DATA</div>';box.hidden=false; q('.v4-search-result',box).forEach(btn=>btn.addEventListener('click',()=>{const el=document.querySelector(`[data-v4-result="${CSS.escape(btn.dataset.result)}"]`);if(el){const stage=el.closest('.stage'); if(stage){activateStage((text(stage.querySelector('.stage-name'))||'').toLowerCase(),stage.dataset.target);} else {const match=el.closest('.recent-item,.agent,.conflict-item,.activity-item');const target=match?.closest('#recent-analyses')?'active-analysis':match?.closest('#perspectives')?'perspective-summary':match?.closest('#conflicts')?'conflict-intelligence':'observer';activateStage(target==='active-analysis'?'opportunity':target==='perspective-summary'?'perspectives':target==='conflict-intelligence'?'conflict':'observer',target);match?.focus?.();} input.blur();box.hidden=true;}})); });
    document.addEventListener('click',e=>{if(!searchWrap.contains(e.target))box.hidden=true;});
  }

  function init(){
    addStyles(); contextBar(); wireStages(); wireRecent(); wireActions(); wirePerspectiveInspector(); buildSearchResults();
    announce('AletheiaTelos V4 institutional workstation active');
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true}); else init();
})();
