'use client';

import React, { useEffect, useState, use } from 'react';
import { api, FailureCenterResponse, FailureRecord } from '@/lib/api';
import { MetricCard } from '@/components/common/MetricCard';
import {
  AlertTriangle,
  ShieldAlert,
  Wrench,
  RefreshCw,
  CheckCircle2,
  Clock,
  Cpu,
  UserCheck,
  FileCode,
  ShieldCheck,
  Activity,
} from 'lucide-react';

export default function MissionFailuresPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const missionId = resolvedParams.id;

  const [data, setData] = useState<FailureCenterResponse | null>(null);
  const [selectedFailure, setSelectedFailure] = useState<FailureRecord | null>(null);
  const [activeTab, setActiveTab] = useState<'COCKPIT' | 'TIMELINE' | 'SPLIT'>('SPLIT');
  const [timelineFilter, setTimelineFilter] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = async () => {
    try {
      const resp = await api.getMissionFailures(missionId);
      setData(resp);
      if (resp.failures.length > 0 && !selectedFailure) {
        setSelectedFailure(resp.failures[0] ?? null);
      }
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [missionId]);

  if (isLoading || !data) {
    return (
      <div className="p-12 text-center text-xs font-mono text-slate-500">
        Loading Agent-X Failure Center & Mission Timeline...
      </div>
    );
  }

  const getClassificationBadge = (cat: string) => {
    switch (cat.toUpperCase()) {
      case 'TRANSIENT':
        return 'bg-blue-950 text-blue-400 border-blue-500/40';
      case 'TOOL':
        return 'bg-amber-950 text-amber-400 border-amber-500/40';
      case 'DATA':
        return 'bg-purple-950 text-purple-400 border-purple-500/40';
      case 'RESOURCE':
        return 'bg-cyan-950 text-cyan-400 border-cyan-500/40';
      case 'PERMISSION':
        return 'bg-rose-950 text-rose-400 border-rose-500/40';
      case 'LOGIC':
        return 'bg-red-950 text-red-400 border-red-500/40';
      case 'MODEL':
        return 'bg-indigo-950 text-indigo-400 border-indigo-500/40';
      case 'ENVIRONMENT':
        return 'bg-orange-950 text-orange-400 border-orange-500/40';
      default:
        return 'bg-slate-900 text-slate-400 border-slate-700';
    }
  };

  const getResultBadge = (res: string) => {
    switch (res.toUpperCase()) {
      case 'RECOVERED':
        return 'bg-emerald-950 text-emerald-400 border-emerald-500/40';
      case 'APPLIED':
        return 'bg-cyan-950 text-cyan-400 border-cyan-500/40';
      case 'ESCALATED_HITL':
        return 'bg-amber-950 text-amber-400 border-amber-500/40';
      case 'FAILED':
        return 'bg-rose-950 text-rose-400 border-rose-500/40';
      default:
        return 'bg-slate-900 text-slate-400 border-slate-700';
    }
  };

  const getTimelineCategoryIcon = (category: string) => {
    switch (category) {
      case 'FAILURE':
        return <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />;
      case 'RECOVERY':
        return <Wrench className="w-3.5 h-3.5 text-emerald-400" />;
      case 'RESOURCE':
        return <Cpu className="w-3.5 h-3.5 text-cyan-400" />;
      case 'DRIFT':
        return <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />;
      case 'EVIDENCE':
        return <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />;
      case 'APPROVAL':
        return <UserCheck className="w-3.5 h-3.5 text-amber-400" />;
      default:
        return <Activity className="w-3.5 h-3.5 text-blue-400" />;
    }
  };

  const filteredTimeline = data.timeline.filter((evt) => {
    if (timelineFilter === 'ALL') return true;
    if (timelineFilter === 'FAILURES') return evt.category === 'FAILURE' || evt.category === 'RECOVERY';
    if (timelineFilter === 'TASKS') return evt.category === 'TASK';
    if (timelineFilter === 'RESOURCES') return evt.category === 'RESOURCE';
    return evt.category === timelineFilter;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 font-mono tracking-tight flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <span>AGENT-X FAILURE CENTER & MISSION TIMELINE</span>
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Real-time diagnostic classification, automated self-healing recoveries, replacement tracking, and chronological timeline.
          </p>
        </div>

        {/* View Mode Buttons */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <button
            onClick={() => setActiveTab('SPLIT')}
            className={`px-3 py-1.5 rounded-lg border transition-colors ${
              activeTab === 'SPLIT'
                ? 'bg-cyan-950 border-cyan-500/80 text-cyan-300'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            SPLIT VIEW
          </button>
          <button
            onClick={() => setActiveTab('COCKPIT')}
            className={`px-3 py-1.5 rounded-lg border transition-colors ${
              activeTab === 'COCKPIT'
                ? 'bg-cyan-950 border-cyan-500/80 text-cyan-300'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            FAILURES ROSTER
          </button>
          <button
            onClick={() => setActiveTab('TIMELINE')}
            className={`px-3 py-1.5 rounded-lg border transition-colors ${
              activeTab === 'TIMELINE'
                ? 'bg-cyan-950 border-cyan-500/80 text-cyan-300'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            TIMELINE FEED
          </button>
          <button
            onClick={fetchData}
            className="flex items-center gap-1 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-slate-400 hover:text-slate-200"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>REFRESH</span>
          </button>
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 font-mono">
        <MetricCard
          label="Diagnosed Failures"
          value={data.summary.total_failures}
          subValue="Classified by Recovery Engine"
          icon={<ShieldAlert className="w-4 h-4 text-rose-400" />}
        />
        <MetricCard
          label="Self-Healing Recoveries"
          value={data.summary.healed_count}
          subValue="Automated strategy executions"
          icon={<Wrench className="w-4 h-4 text-emerald-400" />}
        />
        <MetricCard
          label="HITL Escalations"
          value={data.summary.escalated_hitl_count}
          subValue="Operator decisions required"
          icon={<UserCheck className="w-4 h-4 text-amber-400" />}
        />
        <MetricCard
          label="Recovery Success Rate"
          value={`${data.summary.recovery_rate}%`}
          subValue="Automated self-healing rate"
          icon={<CheckCircle2 className="w-4 h-4 text-cyan-400" />}
        />
      </div>

      {/* Failure Center Cockpit Content */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start font-mono text-xs">
        {/* Failures Roster Column */}
        {(activeTab === 'COCKPIT' || activeTab === 'SPLIT') && (
          <div
            className={`${
              activeTab === 'SPLIT' ? 'lg:col-span-7' : 'lg:col-span-12'
            } space-y-4`}
          >
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="font-bold text-slate-200 uppercase tracking-wider text-xs flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                  <span>DIAGNOSED FAILURES & RECOVERIES ({data.failures.length})</span>
                </span>
                <span className="text-[10px] text-slate-500">
                  Select row to inspect diagnosis & stack trace
                </span>
              </div>

              {data.failures.length === 0 ? (
                <div className="p-8 text-center text-slate-500 flex items-center justify-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Zero runtime failures detected in this mission execution.</span>
                </div>
              ) : (
                <div className="space-y-3">
                  {data.failures.map((f) => {
                    const isSelected = f.failure_id === selectedFailure?.failure_id;

                    return (
                      <div
                        key={f.failure_id}
                        onClick={() => setSelectedFailure(f)}
                        className={`cursor-pointer p-4 rounded-xl border transition-all ${
                          isSelected
                            ? 'bg-slate-950 border-cyan-500/80 shadow-lg shadow-cyan-950/40 ring-1 ring-cyan-500/40'
                            : 'bg-slate-950/70 border-slate-800 hover:border-slate-700 hover:bg-slate-900/60'
                        }`}
                      >
                        {/* Row Header: Classification, Task, Result */}
                        <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                          <div className="flex items-center gap-2">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getClassificationBadge(
                                f.classification
                              )}`}
                            >
                              {f.classification}
                            </span>
                            <span className="text-slate-400 font-semibold">
                              Task: <strong className="text-slate-200">{f.affected_task_name}</strong> ({f.affected_task_id})
                            </span>
                            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-400">
                              {f.assigned_agent}
                            </span>
                          </div>

                          <div className="flex items-center gap-2">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getResultBadge(
                                f.result
                              )}`}
                            >
                              {f.result}
                            </span>
                          </div>
                        </div>

                        {/* Error Proposition / Failure */}
                        <div className="text-rose-300 font-bold text-xs mb-3 bg-rose-950/30 p-2.5 rounded border border-rose-950/60">
                          {f.failure}
                        </div>

                        {/* 7 Required Attributes Grid */}
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 p-3 bg-slate-900/90 rounded-lg border border-slate-800/80 text-[11px]">
                          <div>
                            <span className="text-slate-500 block text-[10px] uppercase font-semibold">
                              Recovery Strategy
                            </span>
                            <span className="text-cyan-400 font-bold flex items-center gap-1 mt-0.5">
                              <Wrench className="w-3 h-3" />
                              <span>{f.recovery_strategy}</span>
                            </span>
                          </div>

                          <div>
                            <span className="text-slate-500 block text-[10px] uppercase font-semibold">
                              Replacement Action
                            </span>
                            <span className="text-slate-200 font-medium mt-0.5 block truncate">
                              {f.replacement}
                            </span>
                          </div>

                          <div>
                            <span className="text-slate-500 block text-[10px] uppercase font-semibold">
                              Additional Resources
                            </span>
                            <span className="text-emerald-400 font-bold mt-0.5 block">
                              {f.additional_resources}
                            </span>
                          </div>
                        </div>

                        {/* Retry & Timing Footer */}
                        <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-900 text-[10px] text-slate-500">
                          <div>
                            Retries:{' '}
                            <span className="text-slate-300 font-bold">
                              {f.retry_count} / {f.max_retries}
                            </span>
                          </div>
                          <div>{new Date(f.timestamp).toLocaleTimeString()}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Selected Failure Detailed Inspector Drawer */}
            {selectedFailure && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                    <FileCode className="w-4 h-4" />
                    <span>DIAGNOSTIC DETAILS & CAUSAL REASONING: {selectedFailure.failure_id}</span>
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getResultBadge(
                      selectedFailure.result
                    )}`}
                  >
                    {selectedFailure.result}
                  </span>
                </div>

                <div className="space-y-2">
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">
                    Automated Self-Healing Rationale
                  </div>
                  <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-slate-200 text-xs leading-relaxed">
                    {selectedFailure.diagnostic_reasoning}
                  </div>
                </div>

                {selectedFailure.stack_trace && (
                  <div className="space-y-2">
                    <div className="text-[10px] text-slate-500 uppercase font-semibold">
                      Diagnostic Stack Trace
                    </div>
                    <pre className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-slate-300 font-mono text-[10px] overflow-x-auto max-h-48">
                      {selectedFailure.stack_trace}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Mission Timeline Column */}
        {(activeTab === 'TIMELINE' || activeTab === 'SPLIT') && (
          <div
            className={`${
              activeTab === 'SPLIT' ? 'lg:col-span-5' : 'lg:col-span-12'
            } bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4`}
          >
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Clock className="w-4 h-4 text-cyan-400" />
                <span>MISSION TIMELINE ({filteredTimeline.length})</span>
              </div>

              {/* Filter */}
              <select
                value={timelineFilter}
                onChange={(e) => setTimelineFilter(e.target.value)}
                className="bg-slate-950 border border-slate-800 text-slate-300 rounded px-2 py-1 text-[10px] focus:outline-none focus:border-cyan-500"
              >
                <option value="ALL">ALL EVENTS</option>
                <option value="FAILURES">FAILURES & RECOVERIES</option>
                <option value="TASKS">TASK EVENTS</option>
                <option value="RESOURCES">RESOURCES</option>
                <option value="EVIDENCE">EVIDENCE</option>
                <option value="DRIFT">GOAL DRIFT</option>
              </select>
            </div>

            {/* Vertical Chronological Timeline Feed */}
            <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800 max-h-[720px] overflow-y-auto pr-1">
              {filteredTimeline.length === 0 ? (
                <div className="p-8 text-center text-slate-500">No timeline events recorded.</div>
              ) : (
                filteredTimeline.map((evt) => {
                  return (
                    <div key={evt.event_id} className="relative group">
                      {/* Timeline Dot */}
                      <div className="absolute -left-[23px] top-1 w-5 h-5 rounded-full bg-slate-950 border border-slate-700 flex items-center justify-center group-hover:border-cyan-400 transition-colors">
                        {getTimelineCategoryIcon(evt.category)}
                      </div>

                      {/* Event Card */}
                      <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/90 group-hover:border-slate-700 transition-colors space-y-1.5">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-bold text-slate-200 text-[11px]">
                            {evt.title}
                          </span>
                          <span className="text-[10px] text-slate-500">
                            {new Date(evt.timestamp).toLocaleTimeString()}
                          </span>
                        </div>

                        <p className="text-slate-300 text-[11px] leading-relaxed">
                          {evt.description}
                        </p>

                        <div className="flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-500 pt-1 border-t border-slate-900">
                          <span className="px-1.5 py-0.5 rounded bg-slate-900 text-slate-400 font-bold">
                            {evt.category}
                          </span>
                          {evt.task_id && (
                            <span className="text-cyan-400 font-mono">Task: {evt.task_id}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
