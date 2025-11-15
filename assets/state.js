(() => {
  const listeners = new Set();
  
  function safeLocalStorage(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(key);
      return item !== null ? item : defaultValue;
    } catch (e) {
      console.warn('localStorage access failed:', e);
      return defaultValue;
    }
  }
  
  function safeJSONParse(str, defaultValue) {
    try {
      return JSON.parse(str);
    } catch (e) {
      return defaultValue;
    }
  }
  
  function safeSetItem(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch (e) {
      console.warn('localStorage write failed:', e);
    }
  }
  
  function safeRemoveItem(key) {
    try {
      localStorage.removeItem(key);
    } catch (e) {
      console.warn('localStorage remove failed:', e);
    }
  }

  const initial = {
    auth: {
      token: safeLocalStorage('token', ''),
      role: safeLocalStorage('user_role'),
      userId: safeLocalStorage('user_id'),
    },
    ui: {
      sidebarOpen: safeJSONParse(safeLocalStorage('ui.sidebarOpen', 'false'), false),
    },
  };

  let state = initial;

  function notify() {
    const snapshot = getState();
    listeners.forEach(fn => {
      try { 
        fn(snapshot); 
      } catch (e) { 
        console.warn('State subscriber error:', e); 
      }
    });
  }

  function getState() {
    try {
      return JSON.parse(JSON.stringify(state));
    } catch (e) {
      console.warn('State serialization error:', e);
      return { ...state };
    }
  }

  function deepMerge(target, source) {
    const result = { ...target };
    for (const key in source) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = deepMerge(target[key] || {}, source[key]);
      } else {
        result[key] = source[key];
      }
    }
    return result;
  }

  function setState(partial) {
    if (!partial || typeof partial !== 'object') return;
    
    state = deepMerge(state, partial);
    
    if (state.auth) {
      const { token, role, userId } = state.auth;
      if (token !== undefined) safeSetItem('token', token || '');
      if (role !== undefined) safeSetItem('user_role', role || '');
      if (userId !== undefined) safeSetItem('user_id', userId || '');
    }
    
    if (state.ui && state.ui.sidebarOpen !== undefined) {
      safeSetItem('ui.sidebarOpen', JSON.stringify(!!state.ui.sidebarOpen));
    }
    
    notify();
  }

  function subscribe(fn) {
    if (typeof fn !== 'function') return () => {};
    listeners.add(fn);
    return () => listeners.delete(fn);
  }

  function setAuth(token, role, userId) {
    setState({ 
      auth: { 
        token: token || '', 
        role: role || null, 
        userId: userId || null 
      } 
    });
  }

  function clearAuth() {
    setState({ auth: { token: '', role: null, userId: null } });
    safeRemoveItem('token');
    safeRemoveItem('user_role');
    safeRemoveItem('user_id');
    try {
      sessionStorage.removeItem('currentUser');
      sessionStorage.removeItem('authToken');
    } catch (e) {
      console.warn('sessionStorage clear failed:', e);
    }
  }

  function setSidebarOpen(open) {
    setState({ ui: { sidebarOpen: !!open } });
    try {
      const body = document.body;
      if (body) body.classList.toggle('sidebar-open', !!open);
    } catch (e) {
      console.warn('DOM manipulation failed:', e);
    }
  }

  function isAuthenticated() {
    const { token, role } = state.auth;
    return !!(token && role);
  }

  function getAuthToken() {
    return state.auth.token;
  }

  function getUserRole() {
    return state.auth.role;
  }

  function getUserId() {
    return state.auth.userId;
  }

  window.State = { 
    getState, 
    setState, 
    subscribe, 
    setAuth, 
    clearAuth, 
    setSidebarOpen,
    isAuthenticated,
    getAuthToken,
    getUserRole,
    getUserId
  };
})();