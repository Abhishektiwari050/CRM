import React, { useEffect, useState } from 'react';
import { AlertCircle, User, CheckCircle } from 'lucide-react';

const DashboardAlerts = () => {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
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
        fetchAlerts();
    }, []);

    if (loading) return null; // Don't show anything while loading to avoid layout shift or just show spinner if critical

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
                    <div key={index} className="bg-white p-3 rounded-xl border border-red-100 shadow-sm flex justify-between items-center">
                        <div className="flex items-center gap-3">
                            <div className="bg-red-100 p-2 rounded-lg text-red-600">
                                <User size={16} />
                            </div>
                            <div>
                                <p className="font-semibold text-slate-800">{alert.name}</p>
                                <p className="text-xs text-slate-500">Contacted {alert.count} days in a row</p>
                            </div>
                        </div>
                        <span className="text-xs font-mono bg-slate-100 px-2 py-1 rounded text-slate-600">
                            ID: {alert.employee_id}
                        </span>
                    </div>
                ))}
            </div>
            <p className="text-xs text-red-600 mt-3 font-medium text-center">
                These clients have been contacted excessively.
            </p>
        </div>
    );
};

export default DashboardAlerts;
