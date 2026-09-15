/* AletheiaTelos workstation interaction layer. Presentation/navigation only. */
(() => {
  const $ = id => document.getElementById(id);
  const q = (s, root=document) => Array.from(root.querySelectorAll(s));
  const normalize = v => String(v || '').trim().toLowerCase();

  function announce(text) {
    let el = $('workstation-announcer');
    if (!el) {
      el = document.createElement('div');
      el.id = 'workstation-announcer';
      el.className = 'sr-only';
      el.setAttribute('aria-live', 'polite');
      document.body.appendChild(el);
    }
    el.textContent = text;
  }

  function setActiveNav(target) {
    q('.nav-item[href^="#"]').forEach(item => item.classList.toggle('active', item.getAttribute('href') === `#${target}`));
  }

  function focusPanel(id) {
    const panel = $(id);
    if (!panel) return;
    panel.scrollIntoView({behavior:'smooth', block:'start'});
    setActiveNav(id);
    announce(`Opened ${panel.querySelector('h2, .panel-head span')?.textContent || id}`);
  }

  function enhanceStages() {
    q('.stage').forEach((stage, index) => {
      stage.setAttribute('aria-label', `${index + 1}. ${stage.querySelector('.stage-name')?.textContent || 'Pipeline stage'}`);
      stage.addEventListener('focus', () => stage.classList.add('keyboard-focus'));
      stage.addEventListener('blur', () => stage.classList.remove('keyboard-focus'));
    });
  }

  function wireNav() {
    q('.nav-item[href^="#"]').forEach(item => {
      if (item.classList.contains('disabled')) return;
      item.addEventListener('click', event => {
        const id = item.getAttribute('href').slice(1);
        if (!$(id)) return;
        event.preventDefault();
        focusPanel(id);
      });
    });
  }

  function wireSearch() {
    const input = $('global-search');
    if (!input) return;
    let last = '';
    input.addEventListener('input', () => {
      const term = normalize(input.value);
      if (term === last) return;
      last = term;
      const cards = [...q('.recent-item'), ...q('.agent'), ...q('.stage'), ...q('.conflict-item'), ...q('.activity-item')];
      let matches = 0;
      cards.forEach(card => {
        const hit = !term || normalize(card.textContent).includes(term);
        card.hidden = !hit;
        if (hit && term) matches += 1;
      });
      announce(term ? `${matches} matching workstation records` : 'Search cleared');
    });
    input.addEventListener('keydown', event => {
      if (event.key === 'Escape') { input.value = ''; input.dispatchEvent(new Event('input')); input.blur(); }
    });
  }

  function wireKeyboard() {
    document.addEventListener('keydown', event => {
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      const tag = document.activeElement?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      const key = event.key.toLowerCase();
      if (key === '/') { event.preventDefault(); $('global-search')?.focus(); }
      if (key === 'n') { event.preventDefault(); $('new-analysis-top')?.click(); }
      if (key === 'escape') { $('close-drawer')?.click(); }
    });
  }

  function wirePanels() {
    document.addEventListener('click', event => {
      const button = event.target.closest('[data-target-panel]');
      if (button) focusPanel(button.dataset.targetPanel);
    });
  }

  function injectControls() {
    const toolbar = document.querySelector('.toolbar');
    if (toolbar && !$('workstation-help')) {
      const help = document.createElement('button');
      help.id = 'workstation-help';
      help.className = 'secondary compact-button';
      help.type = 'button';
      help.textContent = '⌘ / COMMAND';
      help.title = 'Keyboard: / search, N new analysis, Esc close';
      help.addEventListener('click', () => {
        announce('Keyboard commands: slash for search, N for new analysis, Escape to close command drawer');
        $('global-search')?.focus();
      });
      toolbar.insertBefore(help, toolbar.firstChild);
    }

    const intro = document.querySelector('.workspace-intro');
    if (intro && !$('workstation-statusline')) {
      const line = document.createElement('div');
      line.id = 'workstation-statusline';
      line.className = 'workstation-statusline';
      line.innerHTML = '<span>WORKSTATION MODE</span><b>INTERACTIVE</b><i>presentation/navigation layer</i>';
      intro.appendChild(line);
    }
  }

  function observeDynamicPipeline() {
    const pipeline = $('pipeline-stages');
    if (!pipeline) return;
    new MutationObserver(enhanceStages).observe(pipeline, {childList:true});
  }

  function init() {
    injectControls();
    wireNav();
    wireSearch();
    wireKeyboard();
    wirePanels();
    enhanceStages();
    observeDynamicPipeline();
    announce('AletheiaTelos institutional workstation ready');
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once:true});
  else init();
})();
