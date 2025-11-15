// Lightweight Supabase client helpers with local fallback.
// Uses CDN-loaded supabase-js v2 if keys are provided in window.SUPABASE_URL/ANON_KEY.
(function(){
  const hasKeys = Boolean(window.SUPABASE_URL && window.SUPABASE_ANON_KEY && !String(window.SUPABASE_URL).includes('YOUR_PROJECT_ID') && !String(window.SUPABASE_ANON_KEY).includes('YOUR_ANON_KEY'));
  const supa = hasKeys && window.supabase ? window.supabase.createClient(window.SUPABASE_URL, window.SUPABASE_ANON_KEY) : null;

  const storageKey = 'crm_fallback_store_v1';
  const store = JSON.parse(localStorage.getItem(storageKey) || '{}');
  function save(){ localStorage.setItem(storageKey, JSON.stringify(store)); }
  function ensureTable(t){ if(!store[t]){ store[t] = []; save(); } }

  async function select(table, filters = {}, opts = {}){
    if (supa){
      let q = supa.from(table).select(opts.columns || '*');
      Object.entries(filters).forEach(([k,v]) => { if (v !== undefined) q = q.eq(k, v); });
      if (opts.orderBy) q = q.order(opts.orderBy, { ascending: !!opts.ascending });
      const { data, error } = await q;
      if (error) throw error; return data;
    }
    ensureTable(table);
    let data = [...store[table]];
    Object.entries(filters).forEach(([k,v]) => { data = data.filter(row => row[k] === v); });
    if (opts.orderBy){
      data.sort((a,b) => {
        const av = a[opts.orderBy], bv = b[opts.orderBy];
        return (av > bv ? 1 : av < bv ? -1 : 0) * (opts.ascending ? 1 : -1);
      });
    }
    return data;
  }

  async function insert(table, rows){
    if (supa){
      const { data, error } = await supa.from(table).insert(rows).select('*');
      if (error) throw error; return data;
    }
    ensureTable(table);
    const arr = Array.isArray(rows) ? rows : [rows];
    arr.forEach(r => { if (!r.id) r.id = crypto.randomUUID(); r.created_at = r.created_at || new Date().toISOString(); store[table].push(r); });
    save();
    return arr;
  }

  async function upsert(table, rows, key = 'id'){
    if (supa){
      const { data, error } = await supa.from(table).upsert(rows, { onConflict: key }).select('*');
      if (error) throw error; return data;
    }
    ensureTable(table);
    const arr = Array.isArray(rows) ? rows : [rows];
    arr.forEach(r => {
      const idx = store[table].findIndex(x => x[key] === r[key]);
      if (idx >= 0) store[table][idx] = { ...store[table][idx], ...r, updated_at: new Date().toISOString() };
      else store[table].push({ ...r, id: r.id || crypto.randomUUID(), created_at: new Date().toISOString() });
    });
    save();
    return arr;
  }

  async function remove(table, filters = {}){
    if (supa){
      let q = supa.from(table).delete();
      Object.entries(filters).forEach(([k,v]) => { if (v !== undefined) q = q.eq(k, v); });
      const { data, error } = await q; if (error) throw error; return data;
    }
    ensureTable(table);
    const before = store[table].length;
    store[table] = store[table].filter(row => !Object.entries(filters).every(([k,v]) => row[k] === v));
    save();
    return { removed: before - store[table].length };
  }

  function currentUser(){
    try {
      const raw = sessionStorage.getItem('currentUser');
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  }

  async function audit(action, entity, payload){
    const user = currentUser();
    const log = { id: crypto.randomUUID(), user_id: user?.id, action, entity, payload, timestamp: new Date().toISOString() };
    try { await insert('audit_logs', log); } catch(e){ console.warn('audit failed', e); }
    return log;
  }

  // Round-robin helper: assigns tasks fairly across employees
  function roundRobinAssign(tasks, employees){
    const out = []; if (!employees?.length) return out;
    let i = 0; tasks.forEach(t => { out.push({ ...t, assignee_id: employees[i % employees.length].id }); i++; });
    return out;
  }

  window.SUPA = { select, insert, upsert, remove, audit, roundRobinAssign, hasKeys };
  // Realtime subscriptions: listen to table changes
  function subscribe(table, event = '*', cb = () => {}, filter = {}){
    if (!supa){ console.warn('Realtime unavailable: Supabase keys not configured'); return null; }
    const chan = supa.channel(`table_${table}_${Date.now()}`);
    const payload = Object.assign({ event, schema: 'public', table }, filter || {});
    chan.on('postgres_changes', payload, (msg) => { try { cb(msg); } catch(e){ console.error('subscribe callback error', e); } });
    chan.subscribe().catch(e => console.error('subscribe failed', e));
    return chan;
  }

  function unsubscribe(channel){ try { channel?.unsubscribe(); } catch(e){ console.warn('unsubscribe failed', e); } }

  window.SUPA.subscribe = subscribe;
  window.SUPA.unsubscribe = unsubscribe;
})();