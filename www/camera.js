const CameraWatch = (() => {
  let enabled=false, stream=null, video=null, detector=null, rafId=null, lastScan=0;
  const SCAN_MS = 1200;

  async function enable() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({video:{facingMode:'user',width:320,height:240}});
      video = document.createElement('video');
      video.srcObject=stream; video.autoplay=true; video.muted=true; video.playsInline=true;
      video.style.display='none'; document.body.appendChild(video);
      if('FaceDetector' in window) detector = new FaceDetector({fastMode:true,maxDetectedFaces:3});
      enabled=true; _loop(); _sync(true); return true;
    } catch(e) { _sync(false); return false; }
  }
  function disable() {
    enabled=false; if(rafId){cancelAnimationFrame(rafId);rafId=null;}
    if(stream){stream.getTracks().forEach(t=>t.stop());stream=null;}
    if(video){video.remove();video=null;} _sync(false);
  }
  function toggle() { if(enabled){disable();return false;} return enable(); }
  function isEnabled() { return enabled; }

  function _loop(ts=0) {
    if(!enabled) return;
    rafId=requestAnimationFrame(_loop);
    if(ts-lastScan<SCAN_MS) return;
    lastScan=ts; _scan();
  }
  async function _scan() {
    if(!video||video.readyState<2) return;
    try {
      let count=0;
      if(detector) { count=(await detector.detect(video)).length; }
      else {
        const c=document.createElement('canvas'); c.width=40;c.height=30;
        const ctx=c.getContext('2d'); ctx.drawImage(video,0,0,40,30);
        const px=ctx.getImageData(0,0,40,30).data;
        let t=0; for(let i=0;i<px.length;i+=4) t+=px[i];
        count = (t/(px.length/4))>40 ? 1 : 0;
      }
      if(count>1) { if(!PrivacyOverlay.isEnabled()) PrivacyOverlay.enable(); _toast('👁 Extra face — privacy blur on','red'); }
    } catch{}
  }
  function _sync(on) {
    const d=document.getElementById('watchDot'),t=document.getElementById('watchTxt');
    if(d) d.className='status-dot '+(on?'on':'off');
    if(t) t.textContent=on?'on':'off';
  }
  function _toast(msg,type) {
    const t=document.createElement('div'); t.className='toast '+(type||'');
    t.textContent=msg; document.body.appendChild(t); setTimeout(()=>t.remove(),3000);
  }

  // ── Intruder Selfie ──────────────────────────────
  const IK='ss_intruders';
  async function captureIntruder() {
    try {
      const s = await navigator.mediaDevices.getUserMedia({video:{facingMode:'user',width:400,height:400}});
      const v = document.createElement('video');
      v.srcObject=s; v.autoplay=true; v.muted=true; v.playsInline=true;
      document.body.appendChild(v);
      await new Promise(r=>setTimeout(r,800));
      const c=document.createElement('canvas'); c.width=400;c.height=400;
      c.getContext('2d').drawImage(v,0,0,400,400);
      const dataUrl=c.toDataURL('image/jpeg',0.6);
      s.getTracks().forEach(t=>t.stop()); v.remove();
      const intruders=JSON.parse(localStorage.getItem(IK)||'[]');
      intruders.push({img:dataUrl,ts:Date.now()});
      if(intruders.length>20) intruders.shift();
      localStorage.setItem(IK,JSON.stringify(intruders));
      document.getElementById('intruderAlert').classList.remove('hidden');
    } catch(e) { console.warn('Intruder capture failed',e); }
  }
  function getIntruders() { try{return JSON.parse(localStorage.getItem(IK)||'[]');}catch{return[];} }
  function clearIntruders() { localStorage.removeItem(IK); }

  return {enable,disable,toggle,isEnabled,captureIntruder,getIntruders,clearIntruders};
})();
