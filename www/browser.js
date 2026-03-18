const SecureBrowser = (() => {
  let currentUrl='';
  const frame=document.getElementById('browserFrame');
  const urlInput=document.getElementById('urlInput');
  const placeholder=document.getElementById('browserPlaceholder');

  function init() {
    document.getElementById('goBtn').addEventListener('click',navigate);
    urlInput.addEventListener('keydown',e=>{if(e.key==='Enter')navigate();});
    document.getElementById('clearBrowserBtn').addEventListener('click',clearSession);
    document.getElementById('reloadBtn').addEventListener('click',()=>{if(currentUrl)_load(currentUrl);});
  }
  function navigate() {
    let u=urlInput.value.trim(); if(!u) return;
    if(!/^https?:\/\//i.test(u)) u='https://'+u;
    _load(u);
  }
  function _load(u) {
    currentUrl=u; frame.src=u; placeholder.classList.add('hidden'); urlInput.value=u;
  }
  function clearSession() {
    frame.src='about:blank'; currentUrl=''; urlInput.value=''; placeholder.classList.remove('hidden');
    _toast('🗑 Session cleared — no trace left','green');
  }
  function onLeave() { clearSession(); }
  function _toast(msg,type) {
    const t=document.createElement('div'); t.className='toast '+(type||'');
    t.textContent=msg; document.body.appendChild(t); setTimeout(()=>t.remove(),2500);
  }
  return {init,clearSession,onLeave};
})();
