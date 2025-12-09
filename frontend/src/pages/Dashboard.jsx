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

    useEffect(() => {
        const fetchData = async () => {
            try {
                // 1. Fetch Stats
                const statsRes = await fetch('/api/manager/stats', { headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` } }); // TODO: Auth Context
                const statsJson = await statsRes.json();
                setStats(statsJson);

                // 2. Fetch Clients for Charts (Simulating chart logic from backend/frontend)
                // In React, we'll fetch clients list and aggregate locally for now, 
                // matching the logic in employee_dashboard.js
                // Ideally backend should provide chart data, but we'll stick to parity.
                const clientsRes = await fetch('/api/clients', { headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` } });
                const clients = (await clientsRes.json()).data || [];

                // Process Charts
                // Pie: Status
                const statusCounts = { Good: 0, Due: 0, Overdue: 0 };
                const contactBuckets = { '<7 Days': 0, '7-14 Days': 0, '15-30 Days': 0, '>30 Days': 0 };

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
                    else statusCounts.Overdue++;

                    // Activity
                    if (diff < 7) contactBuckets['<7 Days']++;
                    else if (diff <= 14) contactBuckets['7-14 Days']++;
                    else if (diff <= 30) contactBuckets['15-30 Days']++;
                    else contactBuckets['>30 Days']++;
                });

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

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Manager Overview</h1>
                <p className="text-slate-500 mt-1">Real-time performance metrics and team insights.</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Total Employees"
                    value={stats?.employees || 0}
                    icon={Users}
                    color="blue"
                    subtitle="Active team members"
                />
                <StatCard
                    title="Total Clients"
                    value={stats?.clients || 0}
                    icon={UserCheck}
                    color="green" // Using green variant
                    subtitle="In system"
                />
                <StatCard
                    title="Overdue Clients"
                    value={stats?.overdue || 0}
                    icon={AlertOctagon}
                    color="red" // Explicit red
                    subtitle="Needs attention"
                />
                <StatCard
                    title="Team Efficiency"
                    value={`${stats?.efficiency || 0}%`}
                    icon={TrendingUp}
                    color="orange" // Orange for metrics
                    subtitle="Based on activity"
                />
            </div>

            {/* Alerts Section (DMR Flags) */}
            <DashboardAlerts />

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
