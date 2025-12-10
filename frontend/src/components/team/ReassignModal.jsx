import React, { useState } from 'react';
import { ArrowRightLeft, Users, AlertCircle } from 'lucide-react';

const ReassignModal = ({ fromUser, targetUsers, clientCount, onClose, onConfirm }) => {
    const [selectedTargetId, setSelectedTargetId] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!selectedTargetId) return;

        setLoading(true);
        await onConfirm(selectedTargetId);
        setLoading(false);
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center px-4">
            <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={onClose} />
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-md relative z-10 p-6 animate-in zoom-in-95 duration-200">
                <div className="flex items-center gap-3 mb-6 text-slate-800">
                    <div className="bg-blue-50 p-2 rounded-lg text-blue-600">
                        <ArrowRightLeft size={24} />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold">Transfer Clients</h2>
                        <p className="text-sm text-slate-500">Reassign portfolio to another employee.</p>
                    </div>
                </div>

                <div className="bg-orange-50 border border-orange-100 rounded-xl p-4 mb-6 flex gap-3 text-orange-800">
                    <AlertCircle size={20} className="shrink-0 mt-0.5" />
                    <div className="text-sm">
                        You are about to move <strong>{clientCount} clients</strong> from
                        <span className="font-semibold block mt-1">{fromUser.name}</span>
                        to the selected employee below.
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">Transfer To</label>
                        <select
                            required
                            className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                            value={selectedTargetId}
                            onChange={(e) => setSelectedTargetId(e.target.value)}
                        >
                            <option value="">-- Select Employee --</option>
                            {targetUsers.map(user => (
                                <option key={user.id} value={user.id}>
                                    {user.name} ({user.email})
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="flex gap-3 pt-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 text-slate-600 font-medium hover:bg-slate-50 transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={!selectedTargetId || loading}
                            className="flex-1 px-4 py-2.5 rounded-xl bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2"
                        >
                            {loading ? (
                                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <>
                                    <ArrowRightLeft size={18} />
                                    Transfer Now
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default ReassignModal;
