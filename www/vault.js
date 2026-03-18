const Vault = (() => {
  const NK = 'ss_vault_notes', FK = 'ss_vault_files', SK = 'ss_vault_salt';
  let _key = null;

  async function _deriveKey(pin, salt) {
    const km = await crypto.subtle.importKey('raw', new TextEncoder().encode(pin), {name:'PBKDF2'}, false, ['deriveKey']);
    return crypto.subtle.deriveKey({name:'PBKDF2', salt, iterations:100000, hash:'SHA-256'}, km, {name:'AES-GCM', length:256}, false, ['encrypt','decrypt']);
  }
  function _getSalt() {
    let b = localStorage.getItem(SK);
    if (!b) { const s = crypto.getRandomValues(new Uint8Array(16)); b = btoa(String.fromCharCode(...s)); localStorage.setItem(SK, b); }
    return Uint8Array.from(atob(b), c => c.charCodeAt(0));
  }
  async function _enc(text) {
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const ct = new Uint8Array(await crypto.subtle.encrypt({name:'AES-GCM', iv}, _key, new TextEncoder().encode(text)));
    const out = new Uint8Array(12 + ct.length); out.set(iv); out.set(ct, 12);
    return btoa(String.fromCharCode(...out));
  }
  async function _dec(b64) {
    const d = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    const pt = await crypto.subtle.decrypt({name:'AES-GCM', iv:d.slice(0,12)}, _key, d.slice(12));
    return new TextDecoder().decode(pt);
  }

  async function unlock(pin) { _key = await _deriveKey(pin, _getSalt()); }
  function lock() { _key = null; }
  function isUnlocked() { return !!_key; }

  function _rawNotes() { try { return JSON.parse(localStorage.getItem(NK)||'{}'); } catch { return {}; } }
  function _rawFiles() { try { return JSON.parse(localStorage.getItem(FK)||'{}'); } catch { return {}; } }

  async function saveNote(n) {
    const notes = _rawNotes(), id = n.id || Date.now().toString();
    notes[id] = {id, eT: await _enc(n.title||'Untitled'), eB: await _enc(n.body||''), ts: Date.now()};
    localStorage.setItem(NK, JSON.stringify(notes)); return id;
  }
  async function getAllNotes() {
    const r = _rawNotes(), out = [];
    for (const id of Object.keys(r)) {
      try { out.push({id, title: await _dec(r[id].eT), body: await _dec(r[id].eB), ts: r[id].ts}); } catch {}
    }
    return out.sort((a,b) => b.ts - a.ts);
  }
  async function deleteNote(id) { const n = _rawNotes(); delete n[id]; localStorage.setItem(NK, JSON.stringify(n)); }

  async function saveFile(file) {
    const b64 = await new Promise((res,rej) => { const r=new FileReader(); r.onload=()=>res(r.result.split(',')[1]); r.onerror=rej; r.readAsDataURL(file); });
    const id = Date.now().toString(), files = _rawFiles();
    files[id] = {id, eD: await _enc(b64), eN: await _enc(file.name), size: file.size, type: file.type, ts: Date.now()};
    localStorage.setItem(FK, JSON.stringify(files)); return id;
  }
  async function getAllFiles() {
    const r = _rawFiles(), out = [];
    for (const id of Object.keys(r)) {
      try { out.push({id, name: await _dec(r[id].eN), size: r[id].size, type: r[id].type, ts: r[id].ts}); } catch {}
    }
    return out.sort((a,b) => b.ts - a.ts);
  }
  async function downloadFile(id) {
    const r = _rawFiles(), e = r[id]; if (!e) return;
    const b64 = await _dec(e.eD), name = await _dec(e.eN);
    const bytes = Uint8Array.from(atob(b64), c=>c.charCodeAt(0));
    const url = URL.createObjectURL(new Blob([bytes], {type: e.type||'application/octet-stream'}));
    Object.assign(document.createElement('a'), {href:url, download:name}).click();
    URL.revokeObjectURL(url);
  }
  async function deleteFile(id) { const f = _rawFiles(); delete f[id]; localStorage.setItem(FK, JSON.stringify(f)); }

  async function exportBackup() {
    const notes = _rawNotes(), files = _rawFiles();
    const blob = new Blob([JSON.stringify({v:2, notes, files, ts: Date.now()})], {type:'application/json'});
    const url = URL.createObjectURL(blob);
    Object.assign(document.createElement('a'), {href:url, download:`shieldspace-backup-${Date.now()}.shieldspace`}).click();
    URL.revokeObjectURL(url);
  }
  async function importBackup(file) {
    const text = await new Promise((res,rej) => { const r=new FileReader(); r.onload=()=>res(r.result); r.onerror=rej; r.readAsText(file); });
    const data = JSON.parse(text);
    if (data.notes) { const n = _rawNotes(); Object.assign(n, data.notes); localStorage.setItem(NK, JSON.stringify(n)); }
    if (data.files) { const f = _rawFiles(); Object.assign(f, data.files); localStorage.setItem(FK, JSON.stringify(f)); }
    return Object.keys(data.notes||{}).length;
  }

  function clearAll() { localStorage.removeItem(NK); localStorage.removeItem(FK); localStorage.removeItem(SK); _key = null; }
  function formatSize(b) { return b<1024?b+' B':b<1048576?(b/1024).toFixed(1)+' KB':(b/1048576).toFixed(1)+' MB'; }

  return {unlock,lock,isUnlocked,saveNote,getAllNotes,deleteNote,saveFile,getAllFiles,downloadFile,deleteFile,exportBackup,importBackup,clearAll,formatSize};
})();
