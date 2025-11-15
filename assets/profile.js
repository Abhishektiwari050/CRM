// User profile management
(()=>{
const API=window.location.origin;

const updateProfile=async(data)=>{
const token=localStorage.getItem('token');
const res=await fetch(`${API}/api/profile`,{
method:'PUT',
headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},
body:JSON.stringify(data)
});
if(!res.ok)throw new Error('Update failed');
return res.json();
};

const changePassword=async(oldPass,newPass)=>{
const token=localStorage.getItem('token');
const res=await fetch(`${API}/api/profile/password`,{
method:'PUT',
headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},
body:JSON.stringify({old_password:oldPass,new_password:newPass})
});
if(!res.ok)throw new Error('Password change failed');
return res.json();
};

const showProfileModal=()=>{
const modal=document.createElement('div');
modal.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:10000;display:flex;align-items:center;justify-content:center';
modal.innerHTML=`<div style="background:#fff;border-radius:12px;padding:24px;max-width:400px;width:90%">
<h3 style="margin:0 0 16px;font-size:20px">Edit Profile</h3>
<form id="profileForm">
<div style="margin-bottom:16px"><label style="display:block;margin-bottom:8px;font-weight:600">Name</label><input type="text" id="profileName" style="width:100%;padding:10px;border:2px solid #e2e8f0;border-radius:8px" required></div>
<div style="margin-bottom:16px"><label style="display:block;margin-bottom:8px;font-weight:600">Email</label><input type="email" id="profileEmail" style="width:100%;padding:10px;border:2px solid #e2e8f0;border-radius:8px" required></div>
<div style="display:flex;gap:12px;margin-top:20px">
<button type="submit" style="flex:1;padding:10px;background:#3b82f6;color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:600">Save</button>
<button type="button" onclick="this.closest('div[style*=fixed]').remove()" style="flex:1;padding:10px;background:#64748b;color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:600">Cancel</button>
</div>
</form>
</div>`;
document.body.appendChild(modal);
const user=JSON.parse(sessionStorage.getItem('currentUser')||'{}');
document.getElementById('profileName').value=user.name||'';
document.getElementById('profileEmail').value=user.email||'';
document.getElementById('profileForm').onsubmit=async(e)=>{
e.preventDefault();
try{
await updateProfile({name:document.getElementById('profileName').value,email:document.getElementById('profileEmail').value});
alert('Profile updated');
modal.remove();
location.reload();
}catch(err){alert('Update failed: '+err.message)}
};
};

const showPasswordModal=()=>{
const modal=document.createElement('div');
modal.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:10000;display:flex;align-items:center;justify-content:center';
modal.innerHTML=`<div style="background:#fff;border-radius:12px;padding:24px;max-width:400px;width:90%">
<h3 style="margin:0 0 16px;font-size:20px">Change Password</h3>
<form id="passwordForm">
<div style="margin-bottom:16px"><label style="display:block;margin-bottom:8px;font-weight:600">Current Password</label><input type="password" id="oldPass" style="width:100%;padding:10px;border:2px solid #e2e8f0;border-radius:8px" required></div>
<div style="margin-bottom:16px"><label style="display:block;margin-bottom:8px;font-weight:600">New Password</label><input type="password" id="newPass" style="width:100%;padding:10px;border:2px solid #e2e8f0;border-radius:8px" required minlength="8"></div>
<div style="margin-bottom:16px"><label style="display:block;margin-bottom:8px;font-weight:600">Confirm Password</label><input type="password" id="confirmPass" style="width:100%;padding:10px;border:2px solid #e2e8f0;border-radius:8px" required></div>
<div style="display:flex;gap:12px;margin-top:20px">
<button type="submit" style="flex:1;padding:10px;background:#3b82f6;color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:600">Change</button>
<button type="button" onclick="this.closest('div[style*=fixed]').remove()" style="flex:1;padding:10px;background:#64748b;color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:600">Cancel</button>
</div>
</form>
</div>`;
document.body.appendChild(modal);
document.getElementById('passwordForm').onsubmit=async(e)=>{
e.preventDefault();
const newPass=document.getElementById('newPass').value;
const confirmPass=document.getElementById('confirmPass').value;
if(newPass!==confirmPass)return alert('Passwords do not match');
try{
await changePassword(document.getElementById('oldPass').value,newPass);
alert('Password changed successfully');
modal.remove();
}catch(err){alert('Password change failed: '+err.message)}
};
};

window.Profile={update:updateProfile,changePassword,showProfileModal,showPasswordModal};
})();
