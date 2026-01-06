import React, { useEffect, useState } from 'react';
import { Users, UserCheck, AlertOctagon, TrendingUp } from 'lucide-react';
import StatCard from '../components/dashboard/StatCard';
import ClientChart from '../components/dashboard/ClientChart';
import ActivityFeed from '../components/dashboard/ActivityFeed';
import DashboardAlerts from '../components/dashboard/DashboardAlerts';

const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [chartsData, setChartsData] = useState({ pie: null, bar: null });
    const [loading, setLoading] = useState(true);
    const [userRole, setUserRole] = useState('');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const user = JSON.parse(sessionStorage.getItem('currentUser') || '{}');
                const role = (user.role || '').toLowerCase();
                setUserRole(role);

                let fetchedStats = {};

                // 1. Fetch Stats (Manager Only)
                if (role === 'manager' || role === 'admin') {
                    const statsRes = await fetch('/api/manager/stats', { headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` } });
                    fetchedStats = await statsRes.json();
                }

                // 2. Fetch Clients & Calculate Charts/Employee Stats
                const clientsRes = await fetch('/api/clients', { headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` } });
                const clients = (await clientsRes.json()).data || [];

                // Common aggregation
                const statusCounts = { Good: 0, Due: 0, Overdue: 0 };
                const contactBuckets = { '<7 Days': 0, '7-14 Days': 0, '15-30 Days': 0, '>30 Days': 0 };

                let overdueCount = 0;
                const now = new Date();

                clients.forEach(c => {
                    // Status
                    let status = 'Overdue';
                    let diff = 999;
                    if (c.last_contact_date) {
                        diff = Math.floor((now - new Date(c.last_contact_date)) / (1000 * 60 * 60 * 24));
                        if (diff < 7) status = 'Good';
                        else if (diff <= 14) status = 'Due Soon';
                    }

                    if (status === 'Good') statusCounts.Good++;
                    else if (status === 'Due Soon') statusCounts.Due++;
                    else { statusCounts.Overdue++; overdueCount++; }

                    // Activity
                    if (diff < 7) contactBuckets['<7 Days']++;
                    else if (diff <= 14) contactBuckets['7-14 Days']++;
                    else if (diff <= 30) contactBuckets['15-30 Days']++;
                    else contactBuckets['>30 Days']++;
                });

                // If Employee, calculate stats locally
                if (role === 'employee') {
                    fetchedStats = {
                        employees: 1, // Self
                        clients: clients.length,
                        overdue: overdueCount,
                        efficiency: clients.length > 0 ? Math.round(((clients.length - overdueCount) / clients.length) * 100) : 0
                    };
                }

                setStats(fetchedStats);

                setChartsData({
                    pie: {
                        labels: ['Good', 'Due Soon', 'Overdue'],
                        datasets: [{
                            data: [statusCounts.Good, statusCounts.Due, statusCounts.Overdue],
                            backgroundColor: ['#22c55e', '#f97316', '#ef4444'],
                            borderWidth: 0,
                        }]
                    },
                    bar: {
                        labels: Object.keys(contactBuckets),
                        datasets: [{
                            label: 'Clients',
                            data: Object.values(contactBuckets),
                            backgroundColor: '#3b82f6',
                            borderRadius: 4,
                        }]
                    }
                });

            } catch (error) {
                console.error("Failed to load dashboard", error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    if (loading) return <div className="min-h-screen flex items-center justify-center text-blue-600 font-medium">Loading Dashboard...</div>;

    const isManager = userRole === 'manager' || userRole === 'admin';

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-slate-800 tracking-tight">
                    {isManager ? 'Manager Overview' : 'Employee Dashboard'}
                </h1>
                <p className="text-slate-500 mt-1">
                    {isManager ? 'Real-time performance metrics and team insights.' : 'Track your client portfolio and performance.'}
                </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {isManager && (
                    <StatCard
                        title="Total Employees"
                        value={stats?.employees || 0}
                        icon={Users}
                        color="blue"
                        subtitle="Active team members"
                    />
                )}
                <StatCard
                    title="Total Clients"
                    value={stats?.clients || 0}
                    icon={UserCheck}
                    color="green"
                    subtitle={isManager ? "In system" : "Assigned to you"}
                />
                <StatCard
                    title="Overdue Clients"
                    value={stats?.overdue || 0}
                    icon={AlertOctagon}
                    color="red"
                    subtitle="Needs attention"
                />
                <StatCard
                    title="Efficiency Score"
                    value={`${stats?.efficiency || 0}%`}
                    icon={TrendingUp}
                    color="orange"
                    subtitle="Based on activity"
                />
            </div>

            {/* Alerts Section (Manager Only) */}
            {isManager && <DashboardAlerts />}

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    <ClientChart type="bar" data={chartsData.bar} title="Contact Recency" />
                    <ClientChart type="pie" data={chartsData.pie} title="Client Status Distribution" />
                </div>

                {/* Activity Feed */}
                <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 h-fit">
                    <h2 className="text-lg font-bold text-slate-800 mb-4">Recent Activity</h2>
                    <ActivityFeed />
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
