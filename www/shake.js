const ShakeLock = (() => {
  let enabled=false, lastX=null, lastY=null, lastZ=null, lastShake=0;
  const THRESH=20, COOLDOWN=2000;

  function enable() {
    if(typeof DeviceMotionEvent==='undefined') return false;
    if(typeof DeviceMotionEvent.requestPermission==='function') {
      DeviceMotionEvent.requestPermission().then(r=>{ if(r==='granted') _bind(); }).catch(()=>{});
    } else { _bind(); }
    enabled=true; _sync(true); return true;
  }
  function disable() { window.removeEventListener('devicemotion',_onMotion); enabled=false; _sync(false); }
  function toggle() { if(enabled){disable();return false;} return enable(); }
  function isEnabled() { return enabled; }

  function _bind() { window.addEventListener('devicemotion',_onMotion,{passive:true}); }
  function _onMotion(e) {
    if(!enabled) return;
    const a=e.accelerationIncludingGravity; if(!a) return;
    const {x,y,z}=a;
    if(lastX!==null) {
      const dx=Math.abs(x-lastX), dy=Math.abs(y-lastY), dz=Math.abs(z-lastZ);
      if(dx+dy+dz>THRESH && Date.now()-lastShake>COOLDOWN) {
        lastShake=Date.now();
        if(typeof App!=='undefined') App.lock();
      }
    }
    lastX=x; lastY=y; lastZ=z;
  }
  function _sync(on) {
    const d=document.getElementById('shakeDot'),t=document.getElementById('shakeTxt');
    if(d) d.className='status-dot '+(on?'on':'off');
    if(t) t.textContent=on?'on':'off';
  }
  return {enable,disable,toggle,isEnabled};
})();
