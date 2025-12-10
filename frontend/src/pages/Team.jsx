import React, { useState, useEffect } from 'react';
import { UserPlus, Trash2, Search, Mail, User, ChevronDown, ChevronUp, Briefcase, ArrowRightLeft } from 'lucide-react';
import clsx from 'clsx';
import UserEditModal from '../components/team/UserEditModal';
import ReassignModal from '../components/team/ReassignModal';

const Team = () => {
    const [employees, setEmployees] = useState([]);
    const [clients, setClients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [expandedEmployeeId, setExpandedEmployeeId] = useState(null);

    // State for actions
    const [editingUser, setEditingUser] = useState(null);
    const [reassigningUser, setReassigningUser] = useState(null); // The user we are moving FROM

    const handleEditSave = (updatedUser) => {
        setEmployees(prev => prev.map(u => u.id === updatedUser.id ? { ...u, ...updatedUser } : u));
        setEditingUser(null);
    };

    // Form State
    const [formData, setFormData] = useState({ name: '', email: '', password: '' });

    const fetchData = async () => {
        setLoading(true);
        try {
            const token = sessionStorage.getItem('token');
            const headers = { 'Authorization': `Bearer ${token}` };

            const [usersRes, clientsRes] = await Promise.all([
                fetch('/api/users', { headers }),
                fetch('/api/clients', { headers })
            ]);

            if (usersRes.ok) {
                const json = await usersRes.json();
                setEmployees((json.data || []).filter(u => u.role === 'employee'));
            }

            if (clientsRes.ok) {
                const json = await clientsRes.json();
                setClients(json.data || []);
            }

        } catch (e) {
            console.error("Error fetching team data", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleDelete = async (id) => {
        if (!confirm('Are you sure you want to delete this employee?')) return;
        try {
            const res = await fetch(`/api/admin/users/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
            });
            if (res.ok) {
                setEmployees(prev => prev.filter(e => e.id !== id));
            } else {
                alert('Failed to delete');
            }
        } catch (e) {
            alert('Error deleting user');
        }
    };

    const handleBulkReassign = async (targetId) => {
        if (!reassigningUser) return;

        try {
            const fromId = reassigningUser.id;
            const clientsToMove = clients.filter(c => c.assigned_employee_id === fromId).map(c => c.id);

            if (clientsToMove.length === 0) {
                alert("This user has no clients to transfer.");
                setReassigningUser(null);
                return;
            }

            const token = sessionStorage.getItem('token');
            const res = await fetch('/api/clients/bulk-assign', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    client_ids: clientsToMove,
                    employee_id: targetId
                })
            });

            if (res.ok) {
                // Optimistic UI Update
                setClients(prev => prev.map(c =>
                    c.assigned_employee_id === fromId
                        ? { ...c, assigned_employee_id: targetId }
                        : c
                ));
                setReassigningUser(null);
            } else {
                const err = await res.json();
                alert(err.detail || 'Transfer failed');
            }
        } catch (error) {
            console.error(error);
            alert('Network error during transfer');
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            const res = await fetch('/api/employees', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${sessionStorage.getItem('token')}`
                },
                body: JSON.stringify(formData)
            });

            if (res.ok) {
                setIsModalOpen(false);
                setFormData({ name: '', email: '', password: '' });
                fetchData(); // Refresh list
            } else {
                const err = await res.json();
                alert(err.detail || 'Failed to create');
            }
        } catch (e) {
            console.error(e);
            alert('Error creating employee');
        }
    };

    const toggleExpand = (id) => {
        setExpandedEmployeeId(prev => prev === id ? null : id);
    };

    const getAssignedClients = (employeeId) => {
        return clients.filter(c => c.assigned_employee_id === employeeId);
    };

    const filteredEmployees = employees.filter(e =>
        e.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        e.email.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) return <div className="text-center p-10 text-slate-500">Loading Team...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Team Management</h1>
                    <p className="text-slate-500 mt-1">Manage employee access and accounts.</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl flex items-center gap-2 font-medium transition-colors shadow-sm"
                >
                    <UserPlus size={18} />
                    Add Employee
                </button>
            </div>

            {/* Search */}
            <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-3 w-full md:w-96">
                <Search size={20} className="text-slate-400" />
                <input
                    type="text"
                    placeholder="Search employees..."
                    className="bg-transparent outline-none w-full text-slate-700 placeholder:text-slate-400"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
            </div>

            {/* Table */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-slate-50 border-b border-slate-100 text-xs uppercase tracking-wider text-slate-500 font-semibold">
                            <th className="px-6 py-4 w-12"></th>
                            <th className="px-6 py-4">Name</th>
                            <th className="px-6 py-4">Email</th>
                            <th className="px-6 py-4">Role</th>
                            <th className="px-6 py-4">Status</th>
                            <th className="px-6 py-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {filteredEmployees.map(employee => {
                            const isExpanded = expandedEmployeeId === employee.id;
                            const assigned = getAssignedClients(employee.id);

                            return (
                                <React.Fragment key={employee.id}>
                                    <tr className={clsx("hover:bg-slate-50/50 transition-colors cursor-pointer", isExpanded && "bg-slate-50")} onClick={() => toggleExpand(employee.id)}>
                                        <td className="px-6 py-4 text-slate-400">
                                            {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                                        </td>
                                        <td className="px-6 py-4 font-medium text-slate-800 flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-xs">
                                                {employee.name.charAt(0)}
                                            </div>
                                            <div>
                                                {employee.name}
                                                <div className="text-xs text-slate-400 font-normal">{assigned.length} Clients</div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-slate-600">
                                            <div className="flex items-center gap-2">
                                                <Mail size={14} className="text-slate-400" />
                                                {employee.email}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="bg-slate-100 text-slate-600 px-2 py-1 rounded-lg text-xs font-semibold uppercase">
                                                {employee.role}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="bg-green-50 text-green-700 px-2 py-1 rounded-lg text-xs font-semibold uppercase flex items-center gap-1 w-fit">
                                                <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                                                Active
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right" onClick={e => e.stopPropagation()}>
                                            <div className="flex justify-end gap-2">
                                                <button
                                                    onClick={() => setReassigningUser(employee)}
                                                    className="bg-orange-50 text-orange-600 hover:bg-orange-100 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 disabled:opacity-50"
                                                    disabled={assigned.length === 0}
                                                    title={assigned.length === 0 ? "No clients to transfer" : "Transfer Clients"}
                                                >
                                                    <ArrowRightLeft size={16} />
                                                    Transfer
                                                </button>
                                                <button
                                                    onClick={() => setEditingUser(employee)}
                                                    className="text-blue-600 hover:bg-blue-50 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
                                                >
                                                    Edit
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(employee.id)}
                                                    className="text-slate-400 hover:text-red-600 transition-colors p-2 rounded-lg hover:bg-red-50"
                                                >
                                                    <Trash2 size={18} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                    {isExpanded && (
                                        <tr className="bg-slate-50/50">
                                            <td colSpan="6" className="px-6 pb-6 pt-2">
                                                <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm ml-12 animate-in slide-in-from-top-2 duration-200">
                                                    <h3 className="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
                                                        <Briefcase size={16} className="text-blue-600" />
                                                        Assigned Clients
                                                        <span className="bg-slate-100 text-slate-600 px-2.5 py-0.5 rounded-full text-xs ml-auto">
                                                            {assigned.length} Total
                                                        </span>
                                                    </h3>
                                                    {assigned.length > 0 ? (
                                                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                                                            {assigned.map(client => (
                                                                <div key={client.id} className="p-3 bg-white border border-slate-200 rounded-lg hover:border-blue-300 hover:shadow-md transition-all group">
                                                                    <div className="flex justify-between items-start mb-2">
                                                                        <div className="font-semibold text-slate-900 text-sm truncate pr-2" title={client.name}>
                                                                            {client.name}
                                                                        </div>
                                                                        <div className={clsx(
                                                                            "text-[10px] uppercase font-bold px-1.5 py-0.5 rounded border",
                                                                            client.status === 'good' ? "bg-green-50 text-green-700 border-green-100" :
                                                                                client.status === 'due_soon' ? "bg-orange-50 text-orange-700 border-orange-100" :
                                                                                    "bg-red-50 text-red-700 border-red-100"
                                                                        )}>
                                                                            {client.status?.replace('_', ' ')}
                                                                        </div>
                                                                    </div>

                                                                    <div className="space-y-1">
                                                                        <div className="text-xs text-slate-500 flex items-center justify-between">
                                                                            <span>City:</span>
                                                                            <span className="text-slate-700 font-medium">{client.city || '-'}</span>
                                                                        </div>
                                                                        <div className="text-xs text-slate-500 flex items-center justify-between">
                                                                            <span>Expires:</span>
                                                                            <span className="text-slate-700 font-medium whitespace-nowrap">
                                                                                {client.expiry_date ? new Date(client.expiry_date).toLocaleDateString() : '-'}
                                                                            </span>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    ) : (
                                                        <div className="text-center py-8 bg-slate-50 rounded-lg border border-dashed border-slate-200 text-slate-400 text-sm">
                                                            No clients currently assigned to this employee.
                                                        </div>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </React.Fragment>
                            );
                        })}
                        {filteredEmployees.length === 0 && (
                            <tr>
                                <td colSpan="6" className="px-6 py-12 text-center text-slate-400">
                                    No employees found.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Create Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center px-4">
                    <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={() => setIsModalOpen(false)} />
                    <div className="bg-white rounded-2xl shadow-xl w-full max-w-md relative z-10 p-6 animate-in zoom-in-95 duration-200">
                        <h2 className="text-xl font-bold text-slate-800 mb-1">Add New Employee</h2>
                        <p className="text-slate-500 text-sm mb-6">Create credentials for a new team member.</p>

                        <form onSubmit={handleCreate} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
                                <div className="relative">
                                    <User size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                    <input
                                        type="text"
                                        required
                                        className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                                        placeholder="John Doe"
                                        value={formData.name}
                                        onChange={e => setFormData({ ...formData, name: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
                                <div className="relative">
                                    <Mail size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                    <input
                                        type="email"
                                        required
                                        className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                                        placeholder="john@example.com"
                                        value={formData.email}
                                        onChange={e => setFormData({ ...formData, email: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
                                <input
                                    type="password"
                                    required
                                    className="w-full px-4 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                                    placeholder="••••••••"
                                    value={formData.password}
                                    onChange={e => setFormData({ ...formData, password: e.target.value })}
                                />
                            </div>

                            <div className="flex gap-3 mt-6 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    className="flex-1 px-4 py-2 rounded-xl border border-slate-200 text-slate-600 font-medium hover:bg-slate-50 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 px-4 py-2 rounded-xl bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors shadow-sm"
                                >
                                    Create Account
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Edit Modal */}
            {editingUser && (
                <UserEditModal
                    user={editingUser}
                    onClose={() => setEditingUser(null)}
                    onSave={handleEditSave}
                />
            )}

            {/* Reassign Modal */}
            {reassigningUser && (
                <ReassignModal
                    fromUser={reassigningUser}
                    targetUsers={employees.filter(e => e.id !== reassigningUser.id)}
                    clientCount={getAssignedClients(reassigningUser.id).length}
                    onClose={() => setReassigningUser(null)}
                    onConfirm={handleBulkReassign}
                />
            )}
        </div>
    );
};

export default Team;
