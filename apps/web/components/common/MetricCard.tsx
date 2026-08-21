import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  icon?: React.ReactNode;
  trend?: string;
  className?: string;
}

export function MetricCard({
  label,
  value,
  subValue,
  icon,
  trend,
  className = '',
}: MetricCardProps) {
  return (
    <div
      className={`bg-slate-900/90 border border-slate-800 rounded-lg p-4 flex flex-col justify-between ${className}`}
    >
      <div className="flex items-center justify-between text-slate-400 mb-2">
        <span className="text-xs font-mono uppercase tracking-wider">{label}</span>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>
      <div>
        <div className="text-2xl font-bold text-slate-100 font-mono tracking-tight">{value}</div>
        {(subValue || trend) && (
          <div className="flex items-center justify-between mt-1 text-xs text-slate-400 font-mono">
            {subValue && <span>{subValue}</span>}
            {trend && <span className="text-cyan-400">{trend}</span>}
          </div>
        )}
      </div>
    </div>
  );
}
