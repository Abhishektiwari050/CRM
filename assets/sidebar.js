// Sidebar Component - Production Ready
(()=>{
const STORAGE_KEY='sidebar_state';
const THEME_KEY='theme_preference';

const config={
employee:[
{icon:'home',text:'Dashboard',href:'/employee_dashboard_page/index.html',id:'dashboard'},
{icon:'clipboard',text:'Log Activity',href:'/activity_logging_page/index.html',id:'activity'},
{icon:'file-text',text:'Daily Report',href:'/daily_work_report/index.html',id:'report'},
{icon:'bell',text:'Notifications',href:'/notifications_page/index.html',id:'notifications',badge:0}
],
manager:[
{icon:'bar-chart',text:'Dashboard',href:'/manager_dashboard_page/index.html',id:'dashboard'},
{icon:'users',text:'All Clients',href:'/employee_dashboard_page/index.html',id:'clients'},
{icon:'bell',text:'Notifications',href:'/notifications_page/index.html',id:'notifications',badge:0},
{icon:'settings',text:'Team Management',href:'/management_page/index.html',id:'management'},
{icon:'file-text',text:'Reports',href:'/reports_page/index.html',id:'reports'}
],
admin:[
{icon:'bar-chart',text:'Dashboard',href:'/manager_dashboard_page/index.html',id:'dashboard'},
{icon:'users',text:'All Clients',href:'/employee_dashboard_page/index.html',id:'clients'},
{icon:'bell',text:'Notifications',href:'/notifications_page/index.html',id:'notifications',badge:0},
{icon:'settings',text:'Team Management',href:'/management_page/index.html',id:'management'},
{icon:'file-text',text:'Reports',href:'/reports_page/index.html',id:'reports'}
]
};

const icons={
home:'<svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><path d="M9 22V12h6v10"/></svg>',
clipboard:'<svg viewBox="0 0 24 24"><path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"/><rect x="8" y="2" width="8" height="4" rx="1"/></svg>',
'file-text':'<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/></svg>',
bell:'<svg viewBox="0 0 24 24"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0"/></svg>',
'bar-chart':'<svg viewBox="0 0 24 24"><path d="M18 20V10M12 20V4M6 20v-6"/></svg>',
users:'<svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>',
settings:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6m9-9h-6m-6 0H3m15.4-6.4l-4.2 4.2m-6.4 6.4l-4.2 4.2m12.8 0l-4.2-4.2m-6.4-6.4l-4.2-4.2"/></svg>',
'log-out':'<svg viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"/></svg>',
user:'<svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
};

const getIcon=(name)=>icons[name]||icons.home;

const render=(role,activePage,user)=>{
const items=config[role]||config.employee;
const theme=localStorage.getItem(THEME_KEY)||'dark';
document.documentElement.setAttribute('data-theme',theme);

return`
<aside class="sidebar" id="sidebar" role="navigation" aria-label="Main navigation">
<div class="sidebar-header">
<a href="/" class="sidebar-logo" aria-label="Home">
<img src="/static/images/logo.png" alt="" class="sidebar-logo-img" loading="lazy">
<div class="sidebar-brand">
<h1 class="sidebar-brand-name">Competence CRM</h1>
<span class="sidebar-brand-role">${role} Portal</span>
</div>
</a>
</div>
<nav class="sidebar-nav">
<div class="sidebar-section">
${items.map(item=>`
<a href="${item.href}" 
   class="sidebar-link${activePage===item.id?' active':''}" 
   aria-current="${activePage===item.id?'page':'false'}"
   data-page="${item.id}">
<span class="sidebar-icon" aria-hidden="true">${getIcon(item.icon)}</span>
<span class="sidebar-text">${item.text}</span>
${item.badge?`<span class="sidebar-badge" aria-label="${item.badge} notifications">${item.badge}</span>`:''}
</a>
`).join('')}
</div>
<div class="sidebar-divider" role="separator"></div>
<div class="sidebar-section">
<button class="sidebar-link" onclick="Profile.showProfileModal()" aria-label="Edit profile">
<span class="sidebar-icon" aria-hidden="true">${getIcon('user')}</span>
<span class="sidebar-text">Profile</span>
</button>
<button class="sidebar-link" onclick="toggleTheme()" aria-label="Toggle theme">
<span class="sidebar-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg></span>
<span class="sidebar-text">Theme</span>
</button>
<button class="sidebar-link" onclick="Auth.logout()" aria-label="Logout">
<span class="sidebar-icon" aria-hidden="true">${getIcon('log-out')}</span>
<span class="sidebar-text">Logout</span>
</button>
</div>
</nav>
</aside>
<button class="sidebar-toggle" id="sidebarToggle" aria-label="Toggle sidebar" aria-expanded="false" aria-controls="sidebar">
<svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
</button>
<div class="sidebar-overlay" id="sidebarOverlay" aria-hidden="true"></div>
`;
};

const init=(role,activePage)=>{
const user=JSON.parse(sessionStorage.getItem('currentUser')||'{}');
const container=document.getElementById('sidebarContainer')||document.body;
const html=render(role,activePage,user);
if(container===document.body){
container.insertAdjacentHTML('afterbegin',html);
}else{
container.innerHTML=html;
}

const sidebar=document.getElementById('sidebar');
const toggle=document.getElementById('sidebarToggle');
const overlay=document.getElementById('sidebarOverlay');

const state=JSON.parse(localStorage.getItem(STORAGE_KEY)||'{"open":false}');
if(window.innerWidth<=768&&state.open){
sidebar.classList.add('open');
overlay.classList.add('show');
toggle.setAttribute('aria-expanded','true');
}

toggle?.addEventListener('click',()=>{
const isOpen=sidebar.classList.toggle('open');
overlay.classList.toggle('show',isOpen);
toggle.setAttribute('aria-expanded',isOpen);
localStorage.setItem(STORAGE_KEY,JSON.stringify({open:isOpen}));
});

overlay?.addEventListener('click',()=>{
sidebar.classList.remove('open');
overlay.classList.remove('show');
toggle.setAttribute('aria-expanded','false');
localStorage.setItem(STORAGE_KEY,JSON.stringify({open:false}));
});

document.addEventListener('keydown',(e)=>{
if(e.key==='Escape'&&sidebar.classList.contains('open')){
sidebar.classList.remove('open');
overlay.classList.remove('show');
toggle.setAttribute('aria-expanded','false');
}
});

sidebar.querySelectorAll('.sidebar-link[href]').forEach(link=>{
link.addEventListener('click',()=>{
if(window.innerWidth<=768){
sidebar.classList.remove('open');
overlay.classList.remove('show');
toggle.setAttribute('aria-expanded','false');
}
});
});
};

window.toggleTheme=()=>{
const current=document.documentElement.getAttribute('data-theme')||'dark';
const next=current==='dark'?'light':'dark';
document.documentElement.setAttribute('data-theme',next);
localStorage.setItem(THEME_KEY,next);
};

window.Sidebar={init,render};
})();
