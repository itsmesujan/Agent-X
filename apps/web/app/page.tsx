'use client';

import React from 'react';
import Link from 'next/link';
import { useMission } from '@/lib/context';
import { MetricCard } from '@/components/common/MetricCard';
import { StatusBadge } from '@/components/common/StatusBadge';
import { Shield, Plus, ArrowUpRight, Activity, Cpu, CheckCircle2, AlertCircle } from 'lucide-react';

export default function DashboardPage() {
  const { missions, isLoading, isLiveConnected } = useMission();

  const totalSpent = missions.reduce((acc, m) => acc + (m.current_usd_spent || 0), 0);
  const totalTasks = missions.reduce((acc, m) => acc + (m.task_count || 0), 0);
  const executingCount = missions.filter((m) => m.status === 'EXECUTING').length;
  const completedCount = missions.filter((m) => m.status === 'COMPLETED').length;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100 font-mono tracking-tight">
            FLEET MISSION DASHBOARD
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Real-time telemetry and state synchronization across active autonomous missions.
          </p>
        </div>
        <Link
          href="/missions/new"
          className="flex items-center gap-1.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 px-4 py-2 rounded-lg text-xs font-bold font-mono transition-colors shadow-lg shadow-cyan-500/20"
        >
          <Plus className="w-4 h-4" />
          <span>NEW MISSION</span>
        </Link>
      </div>

      {/* Fleet KPI Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Missions"
          value={missions.length}
          subValue={`${executingCount} Active | ${completedCount} Verified`}
          icon={<Shield className="w-4 h-4 text-cyan-400" />}
        />
        <MetricCard
          label="Total Budget Spent"
          value={`$${totalSpent.toFixed(2)}`}
          subValue="Across all missions"
          icon={<Cpu className="w-4 h-4 text-emerald-400" />}
        />
        <MetricCard
          label="Managed Tasks"
          value={totalTasks}
          subValue="DAG Nodes"
          icon={<CheckCircle2 className="w-4 h-4 text-blue-400" />}
        />
        <MetricCard
          label="Cluster Connectivity"
          value={isLiveConnected ? 'HEALTHY' : 'DISCONNECTED'}
          subValue="FastAPI + Cloud Pub/Sub"
          icon={<Activity className="w-4 h-4 text-emerald-400" />}
        />
      </div>

      {/* Missions Table */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="text-xs font-mono font-bold text-slate-200 tracking-wider uppercase">
            ACTIVE MISSION FLEET ({missions.length})
          </div>
          <span className="text-xs font-mono text-slate-500">Live Telemetry Synchronized</span>
        </div>

        {isLoading ? (
          <div className="p-12 text-center text-xs font-mono text-slate-500">
            Loading missions from cluster...
          </div>
        ) : missions.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <AlertCircle className="w-8 h-8 text-slate-600 mx-auto" />
            <div className="text-sm font-mono text-slate-400 font-medium">No missions initialized yet.</div>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Start by formulating a new mission objective to trigger autonomous planning and DAG execution.
            </p>
            <Link
              href="/missions/new"
              className="inline-flex items-center gap-1 text-xs font-mono text-cyan-400 hover:text-cyan-300 font-semibold"
            >
              <span>Initialize First Mission</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="px-5 py-3">Mission Title</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Budget Spent</th>
                  <th className="px-5 py-3">DAG Tasks</th>
                  <th className="px-5 py-3">Created</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {missions.map((m) => (
                  <tr key={m.mission_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-5 py-3.5 font-bold text-slate-100 max-w-[280px] truncate">
                      {m.title}
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusBadge status={m.status} />
                    </td>
                    <td className="px-5 py-3.5">
                      ${m.current_usd_spent.toFixed(2)} / ${m.max_usd_limit.toFixed(2)}
                    </td>
                    <td className="px-5 py-3.5">{m.task_count} tasks</td>
                    <td className="px-5 py-3.5 text-slate-400">
                      {new Date(m.created_at).toLocaleTimeString()}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <Link
                        href={`/missions/${m.mission_id}`}
                        className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-semibold hover:underline"
                      >
                        <span>Open Cockpit</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
