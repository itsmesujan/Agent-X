'use client';

import React, { useEffect, useState, use } from 'react';
import { api, ResourceMonitorResponse, ResourceMetricTuple } from '@/lib/api';
import {
  Cpu,
  DollarSign,
  Clock,
  Radio,
  Bot,
  Wrench,
  TrendingUp,
  RefreshCw,
  PlusCircle,
  HelpCircle,
  CheckCircle2,
  X,
} from 'lucide-react';

export default function MissionResourcesPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const missionId = resolvedParams.id;

  const [monitor, setMonitor] = useState<ResourceMonitorResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isReallocating, setIsReallocating] = useState(false);

  // Manual reallocation form modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [reallocDimension, setReallocDimension] = useState('budget');
  const [reallocTarget, setReallocTarget] = useState('verification_task_001');
  const [reallocAmount, setReallocAmount] = useState(0.5);
  const [reallocUnit, setReallocUnit] = useState('USD');
  const [reallocReason, setReallocReason] = useState(
    'Verification received additional resources because conflicting evidence increased mission risk.'
  );
  const [reallocSuccess, setReallocSuccess] = useState<string | null>(null);

  const fetchMonitor = async () => {
    try {
      const data = await api.getResourceMonitor(missionId);
      setMonitor(data);
    } catch {
      // fallback or error
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMonitor();
    const interval = setInterval(fetchMonitor, 3000);
    return () => clearInterval(interval);
  }, [missionId]);

  const handleManualReallocate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsReallocating(true);
    setReallocSuccess(null);
    try {
      await api.reallocateResource(missionId, {
        dimension: reallocDimension,
        to_target: reallocTarget,
        amount: reallocAmount,
        unit: reallocUnit,
        reason: reallocReason,
      });
      setReallocSuccess('Resource reallocated and causal explanation broadcasted.');
      await fetchMonitor();
      setTimeout(() => {
        setIsModalOpen(false);
        setReallocSuccess(null);
      }, 1500);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Reallocation failed.');
    } finally {
      setIsReallocating(false);
    }
  };

  if (isLoading || !monitor) {
    return (
      <div className="p-12 text-center text-xs font-mono text-slate-500">
        Loading Resource Monitor multi-dimensional state...
      </div>
    );
  }

  const dimensionConfigs = [
    {
      key: 'budget',
      label: 'Financial Budget',
      icon: DollarSign,
      color: 'text-emerald-400',
      border: 'border-emerald-500/30',
      format: (val: number) => `$${val.toFixed(2)}`,
      desc: 'USD financial ceiling and cost accounting',
    },
    {
      key: 'time',
      label: 'Execution Time',
      icon: Clock,
      color: 'text-blue-400',
      border: 'border-blue-500/30',
      format: (val: number) => `${Math.round(val)}s`,
      desc: 'SLA target duration and timeout meters',
    },
    {
      key: 'compute',
      label: 'Compute Capacity',
      icon: Cpu,
      color: 'text-cyan-400',
      border: 'border-cyan-500/30',
      format: (val: number) => `${Math.round(val)} slots`,
      desc: 'Parallel DAG worker concurrency threads',
    },
    {
      key: 'api_usage',
      label: 'API / Token Volume',
      icon: Radio,
      color: 'text-purple-400',
      border: 'border-purple-500/30',
      format: (val: number) => `${val.toLocaleString()} tok`,
      desc: 'Model tokens and rate quota throughput',
    },
    {
      key: 'agent_capacity',
      label: 'Agent Capacity',
      icon: Bot,
      color: 'text-amber-400',
      border: 'border-amber-500/30',
      format: (val: number) => `${Math.round(val)} slots`,
      desc: 'Active specialist agent leases across roles',
    },
    {
      key: 'tool_usage',
      label: 'Tool Quota & Locks',
      icon: Wrench,
      color: 'text-rose-400',
      border: 'border-rose-500/30',
      format: (val: number) => `${Math.round(val)} runs`,
      desc: 'Sandboxed tool invocations and mutex locks',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 font-mono tracking-tight flex items-center gap-2">
            <Cpu className="w-5 h-5 text-cyan-400" />
            <span>AGENT-X RESOURCE MONITOR</span>
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Real-time 6-dimensional governance: Allocated, Consumed, Remaining, Reserved with automated causal explanations.
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-1.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 px-3.5 py-1.5 rounded-lg font-bold transition-colors shadow-lg shadow-cyan-500/20"
          >
            <PlusCircle className="w-4 h-4" />
            <span>REALLOCATE RESOURCE</span>
          </button>
          <button
            onClick={fetchMonitor}
            className="text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 p-2 rounded-lg"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 6-Dimensional Resource Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {dimensionConfigs.map((cfg) => {
          const metrics: ResourceMetricTuple = monitor.dimensions[cfg.key] || {
            allocated: 0,
            consumed: 0,
            remaining: 0,
            reserved: 0,
            unit: '',
          };

          const Icon = cfg.icon;
          const consumedPct = Math.min(
            100,
            Math.round((metrics.consumed / (metrics.allocated || 1)) * 100)
          );
          const reservedPct = Math.min(
            100,
            Math.round((metrics.reserved / (metrics.allocated || 1)) * 100)
          );

          return (
            <div
              key={cfg.key}
              className={`bg-slate-900 border ${cfg.border} rounded-xl p-5 shadow-xl space-y-4 font-mono text-xs flex flex-col justify-between`}
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2 font-bold text-sm text-slate-100">
                    <Icon className={`w-4 h-4 ${cfg.color}`} />
                    <span>{cfg.label}</span>
                  </div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">
                    {metrics.unit}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mb-3">{cfg.desc}</p>

                {/* 4-Metric Grid */}
                <div className="grid grid-cols-2 gap-2.5 p-3 bg-slate-950/80 rounded-lg border border-slate-800/80">
                  <div>
                    <div className="text-[10px] uppercase text-slate-500">Allocated</div>
                    <div className="text-sm font-bold text-slate-100 mt-0.5">
                      {cfg.format(metrics.allocated)}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase text-emerald-400">Consumed</div>
                    <div className="text-sm font-bold text-emerald-400 mt-0.5">
                      {cfg.format(metrics.consumed)}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase text-cyan-400">Remaining</div>
                    <div className="text-sm font-bold text-cyan-300 mt-0.5">
                      {cfg.format(metrics.remaining)}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase text-amber-400">Reserved</div>
                    <div className="text-sm font-bold text-amber-400 mt-0.5">
                      {cfg.format(metrics.reserved)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Segmented Progress Bar */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-[10px] text-slate-400">
                  <span>Usage Breakdown</span>
                  <span>
                    {consumedPct}% used | {reservedPct}% held
                  </span>
                </div>
                <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden flex border border-slate-800">
                  <div
                    className="bg-emerald-500 h-full transition-all duration-300"
                    style={{ width: `${consumedPct}%` }}
                    title={`Consumed: ${consumedPct}%`}
                  />
                  <div
                    className="bg-amber-400 h-full transition-all duration-300"
                    style={{ width: `${reservedPct}%` }}
                    title={`Reserved: ${reservedPct}%`}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Reallocation History & Causal "WHY" Timeline */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl font-mono text-xs">
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-100 uppercase tracking-wider">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            <span>DYNAMIC ALLOCATION AUDIT LOG & CAUSAL EXPLANATIONS ("WHY")</span>
          </div>
          <span className="text-[11px] text-slate-500">
            {monitor.reallocation_history.length} events logged
          </span>
        </div>

        {monitor.reallocation_history.length === 0 ? (
          <div className="p-12 text-center text-slate-500 space-y-2">
            <HelpCircle className="w-8 h-8 text-slate-600 mx-auto" />
            <div className="text-sm font-medium text-slate-400">
              Zero allocation shifts recorded yet.
            </div>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              As tasks are dispatched, risk scores elevate, or dynamic DAG mutations trigger, explicit causal rationales will appear here in real-time.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60">
            {monitor.reallocation_history
              .slice()
              .reverse()
              .map((item) => (
                <div
                  key={item.change_id}
                  className="p-4 hover:bg-slate-800/30 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-500/30 text-[10px] font-bold">
                        {item.trigger_type}
                      </span>
                      <span className="text-[11px] text-slate-400 uppercase">
                        Dimension: <strong className="text-slate-200">{item.dimension}</strong>
                      </span>
                      <span className="text-[11px] text-slate-400">
                        &rarr; Target: <strong className="text-cyan-300">{item.target_name}</strong>
                      </span>
                    </div>

                    {/* Prominent Causal Reason Callout */}
                    <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-slate-200 text-xs font-semibold leading-relaxed">
                      &ldquo;{item.reason}&rdquo;
                    </div>
                  </div>

                  <div className="text-right shrink-0 font-mono">
                    <div className="text-sm font-bold text-emerald-400">
                      +{item.delta.toLocaleString()} {item.unit}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-0.5">
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>

      {/* Manual Reallocation Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-lg w-full shadow-2xl font-mono text-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="font-bold text-sm text-slate-100 flex items-center gap-2">
                <PlusCircle className="w-4 h-4 text-cyan-400" />
                <span>MANUAL RESOURCE REALLOCATION</span>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {reallocSuccess && (
              <div className="p-3 bg-emerald-950 border border-emerald-800 rounded-lg text-emerald-300 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>{reallocSuccess}</span>
              </div>
            )}

            <form onSubmit={handleManualReallocate} className="space-y-3.5">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Resource Dimension</label>
                <select
                  value={reallocDimension}
                  onChange={(e) => {
                    const dim = e.target.value;
                    setReallocDimension(dim);
                    if (dim === 'budget') setReallocUnit('USD');
                    else if (dim === 'time') setReallocUnit('seconds');
                    else if (dim === 'compute' || dim === 'agent_capacity') setReallocUnit('slots');
                    else if (dim === 'api_usage') setReallocUnit('tokens');
                    else if (dim === 'tool_usage') setReallocUnit('runs');
                  }}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500"
                >
                  <option value="budget">Budget (USD)</option>
                  <option value="compute">Compute Capacity (Worker Slots)</option>
                  <option value="api_usage">API Usage (Model Tokens)</option>
                  <option value="agent_capacity">Agent Capacity (Role Leases)</option>
                  <option value="time">Time (SLA Timeout Seconds)</option>
                  <option value="tool_usage">Tool Usage (Runs Quota)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Target Node / Agent</label>
                <input
                  type="text"
                  required
                  value={reallocTarget}
                  onChange={(e) => setReallocTarget(e.target.value)}
                  placeholder="e.g. task_verify_evidence_001"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Delta Amount</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    required
                    value={reallocAmount}
                    onChange={(e) => setReallocAmount(parseFloat(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Unit</label>
                  <input
                    type="text"
                    readOnly
                    value={reallocUnit}
                    className="w-full bg-slate-950/60 border border-slate-800 rounded-lg px-3 py-2 text-slate-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Causal Justification Rationale (WHY)
                </label>
                <textarea
                  required
                  rows={3}
                  value={reallocReason}
                  onChange={(e) => setReallocReason(e.target.value)}
                  placeholder="State why this reallocation is necessary..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-100 focus:outline-none focus:border-cyan-500 resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg text-slate-400 hover:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isReallocating}
                  className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 px-5 py-2 rounded-lg font-bold transition-colors shadow-lg shadow-cyan-500/20"
                >
                  {isReallocating ? 'Applying...' : 'Authorize Reallocation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
