(function(){
  const BRAND_NAME = 'Competence Consulting Ecommerce LLP';
  const LOGO_SRC = '/static/images/logo.png';
  const FAVICON_SRC = '/assets/favicon.svg';

  function upsertFavicon(){
    let link = document.querySelector('link[rel="icon"]');
    if(!link){
      link = document.createElement('link');
      link.rel = 'icon';
      link.type = 'image/svg+xml';
      link.href = FAVICON_SRC;
      document.head.appendChild(link);
    } else {
      link.type = 'image/svg+xml';
      link.href = FAVICON_SRC;
    }
  }

  function pageTitleFromPath(){
    const p = location.pathname;
    if(p.includes('/manager_dashboard_page/')) return 'Manager Dashboard';
    if(p.includes('/employee_dashboard_page/')) return 'Employee Dashboard';
    if(p.includes('/notifications_page/')) return 'Notifications';
    if(p.includes('/activity_logging_page/')) return 'Activity Logs';
    if(p.includes('/login_page/')) return 'Login';
    return document.title.replace(/\s+-\s+.*/,'').trim() || 'App';
  }

  function replaceBrandText(){
    // Only update title if it contains legacy brand or is generic
    const legacyTitle = /ClientReach|Outreach CRM/i.test(document.title);
    const currentTitle = document.title.trim();
    const pageTitle = pageTitleFromPath();
    if(legacyTitle || !currentTitle || currentTitle === BRAND_NAME){
      document.title = `${BRAND_NAME} - ${pageTitle}`;
    }

    // Replace legacy brand texts in obvious places
    const selectors = ['h1', '.brand h1', '.brand-title'];
    selectors.forEach(sel => {
      document.querySelectorAll(sel).forEach(el => {
        const text = (el.textContent || '').trim();
        if(/ClientReach|Outreach CRM/i.test(text)){
          el.textContent = BRAND_NAME;
        }
      });
    });
  }

  function navItemsForRole(role){
    if(role === 'employee'){
      return [
        { label: 'Dashboard', href: '/employee_dashboard_page/code.html' },
        { label: 'Activity Logs', href: '/activity_logging_page/code.html' },
        { label: 'Notifications', href: '/notifications_page/code.html' },
      ];
    }
    // default manager
    return [
      { label: 'Dashboard', href: '/manager_dashboard_page/code.html' },
      { label: 'Clients', href: '/employee_dashboard_page/code.html' },
      { label: 'Activity Logs', href: '/activity_logging_page/code.html' },
      { label: 'Notifications', href: '/notifications_page/code.html' },
    ];
  }

  function injectBrandSidebar(role){
    // Hide legacy top headers that carry old branding
    document.querySelectorAll('header').forEach(el => {
      const txt = (el.textContent || '').trim();
      if(/ClientReach|Outreach CRM/i.test(txt)){
        el.style.display = 'none';
      }
    });

    // If a sidebar already exists, don't inject a duplicate
    const hasExistingSidebar = !!document.querySelector('aside#sidebar, aside.sidebar, aside#brand-sidebar');
    if (hasExistingSidebar) {
      document.body.classList.add('with-brand-sidebar');
      return;
    }

    const aside = document.createElement('aside');
    aside.id = 'brand-sidebar';
    aside.className = 'sidebar bg-background-light dark:bg-background-dark border-r border-border-light dark:border-border-dark flex flex-col';

    const items = navItemsForRole(role);
    const currentPath = location.pathname;

    // Brand header
    const brand = document.createElement('div');
    brand.className = 'brand';
    const logo = document.createElement('img');
    logo.src = LOGO_SRC;
    logo.alt = 'Brand Logo';
    logo.className = 'brand-logo';
    const brandInfo = document.createElement('div');
    const titleEl = document.createElement('h1');
    titleEl.textContent = BRAND_NAME;
    const roleEl = document.createElement('p');
    roleEl.className = 'role';
    roleEl.textContent = role === 'employee' ? 'Employee' : 'Manager';
    brandInfo.appendChild(titleEl);
    brandInfo.appendChild(roleEl);
    brand.appendChild(logo);
    brand.appendChild(brandInfo);

    // Nav
    const nav = document.createElement('nav');
    nav.className = 'flex-1 px-4 py-2 space-y-2';
    items.forEach(i => {
      const a = document.createElement('a');
      const isActive = currentPath.includes(i.href.split('/')[1]);
      a.className = `flex items-center gap-3 px-4 py-2 rounded-lg ${isActive ? 'bg-primary text-white' : 'text-foreground-light dark:text-foreground-dark hover:bg-primary/10'}`;
      a.href = i.href;
      const label = document.createElement('span');
      label.className = 'text-sm font-medium';
      label.textContent = i.label;
      a.appendChild(label);
      nav.appendChild(a);
    });

    // Logout
    const footer = document.createElement('div');
    footer.className = 'mt-auto p-4';
    const logoutBtn = document.createElement('button');
    logoutBtn.type = 'button';
    logoutBtn.className = 'flex items-center gap-3 px-4 py-2 rounded-lg text-foreground-light dark:text-foreground-dark hover:bg-primary/10';
    const logoutText = document.createElement('span');
    logoutText.className = 'text-sm';
    logoutText.textContent = 'Logout';
    logoutBtn.appendChild(logoutText);
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      try {
        if (window.API && window.API.clearToken) {
          window.API.clearToken();
        } else {
          localStorage.removeItem('token');
        }
        sessionStorage.removeItem('currentUser');
      } finally {
        location.href = '/login_page/code.html';
      }
    });
    footer.appendChild(logoutBtn);

    aside.appendChild(brand);
    aside.appendChild(nav);
    aside.appendChild(footer);

    // Insert as first child for consistent layout
    document.body.prepend(aside);
    document.body.classList.add('with-brand-sidebar');

    // Wrap tables in scroll containers to prevent mobile compression
    document.querySelectorAll('table').forEach(t => {
      if (!t.closest('.table-scroll')) {
        const wrap = document.createElement('div');
        wrap.className = 'table-scroll';
        t.parentNode.insertBefore(wrap, t);
        wrap.appendChild(t);
      }
    });
  }

  function initBrand(){
    // Per request: no favicon (SVG) or sidebar injection
    replaceBrandText();
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', initBrand);
  } else {
    initBrand();
  }
})();