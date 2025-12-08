// Centralized App Configuration and Utilities
const APP = {
  API_URL: window.location.origin,

  // Get auth token
  getToken: () => localStorage.getItem('token'),

  // Get current user
  getUser: () => {
    try {
      return JSON.parse(sessionStorage.getItem('currentUser'));
    } catch {
      return null;
    }
  },

  // Check authentication
  isAuthenticated: () => !!APP.getToken() && !!APP.getUser(),

  // Logout
  logout: () => {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = '/login_page/code.html';
  },

  // Show/hide loading
  loading: {
    show: () => document.getElementById('loading')?.classList.add('show'),
    hide: () => document.getElementById('loading')?.classList.remove('show')
  },

  // Alert messages
  alert: (message, type = 'success') => {
    const container = document.getElementById('alertContainer');
    if (!container) return;
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `<i class="fas fa-${type === 'danger' ? 'times' : 'check'}-circle"></i>${message}`;
    container.appendChild(alert);
    setTimeout(() => alert.remove(), 5000);
  },

  // API call wrapper
  api: async (endpoint, options = {}) => {
    const token = APP.getToken();
    const config = {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };

    try {
      const response = await fetch(`${APP.API_URL}${endpoint}`, config);
      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          APP.logout();
          throw new Error('Session expired');
        }
        throw new Error(data.error?.message || 'Request failed');
      }

      return { ok: true, data };
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      return { ok: false, error: error.message };
    }
  },

  // Calculate days since date
  daysSince: (date) => {
    if (!date) return 999;
    return Math.ceil((new Date() - new Date(date)) / 86400000);
  },

  // Get status color
  getStatusColor: (days) => {
    if (days <= 7) return { color: '#10b981', label: 'Good', class: 'success' };
    if (days <= 14) return { color: '#f59e0b', label: 'Due Soon', class: 'warning' };
    return { color: '#ef4444', label: 'Overdue', class: 'danger' };
  },

  // Redirect based on role
  redirectByRole: (user) => {
    if (!user) {
      window.location.href = '/login_page/code.html';
      return;
    }
    const role = user.role?.toLowerCase();
    if (role === 'manager' || role === 'admin') {
      window.location.href = '/manager_dashboard_page/code.html';
    } else {
      window.location.href = '/employee_dashboard_page/code.html';
    }
  },

  // Render sidebar
  renderSidebar: (role, activePage) => {
    const nav = document.getElementById('sidebarNav');
    if (!nav) return;

    const user = APP.getUser();
    const userName = user?.name || 'User';

    // Update header if exists
    const userNameEl = document.getElementById('userName');
    if (userNameEl) userNameEl.textContent = userName;

    let links = '';
    if (role === 'employee') {
      links = `
        <a href="/employee_dashboard_page/code.html" class="${activePage === 'dashboard' ? 'active' : ''}">
          <i class="fas fa-home"></i>My Dashboard
        </a>
        <a href="/activity_logging_page/code.html" class="${activePage === 'activity' ? 'active' : ''}">
          <i class="fas fa-clipboard-check"></i>Log Client Contact
        </a>
        <a href="/daily_work_report/code.html" class="${activePage === 'report' ? 'active' : ''}">
          <i class="fas fa-file-alt"></i>Submit Daily Report
        </a>
        <a href="/notifications_page/code.html" class="${activePage === 'notifications' ? 'active' : ''}">
          <i class="fas fa-bell"></i>Notifications
        </a>
      `;
    } else {
      links = `
        <a href="/manager_dashboard_page/code.html" class="${activePage === 'dashboard' ? 'active' : ''}">
          <i class="fas fa-chart-line"></i>Dashboard
        </a>
        <a href="/management_page/code.html" class="${activePage === 'management' ? 'active' : ''}">
          <i class="fas fa-users"></i>All Clients
        </a>
        <a href="/notifications_page/code.html" class="${activePage === 'notifications' ? 'active' : ''}">
          <i class="fas fa-bell"></i>Notifications
        </a>
        <a href="/reports_page/code.html" class="${activePage === 'reports' ? 'active' : ''}">
          <i class="fas fa-file-alt"></i>Reports
        </a>
      `;
    }

    nav.innerHTML = links + `
      <div class="nav-divider"></div>
      <a href="#" onclick="APP.logout(); return false;">
        <i class="fas fa-sign-out-alt"></i>Logout
      </a>
    `;
  }
};

// Make APP globally available
window.APP = APP;
