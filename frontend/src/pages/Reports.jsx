import React, { useState, useEffect } from 'react';
import { FileText, Download, Calendar } from 'lucide-react';

const Reports = () => {
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchReports = async () => {
            try {
                // Endpoint defined in reports.py as /api/daily-reports
                const res = await fetch('/api/daily-reports', {
                    headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
                });
                const json = await res.json();
                setReports(json.data || []);
            } catch (error) {
                console.error("Failed to load reports", error);
            } finally {
                setLoading(false);
            }
        };
        fetchReports();
    }, []);

    const handleExport = async () => {
        try {
            const res = await fetch('/api/export/daily-reports', {
                headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
            });
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `daily_reports_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
        } catch (error) {
            alert('Export failed');
        }
    };

    const [selectedReport, setSelectedReport] = useState(null);

    const openReport = (report) => setSelectedReport(report);
    const closeReport = () => setSelectedReport(null);

    if (loading) return <div className="text-center p-10 text-slate-500">Loading Reports...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Daily Work Reports</h1>
                    <p className="text-slate-500 mt-1">Review team submissions and performance.</p>
                </div>
                <button
                    onClick={handleExport}
                    className="bg-white border border-slate-200 text-slate-600 px-4 py-2 rounded-xl flex items-center gap-2 font-medium hover:bg-slate-50 transition-colors"
                >
                    <Download size={18} />
                    Export CSV
                </button>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-slate-50 border-b border-slate-100 text-xs uppercase tracking-wider text-slate-500 font-semibold">
                            <th className="px-6 py-4">Date</th>
                            <th className="px-6 py-4">Employee</th>
                            <th className="px-6 py-4 text-center">TA Calls</th>
                            <th className="px-6 py-4 text-center">Renewals</th>
                            <th className="px-6 py-4 text-center">Service</th>
                            <th className="px-6 py-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {reports.map((report) => (
                            <tr key={report.id} className="hover:bg-slate-50/50 transition-colors">
                                <td className="px-6 py-4 text-slate-600 text-sm font-medium">
                                    <div className="flex items-center gap-2">
                                        <Calendar size={14} className="text-slate-400" />
                                        {report.date}
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-2">
                                        <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-bold">
                                            {report.employee_name?.charAt(0) || 'U'}
                                        </div>
                                        <span className="text-slate-700 font-medium">{report.employee_name}</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 text-center text-slate-600">{report.metrics?.ta_calls || 0}</td>
                                <td className="px-6 py-4 text-center text-slate-600">{report.metrics?.renewal_calls || 0}</td>
                                <td className="px-6 py-4 text-center text-slate-600">{report.metrics?.service_calls || 0}</td>
                                <td className="px-6 py-4 text-right">
                                    <button
                                        onClick={() => openReport(report)}
                                        className="text-blue-600 hover:bg-blue-50 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
                                    >
                                        View
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {reports.length === 0 && (
                            <tr>
                                <td colSpan="6" className="px-6 py-12 text-center text-slate-400">
                                    No reports found.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Report Details Modal */}
            {selectedReport && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center px-4">
                    <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={closeReport} />
                    <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl relative z-10 p-6 animate-in zoom-in-95 duration-200">
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <h2 className="text-xl font-bold text-slate-800">Daily Report Details</h2>
                                <p className="text-slate-500 text-sm mt-1">Submitted by <span className="font-semibold text-slate-700">{selectedReport.employee_name}</span> on {selectedReport.date}</p>
                            </div>
                            <button onClick={closeReport} className="text-slate-400 hover:text-slate-600 p-1">
                                <span className="text-2xl">&times;</span>
                            </button>
                        </div>

                        <div className="space-y-6 max-h-[70vh] overflow-y-auto pr-2 custom-scrollbar">
                            <div className="grid grid-cols-3 gap-4">
                                <div className="bg-blue-50 p-4 rounded-xl text-center">
                                    <div className="text-2xl font-bold text-blue-700">{selectedReport.metrics?.ta_calls || 0}</div>
                                    <div className="text-xs font-semibold text-blue-600 uppercase tracking-wide">TA Calls</div>
                                </div>
                                <div className="bg-purple-50 p-4 rounded-xl text-center">
                                    <div className="text-2xl font-bold text-purple-700">{selectedReport.metrics?.renewal_calls || 0}</div>
                                    <div className="text-xs font-semibold text-purple-600 uppercase tracking-wide">Renewals</div>
                                </div>
                                <div className="bg-orange-50 p-4 rounded-xl text-center">
                                    <div className="text-2xl font-bold text-orange-700">{selectedReport.metrics?.service_calls || 0}</div>
                                    <div className="text-xs font-semibold text-orange-600 uppercase tracking-wide">Service</div>
                                </div>
                            </div>

                            <div className="space-y-4">
                                {selectedReport.metrics?.ta_calls_to && (
                                    <div>
                                        <h3 className="text-sm font-semibold text-slate-700 mb-2">Technical Analysis Calls To:</h3>
                                        <div className="bg-slate-50 p-3 rounded-xl text-sm text-slate-600 leading-relaxed border border-slate-100">
                                            {selectedReport.metrics.ta_calls_to}
                                        </div>
                                    </div>
                                )}
                                {selectedReport.metrics?.renewal_calls_to && (
                                    <div>
                                        <h3 className="text-sm font-semibold text-slate-700 mb-2">Renewal Calls To:</h3>
                                        <div className="bg-slate-50 p-3 rounded-xl text-sm text-slate-600 leading-relaxed border border-slate-100">
                                            {selectedReport.metrics.renewal_calls_to}
                                        </div>
                                    </div>
                                )}
                                {selectedReport.metrics?.service_calls_to && (
                                    <div>
                                        <h3 className="text-sm font-semibold text-slate-700 mb-2">Service Calls To:</h3>
                                        <div className="bg-slate-50 p-3 rounded-xl text-sm text-slate-600 leading-relaxed border border-slate-100">
                                            {selectedReport.metrics.service_calls_to}
                                        </div>
                                    </div>
                                )}

                                <div className="grid grid-cols-2 gap-4 pt-2">
                                    <div className="bg-yellow-50 p-3 rounded-xl flex justify-between items-center border border-yellow-100">
                                        <span className="text-sm font-medium text-yellow-800">1 Star Calls</span>
                                        <span className="text-lg font-bold text-yellow-700">{selectedReport.metrics?.one_star_calls || 0}</span>
                                    </div>
                                    <div className="bg-slate-100 p-3 rounded-xl flex justify-between items-center border border-slate-200">
                                        <span className="text-sm font-medium text-slate-700">0 Star Calls</span>
                                        <span className="text-lg font-bold text-slate-600">{selectedReport.metrics?.zero_star_calls || 0}</span>
                                    </div>
                                </div>

                                {selectedReport.metrics?.additional_info && (
                                    <div>
                                        <h3 className="text-sm font-semibold text-slate-700 mb-2">Additional Notes:</h3>
                                        <div className="bg-slate-50 p-4 rounded-xl text-sm text-slate-600 italic border border-slate-100">
                                            "{selectedReport.metrics.additional_info}"
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Reports;
