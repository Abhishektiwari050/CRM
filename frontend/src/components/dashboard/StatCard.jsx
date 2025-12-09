import React from 'react';
import clsx from 'clsx';

const StatCard = ({ title, value, subtitle, icon: Icon, color = 'blue' }) => {

    const colorStyles = {
        blue: {
            bg: 'bg-blue-50',
            text: 'text-blue-600',
            iconBg: 'bg-blue-100',
            border: 'border-blue-100',
            bar: 'bg-blue-500'
        },
        green: {
            bg: 'bg-green-50',
            text: 'text-green-700', // Making text explicit green
            iconBg: 'bg-green-100',
            border: 'border-green-100',
            bar: 'bg-green-500'
        },
        orange: {
            bg: 'bg-orange-50',
            text: 'text-orange-700', // Explicit orange
            iconBg: 'bg-orange-100',
            border: 'border-orange-100',
            bar: 'bg-orange-500'
        },
        red: {
            bg: 'bg-red-50',
            text: 'text-red-700', // Explicit red
            iconBg: 'bg-red-100',
            border: 'border-red-100',
            bar: 'bg-red-500'
        }
    };

    const styles = colorStyles[color] || colorStyles.blue;

    return (
        <div className={clsx("relative overflow-hidden rounded-2xl p-6 bg-white shadow-sm border transition-all duration-300 hover:-translate-y-1 hover:shadow-md", styles.border)}>
            <div className={clsx("absolute top-0 left-0 w-1 h-full", styles.bar)} />

            <div className="flex justify-between items-start mb-4">
                <div>
                    <h3 className={clsx("text-3xl font-bold mb-1", styles.text)}>{value}</h3>
                    <p className="text-sm font-medium text-slate-500 uppercase tracking-wider">{title}</p>
                </div>
                <div className={clsx("p-3 rounded-xl", styles.iconBg)}>
                    <Icon size={24} className={styles.text} />
                </div>
            </div>

            {subtitle && (
                <p className="text-xs font-medium text-slate-400">
                    {subtitle}
                </p>
            )}
        </div>
    );
};

export default StatCard;
