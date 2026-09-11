document.addEventListener('DOMContentLoaded', async () => {
  const target = document.querySelector('#phase9-mount');
  if (!target) return;
  try {
    const html = await fetch('/web/phase9.html').then(r => r.text());
    target.innerHTML = html;
    const script = document.createElement('script');
    script.src = '/web/phase9.js';
    document.body.appendChild(script);
  } catch (e) {
    target.textContent = 'PHASE 9 VISUAL INTEGRATION UNAVAILABLE';
  }
});
