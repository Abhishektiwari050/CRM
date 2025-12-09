import React, { useEffect, useState } from 'react';
import { Clock, Phone, Mail, MessageSquare, CheckCircle, XCircle } from 'lucide-react';
import clsx from 'clsx';

const ActivityFeed = () => {
    const [activities, setActivities] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchActivities = async () => {
            try {
                const res = await fetch('/api/activity-feed?limit=5', {
                    headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
                });
                const json = await res.json();
                setActivities(json.data || []);
            } catch (error) {
                console.error("Failed to load activities", error);
            } finally {
                setLoading(false);
            }
        };
        fetchActivities();
    }, []);

    const getIcon = (category) => {
        switch (category) {
            case 'call': return Phone;
            case 'email': return Mail;
            case 'meeting': return MessageSquare;
            default: return Clock;
        }
    };

    if (loading) return <div className="text-sm text-slate-400">Loading activities...</div>;

    if (activities.length === 0) return <div className="text-sm text-slate-400">No recent activity.</div>;

    return (
        <div className="space-y-4">
            {activities.map((activity) => {
                const Icon = getIcon(activity.category);
                return (
                    <div key={activity.id} className="flex items-start gap-3 p-3 rounded-xl hover:bg-slate-50 transition-colors border border-transparent hover:border-slate-100">
                        <div className={clsx("p-2 rounded-lg shrink-0",
                            activity.category === 'call' ? "bg-blue-100 text-blue-600" :
                                activity.category === 'email' ? "bg-purple-100 text-purple-600" :
                                    "bg-slate-100 text-slate-600"
                        )}>
                            <Icon size={16} />
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-start">
                                <p className="text-sm font-medium text-slate-800 truncate">
                                    {activity.client_name || 'Unknown Client'}
                                </p>
                                <span className="text-xs text-slate-400 whitespace-nowrap ml-2">
                                    {new Date(activity.created_at).toLocaleDateString()}
                                </span>
                            </div>
                            <p className="text-xs text-slate-500 line-clamp-1 mt-0.5">
                                {activity.notes || activity.outcome}
                            </p>
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

export default ActivityFeed;
