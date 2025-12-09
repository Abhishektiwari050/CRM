import React, { useState, useEffect } from 'react';
import { Search, Filter, Download, UserPlus } from 'lucide-react';
import clsx from 'clsx';
import ClientEditModal from '../components/clients/ClientEditModal';

const Clients = () => {
    const [clients, setClients] = useState([]);
    const [employees, setEmployees] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const token = sessionStorage.getItem('token');
                const [clientsRes, usersRes] = await Promise.all([
                    fetch('/api/clients', { headers: { 'Authorization': `Bearer ${token}` } }),
                    fetch('/api/users', { headers: { 'Authorization': `Bearer ${token}` } })
                ]);

                const clientsJson = await clientsRes.json();
                const usersJson = await usersRes.json();

                setClients(clientsJson.data || []);
                // Filter users to only show employees (role='employee')
                const allUsers = usersJson.data || [];
                setEmployees(allUsers.filter(u => u.role === 'employee'));
            } catch (error) {
                console.error("Failed to fetch data", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    // Helper to get employee name
    const getEmployeeName = (id) => {
        if (!id) return <span className="text-slate-400 italic">Unassigned</span>;
        const emp = employees.find(e => e.id === id);
        return emp ? emp.name : <span className="text-slate-400">Unknown</span>;
    };

    const filteredClients = clients.filter(client => {
        const matchesSearch = client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            client.city?.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = statusFilter === 'all' || client.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    const handleExport = async () => {
        try {
            const res = await fetch('/api/export/clients', {
                headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
            });
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `clients_export_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
        } catch (error) {
            alert('Export failed');
        }
    };

    const [editingClient, setEditingClient] = useState(null);

    const handleEditClick = (client) => {
        setEditingClient(client);
    };

    const handleEditSave = (updatedClient) => {
        // Update local state locally to reflect changes immediately
        setClients(prevClients => prevClients.map(c => c.id === updatedClient.id ? { ...c, ...updatedClient } : c));
        setEditingClient(null);
    };

    if (loading) return <div className="text-center p-10 text-slate-500">Loading Clients...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight">All Clients</h1>
                    <p className="text-slate-500 mt-1">Manage network and view status.</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={handleExport}
                        className="bg-white border border-slate-200 text-slate-600 px-4 py-2 rounded-xl flex items-center gap-2 font-medium hover:bg-slate-50 transition-colors"
                    >
                        <Download size={18} />
                        Export CSV
                    </button>
                    {/* Add Client Modal would go here */}
                </div>
            </div>

            {/* Filters */}
            <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-3 flex-1 min-w-[200px]">
                    <Search size={20} className="text-slate-400" />
                    <input
                        type="text"
                        placeholder="Search clients by name or city..."
                        className="bg-transparent outline-none w-full text-slate-700 placeholder:text-slate-400"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="h-8 w-px bg-slate-100 mx-2 hidden md:block" />
                <div className="flex gap-2 overflow-x-auto pb-1 md:pb-0">
                    {['all', 'good', 'due_soon', 'overdue'].map(status => (
                        <button
                            key={status}
                            onClick={() => setStatusFilter(status)}
                            className={clsx(
                                "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap capitalize",
                                statusFilter === status
                                    ? "bg-slate-800 text-white"
                                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                            )}
                        >
                            {status.replace('_', ' ')}
                        </button>
                    ))}
                </div>
            </div>

            {/* Table */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-slate-50 border-b border-slate-100 text-xs uppercase tracking-wider text-slate-500 font-semibold">
                                <th className="px-6 py-4">Client Name</th>
                                <th className="px-6 py-4">City</th>
                                <th className="px-6 py-4">Assigned To</th>
                                <th className="px-6 py-4">Status</th>
                                <th className="px-6 py-4">Last Contact</th>
                                <th className="px-6 py-4">Expiry</th>
                                <th className="px-6 py-4">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {filteredClients.map(client => (
                                <tr key={client.id} className="hover:bg-slate-50/50 transition-colors">
                                    <td className="px-6 py-4 font-medium text-slate-800">
                                        {client.name}
                                        <div className="text-xs text-slate-400 font-normal">{client.member_id}</div>
                                    </td>
                                    <td className="px-6 py-4 text-slate-600">{client.city || '-'}</td>
                                    <td className="px-6 py-4 text-slate-600 text-sm">
                                        {getEmployeeName(client.assigned_employee_id)}
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={clsx(
                                            "px-2 py-1 rounded-lg text-xs font-semibold uppercase inline-flex items-center gap-1.5",
                                            client.status === 'good' ? "bg-green-50 text-green-700" :
                                                client.status === 'due_soon' ? "bg-orange-50 text-orange-700" :
                                                    "bg-red-50 text-red-700"
                                        )}>
                                            <div className={clsx("w-1.5 h-1.5 rounded-full animate-pulse",
                                                client.status === 'good' ? "bg-green-500" :
                                                    client.status === 'due_soon' ? "bg-orange-500" :
                                                        "bg-red-500"
                                            )} />
                                            {client.status?.replace('_', ' ')}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-slate-600 text-sm">
                                        {client.last_contact_date ? new Date(client.last_contact_date).toLocaleDateString() : 'Never'}
                                    </td>
                                    <td className="px-6 py-4 text-slate-600 text-sm">
                                        {client.expiry_date ? new Date(client.expiry_date).toLocaleDateString() : '-'}
                                    </td>
                                    <td className="px-6 py-4">
                                        <button
                                            onClick={() => handleEditClick(client)}
                                            className="text-blue-600 hover:bg-blue-50 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
                                        >
                                            Edit
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            {filteredClients.length === 0 && (
                                <tr>
                                    <td colSpan="7" className="px-6 py-12 text-center text-slate-400">
                                        No clients found matching your filters.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Edit Modal */}
            {editingClient && (
                <ClientEditModal
                    client={editingClient}
                    employees={employees}
                    onClose={() => setEditingClient(null)}
                    onSave={handleEditSave}
                />
            )}
        </div>
    );
};

export default Clients;
