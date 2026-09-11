// Loaded by the existing dashboard once the Phase 9 mount is present.
(async function(){
  const mount=document.querySelector('#phase9-mount');
  if(!mount) return;
  const html=await fetch('/web/phase9.html').then(r=>r.text());
  mount.innerHTML=html;
  const css=document.createElement('link'); css.rel='stylesheet'; css.href='/web/phase9.css'; document.head.appendChild(css);
  const script=document.createElement('script'); script.src='/web/phase9.js'; document.body.appendChild(script);
})();
