import React, { useEffect, useState } from 'react';
import { AlertCircle, User, CheckCircle, X } from 'lucide-react';

const DashboardAlerts = () => {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchAlerts = async () => {
        try {
            const res = await fetch('/api/manager/report-flags', {
                headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
            });
            const json = await res.json();
            setAlerts(json.data || []);
        } catch (error) {
            console.error("Failed to fetch alerts", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAlerts();
    }, []);

    const dismissAlert = async (id) => {
        try {
            await fetch('/api/manager/dismiss-flag', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${sessionStorage.getItem('token')}`
                },
                body: JSON.stringify({ notification_id: id })
            });
            // Remove from local state
            setAlerts(prev => prev.filter(a => a.id !== id));
        } catch (error) {
            console.error("Failed to dismiss alert", error);
        }
    };

    if (loading) return null;

    if (alerts.length === 0) return (
        <div className="bg-green-50 border border-green-100 rounded-2xl p-4 flex items-center gap-3 text-green-700">
            <CheckCircle size={20} />
            <span className="font-medium">No system alerts today.</span>
        </div>
    );

    return (
        <div className="bg-red-50 border border-red-100 rounded-2xl p-5">
            <h3 className="flex items-center gap-2 text-red-800 font-bold mb-3">
                <AlertCircle size={20} />
                Repeated Contact Flags (DMR)
            </h3>
            <div className="space-y-3">
                {alerts.map((alert, index) => (
                    <div key={alert.id || index} className="bg-white p-3 rounded-xl border border-red-100 shadow-sm flex justify-between items-start">
                        <div className="flex items-start gap-3">
                            <div className="bg-red-100 p-2 rounded-lg text-red-600 mt-1">
                                <User size={16} />
                            </div>
                            <div>
                                <p className="font-semibold text-slate-800">
                                    {alert.employee_name} <span className="text-slate-400 font-normal">contacted</span> {alert.name}
                                </p>
                                <div className="text-xs text-slate-500 mt-1 flex flex-col gap-1">
                                    <span className="font-medium text-red-600 flex items-center gap-1">
                                        ⚠️ Contacted {alert.count} days in a row
                                    </span>
                                    <span>
                                        {new Date(alert.date).toLocaleDateString(undefined, {
                                            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                                        })}
                                    </span>
                                </div>
                            </div>
                        </div>
                        <button
                            onClick={() => dismissAlert(alert.id)}
                            className="text-slate-400 hover:text-red-500 hover:bg-red-50 p-1 rounded transition-colors"
                            title="Dismiss Alert"
                        >
                            <X size={16} />
                        </button>
                    </div>
                ))}
            </div>
            <p className="text-xs text-red-600 mt-3 font-medium text-center">
                These clients have been contacted excessively (3+ consecutive days). Use with caution.
            </p>
        </div>
    );
};

export default DashboardAlerts;
