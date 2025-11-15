(function(){
  const DEFAULT_API_BASE = window.location.origin;
  const API_BASE = window.API_BASE || DEFAULT_API_BASE;

  function getToken(){
    return localStorage.getItem('token') || '';
  }
  function setToken(token){
    localStorage.setItem('token', token);
  }
  function clearToken(){
    localStorage.removeItem('token');
  }

  async function api(path, opts = {}){
    const headers = Object.assign({
      'Content-Type': 'application/json',
    }, opts.headers || {});
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
    
    // Add timeout to prevent long hangs
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
    
    try {
      const res = await fetch(url, Object.assign({}, opts, { 
        headers,
        signal: controller.signal 
      }));
      clearTimeout(timeoutId);
      if (!res.ok){
        const ct = res.headers.get('content-type') || '';
        let bodyText = '';
        let bodyJson = null;
        try { bodyText = await res.text(); } catch (_) {}
        if (ct.includes('application/json')){
          try { bodyJson = JSON.parse(bodyText || '{}'); } catch (_) {}
        }
        if (res.status === 401){
          const hasSessionUser = !!sessionStorage.getItem('currentUser');
          const hasToken = !!getToken();
          if (hasToken && !hasSessionUser){
            console.warn('Unauthorized. Redirecting to login.');
            localStorage.setItem('postLoginRedirect', location.pathname);
            location.href = '../login_page/code.html';
          } else {
            console.warn('Unauthorized in session/demo mode. Staying on page.');
          }
        }
        const info = bodyJson && bodyJson.error ? bodyJson.error : { code: 'http_error', message: bodyText || `HTTP ${res.status}` };
        const err = new Error(`${info.code}: ${info.message}`);
        err.info = info;
        err.status = res.status;
        throw err;
      }
      const ct = res.headers.get('content-type') || '';
      return ct.includes('application/json') ? res.json() : res.text();
    } catch (e) {
      clearTimeout(timeoutId);
      if (e && e.status) throw e;
      
      let errorMessage = 'Network request failed';
      if (e.name === 'AbortError') {
        errorMessage = 'Request timed out - server may be down';
      } else if (e.message && e.message.includes('fetch')) {
        errorMessage = 'Cannot connect to server';
      }
      
      const err = new Error(`network_error: ${errorMessage}`);
      err.info = { code: 'network_error', message: errorMessage };
      throw err;
    }
  }

  async function safe(path, opts = {}){
    try {
      const data = await api(path, opts);
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: err && err.info ? err.info : { code: 'unknown_error', message: String(err && err.message || 'Unknown error') }, status: err && err.status };
    }
  }

  async function login(email, password){
    return api('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  }

  async function currentUser(){
    return api('/api/auth/me');
  }

  window.API = { api, safe, login, currentUser, getToken, setToken, clearToken, API_BASE };
})();