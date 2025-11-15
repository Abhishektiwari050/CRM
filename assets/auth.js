(()=>{
const API=window.location.hostname==='localhost'&&window.location.port==='3000'?'http://localhost:8000':window.location.origin;
const TOKEN_KEY='token',USER_KEY='currentUser';
const getToken=()=>localStorage.getItem(TOKEN_KEY);
const setToken=t=>localStorage.setItem(TOKEN_KEY,t);
const clearToken=()=>{localStorage.removeItem(TOKEN_KEY);sessionStorage.removeItem(USER_KEY)};
const getUser=()=>{try{const u=sessionStorage.getItem(USER_KEY);return u?JSON.parse(u):null}catch{return null}};
const setUser=u=>sessionStorage.setItem(USER_KEY,JSON.stringify(u));
const logout=()=>{clearToken();location.href='/login_page/code.html'};
const checkAuth=async(requiredRole=null)=>{
const user=getUser(),token=getToken();
if(!user||!token){location.href='/login_page/code.html';return null}
if(requiredRole&&user.role!==requiredRole&&user.role!=='admin'){location.href=user.role==='manager'?'/manager_dashboard_page/code.html':'/employee_dashboard_page/code.html';return null}
return user
};
const apiCall=async(endpoint,options={})=>{
const headers={'Content-Type':'application/json',...(options.headers||{})};
const token=getToken();
if(token)headers.Authorization=`Bearer ${token}`;
const res=await fetch(`${API}${endpoint}`,{...options,headers});
if(res.status===401){clearToken();location.href='/login_page/code.html';throw new Error('Unauthorized')}
if(!res.ok){const err=await res.json().catch(()=>({error:{message:'Request failed'}}));throw new Error(err.error?.message||err.detail||'Request failed')}
return res.headers.get('content-type')?.includes('json')?await res.json():await res.text()
};
window.Auth={getToken,setToken,clearToken,getUser,setUser,logout,checkAuth,apiCall};
})();
