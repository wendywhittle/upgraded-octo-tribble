(() => {
  const $ = (id) => document.getElementById(id);
  const value = (id) => Number($(id).value);
  const money = (v) => v == null ? 'UNKNOWN' : new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(v);
  const pct = (v) => v == null ? 'UNKNOWN' : `${(v*100).toFixed(2)}%`;
  const esc = (v) => String(v ?? 'UNKNOWN').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const card = (title, body, type='CALCULATION') => `<article class="p9-card"><div class="p9-card-head"><strong>${title}</strong><span class="p9-type">${type}</span></div>${body}</article>`;
  const row = (k,v,t='CALCULATION') => `<div class="p9-row"><span>${esc(k)}</span><strong>${esc(v)}</strong><small>${t}</small></div>`;
  function render(a, meta) {
    const p = a.proforma;
    const f = a.financing;
    const years = p.annual || [];
    const scenarios = a.scenarios || [];
    const sims = a.simulations || [];
    const findings = (a.contrarian && a.contrarian.findings) || [];
    const thesis = a.synthesis && a.synthesis.thesis || {};
    const disagreements = a.synthesis && a.synthesis.disagreements || [];
    let html = '';
    html += `<div class="p9-banner">ASSEMBLY: <strong>${esc(a.status)}</strong> · RECOMMENDATION: <strong>${esc(a.recommendation)}</strong></div>`;
    html += `<div class="p9-results-grid">`;
    html += card('DEAL', row('Asset',a.case_identity,'ASSUMPTION')+row('Inputs','User-supplied underwriting assumptions','ASSUMPTION'));
    html += card('PRO FORMA', row('Acquisition Basis',money(p.acquisition_basis))+row('Year 1 NOI',money(years[0]?.noi))+row('Final NOI',money(years.at(-1)?.noi))+row('Entry Valuation',money(p.entry_valuation))+row('Exit Valuation',money(p.exit_valuation))+row('Unlevered IRR',pct(p.unlevered_irr))+row('Equity Multiple',p.unlevered_equity_multiple?.toFixed(2)+'x'));
    html += card('SCENARIOS', scenarios.map(s => `<div class="p9-scenario"><b>${esc(s.scenario?.name || s.scenario?.key || 'SCENARIO')}</b>${row('NOI',money(s.proforma?.annual?.[0]?.noi))}${row('IRR',pct(s.proforma?.unlevered_irr))}</div>`).join(''));
    html += card('SIMULATION', sims.map(s => { const x=s.simulation || {}; return `<div class="p9-scenario"><b>${esc(s.scenario?.name || s.scenario?.key || 'SCENARIO')}</b>${row('Probability of Loss',pct(x.probability_of_loss))}${row('Median',x.percentiles?.p50 ?? 'UNKNOWN')}${row('P10',x.percentiles?.p10 ?? 'UNKNOWN')}${row('P90',x.percentiles?.p90 ?? 'UNKNOWN')}</div>`; }).join('') + row('Seed', meta.simulation_seed ?? '42','CALCULATION'));
    html += card('CONTRARIAN · HOW COULD THIS INVESTMENT LOSE?', findings.length ? findings.map(f => `<div class="p9-finding"><b>${esc(f.severity)} · ${esc(f.category)}</b><p>${esc(f.description)}</p><small>${esc(f.provenance || 'INTERPRETATION')}</small></div>`).join('') : '<p>NO MATERIAL FINDINGS RETURNED BY THE EXISTING CONTRARIAN ENGINE.</p>','INTERPRETATION');
    html += card('CAPITAL STACK', f ? row('Sources',money(f.total_sources))+row('Uses',money(f.total_uses))+row('Variance',money(f.sources_uses_variance))+row('Debt',money(f.total_debt))+row('Equity Requirement',money(f.equity_requirement))+row('LTV',pct(f.loan_to_value))+row('LTC',pct(f.loan_to_cost))+row('Annual Debt Service',money(f.annual_debt_service))+row('DSCR',f.debt_service_coverage_ratio?.toFixed(2) ?? 'UNKNOWN')+row('Debt Yield',pct(f.debt_yield))+f.debt_analyses.map(d=>row(`${d.source_name} Balloon`,money(d.balloon_balance))).join('') : '<p>INSUFFICIENT DATA / NO FINANCING ANALYSIS.</p>');
    html += card('LENDER EVIDENCE', '<p><strong>UNKNOWN / NOT PROVIDED</strong></p><p>No lender evidence was supplied to this visual run. No lender terms have been fabricated.</p>','UNKNOWN / INSUFFICIENT DATA');
    html += card('INVESTMENT SYNTHESIS', row('Thesis Status',thesis.status || 'UNKNOWN','INTERPRETATION')+row('Supporting Evidence',(thesis.supporting_evidence||[]).length,'EVIDENCE')+row('Contradictory Evidence',(thesis.contradictory_evidence||[]).length,'EVIDENCE')+row('Disagreements',disagreements.length,'INTERPRETATION')+row('Unresolved Questions',(a.synthesis?.unresolved_questions||[]).length,'UNKNOWN / INSUFFICIENT DATA'));
    html += card('STRUCTURED INVESTMENT CASE', row('Status',a.status,'INTERPRETATION')+row('Recommendation',a.recommendation,'RECOMMENDATION')+row('Rationale',(a.recommendation_rationale||[]).join(' | '),'INTERPRETATION'));
    html += card('HUMAN DECISION GATE','<div class="p9-governance"><h3>INTELLIGENCE IS NOT AUTHORITY</h3><p>ANALYSIS → RECOMMENDATION → <strong>HUMAN AUTHORIZATION</strong> → EXECUTION</p><p>Authorization created: <strong>NO</strong><br>Workflow mutated: <strong>NO</strong><br>Portfolio created: <strong>NO</strong><br>Transaction executed: <strong>NO</strong></p><p class="muted">The system has prepared analytical intelligence. Only the human may authorize.</p></div>','RECOMMENDATION');
    html += '</div>';
    $('p9-results').innerHTML = html;
    $('p9-status').textContent = 'COMPLETE / HUMAN AUTHORIZATION REQUIRED';
  }
  $('p9-run')?.addEventListener('click', async () => {
    $('p9-status').textContent = 'RUNNING EXISTING PHASE 9 ENGINES...';
    const payload = {
      asset_id:$('p9-asset').value, acquisition_price:value('p9-price'), acquisition_costs:value('p9-costs'), annual_rent:value('p9-rent'), other_income:value('p9-other'), initial_occupancy:value('p9-occ'), vacancy_rate:value('p9-vac'), rent_growth:value('p9-rg'), operating_expenses:value('p9-opex'), expense_growth:value('p9-eg'), management_expense:value('p9-mgmt'), property_tax:value('p9-tax'), insurance:value('p9-ins'), maintenance:value('p9-maint'), utilities:value('p9-util'), capex:value('p9-capex'), reserves:value('p9-res'), tenant_improvements:value('p9-ti'), leasing_commissions:value('p9-lc'), entry_cap_rate:value('p9-entry'), exit_cap_rate:value('p9-exit'), exit_costs:value('p9-exitcost'), debt_amount:value('p9-debt'), interest_rate:value('p9-rate'), amortization_years:value('p9-amort'), maturity_years:value('p9-maturity'), equity_contribution:value('p9-equity'), simulation_paths:5000, simulation_seed:42
    };
    try {
      const response = await fetch('/phase9/visual',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Phase 9 request failed');
      render(data.assembly, data.assembly.provenance || {});
    } catch (err) { $('p9-status').textContent = `ERROR / ${err.message}`; $('p9-results').innerHTML=''; }
  });
})();
