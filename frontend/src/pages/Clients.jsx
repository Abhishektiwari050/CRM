import React, { useState, useEffect } from 'react';
import { Search, Filter, Download, UserPlus, Trash2 } from 'lucide-react';
import clsx from 'clsx';
import ClientEditModal from '../components/clients/ClientEditModal';
import ClientCreateModal from '../components/clients/ClientCreateModal';

const Clients = () => {
    const [clients, setClients] = useState([]);
    const [employees, setEmployees] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [showCreateModal, setShowCreateModal] = useState(false);
    useEffect(() => {
        const fetchData = async () => {
            try {
                const token = sessionStorage.getItem('token');
                const headers = { 'Authorization': `Bearer ${token}` };

                const [clientsRes, usersRes] = await Promise.all([
                    fetch('/api/clients', { headers }),
                    fetch('/api/users', { headers })
                ]);

                if (clientsRes.ok) {
                    const clientsData = await clientsRes.json();
                    if (clientsData && Array.isArray(clientsData.data)) {
                        setClients(clientsData.data);
                    } else {
                        console.error("Invalid clients data format:", clientsData);
                        setClients([]);
                    }
                }

                if (usersRes.ok) {
                    const usersData = await usersRes.json();
                    if (usersData && Array.isArray(usersData.data)) {
                        setEmployees(usersData.data.filter(u => u.role === 'employee'));
                    } else {
                        setEmployees([]);
                    }
                }
            } catch (error) {
                console.error("Failed to fetch data", error);
                setClients([]); // Fallback
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    const getEmployeeName = (id) => {
        if (!id || !Array.isArray(employees)) return 'Unassigned';
        const emp = employees.find(e => e.id === id);
        return emp ? emp.name : 'Unknown';
    };

    const formatDate = (dateString) => {
        if (!dateString) return '-';
        try {
            const date = new Date(dateString);
            return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleDateString();
        } catch {
            return 'Invalid Date';
        }
    };

    const filteredClients = clients.filter(client => {
        const matchesSearch = (client.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            (client.city || '').toLowerCase().includes(searchTerm.toLowerCase());

        const matchesStatus = statusFilter === 'all' || client.status === statusFilter;

        return matchesSearch && matchesStatus;
    });

    const [editingClient, setEditingClient] = useState(null);

    const handleExport = () => {
        if (!clients.length) return;

        const headers = ["ID", "Name", "City", "Email", "Phone", "Status", "Expiry Date"];
        const csvContent = [
            headers.join(","),
            ...clients.map(c => [
                c.id,
                `"${c.name}"`,
                `"${c.city || ''}"`,
                c.contact_email || '',
                c.contact_phone || '',
                c.status,
                c.expiry_date || ''
            ].join(","))
        ].join("\n");

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        const url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        link.setAttribute("download", "clients_export.csv");
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleEditClick = (client) => {
        setEditingClient(client);
    };

    const handleEditSave = (updatedClient) => {
        setClients(prevClients => prevClients.map(c => c.id === updatedClient.id ? { ...c, ...updatedClient } : c));
        setEditingClient(null);
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Are you sure you want to delete this client? This action cannot be undone.')) {
            return;
        }

        try {
            const token = sessionStorage.getItem('token');
            const res = await fetch(`/api/clients/${id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (res.ok) {
                setClients(prev => prev.filter(c => c.id !== id));
            } else {
                const err = await res.json();
                alert(`Failed to delete: ${err.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Delete failed', error);
            alert('Failed to delete client due to network error.');
        }
    };

    const handleCreateSave = (newClient) => {
        setClients(prev => [...prev, newClient]);
        setShowCreateModal(false);
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
                    <button
                        onClick={() => setShowCreateModal(true)}
                        className="bg-blue-600 text-white px-4 py-2 rounded-xl flex items-center gap-2 font-medium hover:bg-blue-700 transition-all shadow-lg shadow-blue-500/20 active:scale-95"
                    >
                        <UserPlus size={18} />
                        Add Client
                    </button>
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
                                        {formatDate(client.last_contact_date)}
                                    </td>
                                    <td className="px-6 py-4 text-slate-600 text-sm">
                                        {formatDate(client.expiry_date)}
                                    </td>
                                    <td className="px-6 py-4 flex items-center gap-2">
                                        <button
                                            onClick={() => handleEditClick(client)}
                                            className="text-blue-600 hover:bg-blue-50 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
                                        >
                                            Edit
                                        </button>
                                        <button
                                            onClick={() => handleDelete(client.id)}
                                            className="text-red-600 hover:bg-red-50 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1"
                                        >
                                            <Trash2 size={16} />
                                            Delete
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

            {/* Create Modal */}
            {showCreateModal && (
                <ClientCreateModal
                    onClose={() => setShowCreateModal(false)}
                    onSave={handleCreateSave}
                />
            )}
        </div>
    );
};

import ErrorBoundary from '../components/ErrorBoundary';

const ClientsWithBoundary = () => (
    <ErrorBoundary>
        <Clients />
    </ErrorBoundary>
);

export default ClientsWithBoundary;
