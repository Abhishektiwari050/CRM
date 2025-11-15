// Offline mode support
(()=>{
const OFFLINE_KEY='crm_offline_data';
let isOffline=!navigator.onLine;

const saveOffline=(key,data)=>{
try{
const store=JSON.parse(localStorage.getItem(OFFLINE_KEY)||'{}');
store[key]=data;
localStorage.setItem(OFFLINE_KEY,JSON.stringify(store));
}catch(e){console.warn('Offline save failed',e)}
};

const getOffline=(key)=>{
try{
const store=JSON.parse(localStorage.getItem(OFFLINE_KEY)||'{}');
return store[key]||null;
}catch(e){return null}
};

const clearOffline=()=>localStorage.removeItem(OFFLINE_KEY);

window.addEventListener('online',()=>{
isOffline=false;
document.body.classList.remove('offline');
const banner=document.getElementById('offlineBanner');
if(banner)banner.remove();
});

window.addEventListener('offline',()=>{
isOffline=true;
document.body.classList.add('offline');
const banner=document.createElement('div');
banner.id='offlineBanner';
banner.style.cssText='position:fixed;top:0;left:0;right:0;background:#f59e0b;color:#fff;padding:8px;text-align:center;z-index:10000;font-size:14px;font-weight:600';
banner.textContent='⚠️ You are offline. Some features may be limited.';
document.body.prepend(banner);
});

window.Offline={isOffline:()=>isOffline,save:saveOffline,get:getOffline,clear:clearOffline};
})();
