import React from 'react';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const getBadgeStyle = (st: string) => {
    switch (st.toUpperCase()) {
      case 'READY':
      case 'DRAFT':
        return 'bg-slate-800 text-slate-300 border-slate-700';
      case 'EXECUTING':
      case 'RUNNING':
        return 'bg-cyan-950/80 text-cyan-400 border-cyan-500/40 animate-pulse';
      case 'VERIFIED':
      case 'COMPLETED':
      case 'APPROVED':
        return 'bg-emerald-950/80 text-emerald-400 border-emerald-500/40';
      case 'PAUSED':
      case 'PENDING':
        return 'bg-amber-950/80 text-amber-400 border-amber-500/40';
      case 'FAILED':
      case 'ABORTED':
      case 'REJECTED':
        return 'bg-rose-950/80 text-rose-400 border-rose-500/40';
      case 'SKIPPED':
        return 'bg-slate-900 text-slate-500 border-slate-800';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium border ${getBadgeStyle(
        status
      )} ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current" />
      {status}
    </span>
  );
}
