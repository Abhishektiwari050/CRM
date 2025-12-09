import React, { useState, useEffect } from 'react';
import { Bell, Info, AlertTriangle, CheckCircle } from 'lucide-react';
import clsx from 'clsx';

const Notifications = () => {
    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchNotifications = async () => {
            try {
                // Endpoint defined in users.py as /api/notifications
                const res = await fetch('/api/notifications', {
                    headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
                });
                const json = await res.json();
                setNotifications(json.data || []);
            } catch (error) {
                console.error("Failed to load notifications", error);
            } finally {
                setLoading(false);
            }
        };
        fetchNotifications();
    }, []);

    const getIcon = (type) => {
        switch (type) {
            case 'critical': return AlertTriangle;
            case 'success': return CheckCircle;
            default: return Info; // 'follow_up', 'info', etc.
        }
    };

    const getColor = (type) => {
        switch (type) {
            case 'critical': return 'text-red-600 bg-red-100';
            case 'success': return 'text-green-600 bg-green-100';
            default: return 'text-blue-600 bg-blue-100';
        }
    };

    if (loading) return <div className="text-center p-10 text-slate-500">Loading Notifications...</div>;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Notifications</h1>
                <p className="text-slate-500 mt-1">Updates and alerts requiring attention.</p>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
                {notifications.length === 0 ? (
                    <div className="p-12 text-center text-slate-400">
                        <Bell size={48} className="mx-auto mb-4 opacity-20" />
                        <p>No new notifications.</p>
                    </div>
                ) : (
                    <div className="divide-y divide-slate-100">
                        {notifications.map((notif) => {
                            const Icon = getIcon(notif.type);
                            const colorClass = getColor(notif.type);
                            return (
                                <div key={notif.id} className="p-4 hover:bg-slate-50 transition-colors flex gap-4">
                                    <div className={clsx("p-3 rounded-xl h-fit", colorClass)}>
                                        <Icon size={20} />
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex justify-between items-start">
                                            <h3 className="font-semibold text-slate-800">{notif.title}</h3>
                                            <span className="text-xs text-slate-400 whitespace-nowrap">
                                                {new Date(notif.created_at).toLocaleString()}
                                            </span>
                                        </div>
                                        <p className="text-slate-600 mt-1 text-sm">{notif.message}</p>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Notifications;
