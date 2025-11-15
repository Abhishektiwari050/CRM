// Bulk operations for client management
(()=>{
const API=window.location.origin;

const bulkAssign=async(clientIds,employeeId)=>{
const token=localStorage.getItem('token');
const res=await fetch(`${API}/api/clients/bulk-assign`,{
method:'POST',
headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},
body:JSON.stringify({client_ids:clientIds,employee_id:employeeId})
});
if(!res.ok)throw new Error('Bulk assign failed');
return res.json();
};

const showBulkAssignModal=(selectedIds)=>{
if(!selectedIds||selectedIds.length===0)return alert('No clients selected');
const modal=document.createElement('div');
modal.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:10000;display:flex;align-items:center;justify-content:center';
modal.innerHTML=`<div style="background:#fff;border-radius:12px;padding:24px;max-width:400px;width:90%">
<h3 style="margin:0 0 16px;font-size:20px">Bulk Assign ${selectedIds.length} Clients</h3>
<form id="bulkForm">
<div style="margin-bottom:16px"><label style="display:block;margin-bottom:8px;font-weight:600">Assign To Employee</label><select id="bulkEmployee" style="width:100%;padding:10px;border:2px solid #e2e8f0;border-radius:8px" required></select></div>
<div style="display:flex;gap:12px;margin-top:20px">
<button type="submit" style="flex:1;padding:10px;background:#10b981;color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:600">Assign</button>
<button type="button" onclick="this.closest('div[style*=fixed]').remove()" style="flex:1;padding:10px;background:#64748b;color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:600">Cancel</button>
</div>
</form>
</div>`;
document.body.appendChild(modal);
(async()=>{
const token=localStorage.getItem('token');
const res=await fetch(`${API}/api/users`,{headers:{Authorization:`Bearer ${token}`}});
const data=await res.json();
const sel=document.getElementById('bulkEmployee');
sel.innerHTML='<option value="">-- Select Employee --</option>'+data.data.filter(u=>u.role==='employee').map(u=>`<option value="${u.id}">${u.name}</option>`).join('');
})();
document.getElementById('bulkForm').onsubmit=async(e)=>{
e.preventDefault();
const empId=document.getElementById('bulkEmployee').value;
if(!empId)return alert('Select an employee');
try{
await bulkAssign(selectedIds,empId);
alert(`${selectedIds.length} clients assigned successfully`);
modal.remove();
location.reload();
}catch(err){alert('Bulk assign failed: '+err.message)}
};
};

window.BulkOps={assign:bulkAssign,showAssignModal:showBulkAssignModal};
})();
