import React from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

const ClientChart = ({ type, data, title }) => {
    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: 'bottom',
                labels: { usePointStyle: true, font: { family: 'Inter', size: 12 } }
            },
            title: {
                display: !!title,
                text: title,
                font: { size: 16, weight: 'bold' },
                padding: { bottom: 20 }
            }
        },
        maintainAspectRatio: false,
    };

    if (!data) return <div className="h-64 flex items-center justify-center text-slate-400">No Data</div>;

    return (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 h-80">
            {type === 'pie' ? <Pie data={data} options={options} /> : <Bar data={data} options={options} />}
        </div>
    );
};

export default ClientChart;
