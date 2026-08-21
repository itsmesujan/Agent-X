'use client';

import React, { useEffect, useState, use } from 'react';
import { api, MissionDetail, KernelEventItem } from '@/lib/api';
import { useMission } from '@/lib/context';
import { StatusBadge } from '@/components/common/StatusBadge';
import { MetricCard } from '@/components/common/MetricCard';
import {
  Play,
  Pause,
  RotateCcw,
  XCircle,
  Cpu,
  Clock,
  CheckCircle,
  FileText,
  Radio,
} from 'lucide-react';

export default function MissionOverviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const missionId = resolvedParams.id;
  const { selectMission, refreshMissions } = useMission();

  const [mission, setMission] = useState<MissionDetail | null>(null);
  const [events, setEvents] = useState<KernelEventItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isMutating, setIsMutating] = useState(false);

  const fetchDetails = async () => {
    try {
      const [detail, evts] = await Promise.all([
        api.getMission(missionId),
        api.getMissionEvents(missionId),
      ]);
      setMission(detail);
      setEvents(evts);
      selectMission(missionId);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
    const interval = setInterval(fetchDetails, 3000);
    return () => clearInterval(interval);
  }, [missionId]);

  const handleAction = async (action: 'start' | 'pause' | 'resume' | 'cancel') => {
    setIsMutating(true);
    try {
      if (action === 'start') await api.startMission(missionId);
      if (action === 'pause') await api.pauseMission(missionId);
      if (action === 'resume') await api.resumeMission(missionId);
      if (action === 'cancel') await api.cancelMission(missionId);
      await fetchDetails();
      await refreshMissions();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Action failed.');
    } finally {
      setIsMutating(false);
    }
  };

  if (isLoading || !mission) {
    return (
      <div className="p-12 text-center text-xs font-mono text-slate-500">
        Loading mission cockpit state...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold text-slate-100 font-mono tracking-tight">
              {mission.title}
            </h1>
            <StatusBadge status={mission.status} />
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1 max-w-3xl">
            {mission.goal_statement}
          </p>
        </div>

        {/* Execution Control Actions */}
        <div className="flex items-center gap-2 shrink-0 font-mono text-xs">
          {mission.status === 'READY' && (
            <button
              onClick={() => handleAction('start')}
              disabled={isMutating}
              className="flex items-center gap-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-3.5 py-1.5 rounded-lg font-bold transition-colors"
            >
              <Play className="w-3.5 h-3.5" />
              <span>START</span>
            </button>
          )}

          {mission.status === 'EXECUTING' && (
            <button
              onClick={() => handleAction('pause')}
              disabled={isMutating}
              className="flex items-center gap-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 px-3.5 py-1.5 rounded-lg font-bold transition-colors"
            >
              <Pause className="w-3.5 h-3.5" />
              <span>PAUSE</span>
            </button>
          )}

          {mission.status === 'PAUSED' && (
            <button
              onClick={() => handleAction('resume')}
              disabled={isMutating}
              className="flex items-center gap-1.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 px-3.5 py-1.5 rounded-lg font-bold transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>RESUME</span>
            </button>
          )}

          {['READY', 'EXECUTING', 'PAUSED'].includes(mission.status) && (
            <button
              onClick={() => handleAction('cancel')}
              disabled={isMutating}
              className="flex items-center gap-1.5 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 px-3 py-1.5 rounded-lg font-medium transition-colors"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>CANCEL</span>
            </button>
          )}
        </div>
      </div>

      {/* KPI Metrics Breakdown */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Budget Metering"
          value={`$${mission.budget.current_usd_spent.toFixed(2)}`}
          subValue={`Limit: $${mission.budget.max_usd_limit.toFixed(2)}`}
          icon={<Cpu className="w-4 h-4 text-cyan-400" />}
          trend={`${Math.round(
            (mission.budget.current_usd_spent / (mission.budget.max_usd_limit || 1)) * 100
          )}% spent`}
        />
        <MetricCard
          label="Tokens Consumed"
          value={mission.budget.current_tokens_used.toLocaleString()}
          subValue={`Cap: ${mission.budget.max_total_tokens.toLocaleString()}`}
          icon={<Radio className="w-4 h-4 text-emerald-400" />}
        />
        <MetricCard
          label="Task Progress"
          value={`${mission.summary.verified} / ${mission.summary.total}`}
          subValue={`${mission.summary.running} running | ${mission.summary.failed} failed`}
          icon={<CheckCircle className="w-4 h-4 text-blue-400" />}
        />
        <MetricCard
          label="Target Duration"
          value={`${Math.round(mission.budget.max_execution_time_seconds / 60)} min`}
          subValue={`Created: ${new Date(mission.created_at).toLocaleTimeString()}`}
          icon={<Clock className="w-4 h-4 text-slate-400" />}
        />
      </div>

      {/* Deliverables & Recent Events */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Deliverables */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="text-xs font-mono uppercase text-slate-400 font-bold tracking-wider flex items-center gap-2">
            <FileText className="w-4 h-4 text-cyan-400" />
            <span>EXPECTED DELIVERABLES ({mission.deliverables.length})</span>
          </div>
          <div className="space-y-2">
            {mission.deliverables.map((deliv, idx) => (
              <div
                key={idx}
                className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-xs font-mono text-slate-300 flex items-center justify-between"
              >
                <span className="truncate">{deliv}</span>
                <span className="text-[10px] text-slate-500 font-semibold">REQUIRED</span>
              </div>
            ))}
          </div>
        </div>

        {/* Real-time Event Feed */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between text-xs font-mono uppercase text-slate-400 font-bold tracking-wider">
            <span>REAL-TIME KERNEL EVENTS ({events.length})</span>
            <span className="text-[10px] text-slate-500 font-normal">Streaming Audit Log</span>
          </div>

          <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
            {events.length === 0 ? (
              <div className="text-center py-8 text-xs font-mono text-slate-500">
                No kernel events logged yet.
              </div>
            ) : (
              events
                .slice()
                .reverse()
                .map((e) => (
                  <div
                    key={e.event_id}
                    className="p-2.5 bg-slate-950/80 border border-slate-800/80 rounded-lg text-xs font-mono flex items-start justify-between gap-4"
                  >
                    <div>
                      <div className="text-cyan-400 font-semibold text-[11px]">{e.event_type}</div>
                      <div className="text-slate-400 text-[11px] mt-0.5 truncate max-w-lg">
                        {JSON.stringify(e.payload)}
                      </div>
                    </div>
                    <div className="text-[10px] text-slate-500 shrink-0">
                      {new Date(e.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
