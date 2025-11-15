document.addEventListener('DOMContentLoaded', () => {
  const state = window.State;
  const overlay = document.getElementById('mobile-overlay');
  const sidebar = document.querySelector('.mobile-sidebar');
  const toggleBtn = document.getElementById('mobile-menu-toggle');
  const logoutLinks = Array.from(document.querySelectorAll('#logout-link, [data-action="logout"]'));

  function applySidebar(open) {
    if (!sidebar || !overlay) return;
    sidebar.classList.toggle('open', !!open);
    overlay.classList.toggle('show', !!open);
    if (toggleBtn) {
      toggleBtn.setAttribute('aria-expanded', !!open);
      toggleBtn.setAttribute('aria-controls', 'sidebar');
    }
    if (open) {
      const firstLink = sidebar.querySelector('a, button');
      if (firstLink) firstLink.focus();
    } else if (toggleBtn) {
      toggleBtn.focus();
    }
  }

  // Initialize from persisted state
  const initial = state ? state.getState() : { ui: { sidebarOpen: false }, auth: {} };
  applySidebar(initial.ui && initial.ui.sidebarOpen);

  // Toggle handler
  if (toggleBtn && state) {
    toggleBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const s = state.getState();
      const next = !(s.ui && s.ui.sidebarOpen);
      state.setSidebarOpen(next);
      applySidebar(next);
    });
  }

  // Close overlay when clicking outside
  if (overlay && state) {
    overlay.addEventListener('click', () => {
      state.setSidebarOpen(false);
      applySidebar(false);
    });
  }

  // Logout functionality
  logoutLinks.forEach(el => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      try { state && state.clearAuth && state.clearAuth(); } catch (err) { console.warn('clearAuth failed', err); }
      window.location.href = '../login_page/code.html';
    });
  });

  // Role-based rendering
  function currentRole() {
    const s = state ? state.getState() : {};
    if (s.auth && s.auth.role) return String(s.auth.role).toLowerCase();
    try {
      const raw = sessionStorage.getItem('currentUser');
      if (raw) {
        const me = JSON.parse(raw);
        return String(me.role || '').toLowerCase();
      }
    } catch (e) {}
    return null;
  }

  const role = currentRole();
  const roleEls = Array.from(document.querySelectorAll('[data-role]'));
  roleEls.forEach(el => {
    const required = (el.getAttribute('data-role') || '').toLowerCase();
    const show = !required || required === 'common' || required === role;
    el.style.display = show ? '' : 'none';
    el.setAttribute('aria-hidden', show ? 'false' : 'true');
  });

  // Loading overlay helper
  const loading = document.querySelector('.loading-overlay');
  window.UI = {
    showLoading: () => { if (loading) loading.style.display = 'flex'; },
    hideLoading: () => { if (loading) loading.style.display = 'none'; },
    showError: (msg) => {
      try {
        let banner = document.getElementById('global-error-banner');
        if (!banner) {
          banner = document.createElement('div');
          banner.id = 'global-error-banner';
          banner.setAttribute('role', 'alert');
          banner.style.position = 'fixed';
          banner.style.top = '0';
          banner.style.left = '0';
          banner.style.right = '0';
          banner.style.zIndex = '9999';
          banner.style.background = '#b00020';
          banner.style.color = '#fff';
          banner.style.padding = '10px 16px';
          banner.style.fontSize = '14px';
          banner.style.display = 'none';
          document.body.appendChild(banner);
        }
        banner.textContent = msg || 'An error occurred.';
        banner.style.display = 'block';
        setTimeout(() => { banner.style.display = 'none'; }, 4000);
      } catch (e) {}
    }
  };

  // Network status banner
  try {
    let netBanner = document.getElementById('network-status-banner');
    if (!netBanner) {
      netBanner = document.createElement('div');
      netBanner.id = 'network-status-banner';
      netBanner.setAttribute('aria-live', 'polite');
      netBanner.style.position = 'fixed';
      netBanner.style.bottom = '0';
      netBanner.style.left = '0';
      netBanner.style.right = '0';
      netBanner.style.zIndex = '9999';
      netBanner.style.background = '#444';
      netBanner.style.color = '#fff';
      netBanner.style.padding = '8px 14px';
      netBanner.style.fontSize = '13px';
      netBanner.style.display = 'none';
      netBanner.textContent = 'You are offline. Some actions may fail.';
      document.body.appendChild(netBanner);
    }
    function updateOnlineStatus(){
      netBanner.style.display = navigator.onLine ? 'none' : 'block';
    }
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    updateOnlineStatus();
  } catch (e) {}
});