(()=>{
const cache=new Map(),TTL=3e5;
const get=k=>{const i=cache.get(k);if(!i||Date.now()-i.time>TTL){cache.delete(k);return null}return i.data};
const set=(k,d)=>cache.set(k,{data:d,time:Date.now()});
const clear=()=>cache.clear();
window.Cache={get,set,clear};
})();
