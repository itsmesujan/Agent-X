'use client';

import React, { useEffect, useState, use } from 'react';
import { api, TaskItem } from '@/lib/api';
import { StatusBadge } from '@/components/common/StatusBadge';
import { CheckSquare, Bot, RefreshCw, FileCheck } from 'lucide-react';

export default function MissionTasksPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const missionId = resolvedParams.id;

  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [filter, setFilter] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState(true);

  const fetchTasks = async () => {
    try {
      const data = await api.getMissionTasks(missionId);
      setTasks(data);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 3000);
    return () => clearInterval(interval);
  }, [missionId]);

  const filteredTasks = tasks.filter((t) => {
    if (filter === 'ALL') return true;
    return t.status.toUpperCase() === filter;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 font-mono tracking-tight flex items-center gap-2">
            <CheckSquare className="w-5 h-5 text-cyan-400" />
            <span>TASK EXECUTION ROSTER ({tasks.length})</span>
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Deterministic state machines, agent assignments, and retry metering per DAG node.
          </p>
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">ALL STATUSES ({tasks.length})</option>
            <option value="RUNNING">RUNNING</option>
            <option value="VERIFIED">VERIFIED</option>
            <option value="FAILED">FAILED</option>
            <option value="PENDING">PENDING</option>
            <option value="READY">READY</option>
            <option value="PAUSED">PAUSED</option>
          </select>
          <button
            onClick={fetchTasks}
            className="text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 p-2 rounded-lg"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="p-12 text-center text-xs font-mono text-slate-500">
          Loading tasks from mission workflow...
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-12 text-center text-xs font-mono text-slate-500">
          No tasks match the selected filter.
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="px-5 py-3">Task Name</th>
                  <th className="px-5 py-3">Agent Role</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Dependencies</th>
                  <th className="px-5 py-3">Tokens</th>
                  <th className="px-5 py-3">Retries</th>
                  <th className="px-5 py-3 text-right">Evidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {filteredTasks.map((t) => (
                  <tr key={t.task_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-5 py-3.5">
                      <div className="font-bold text-slate-100">{t.name}</div>
                      <div className="text-[10px] text-slate-500 mt-0.5 max-w-sm truncate">
                        {t.description}
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-1.5 text-cyan-400">
                        <Bot className="w-3.5 h-3.5" />
                        <span>{t.agent_role}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusBadge status={t.status} />
                    </td>
                    <td className="px-5 py-3.5 text-slate-400">
                      {t.dependencies.length > 0 ? t.dependencies.join(', ') : 'Root (None)'}
                    </td>
                    <td className="px-5 py-3.5">{t.allocated_tokens.toLocaleString()}</td>
                    <td className="px-5 py-3.5">
                      {t.retry_count > 0 ? (
                        <span className="text-amber-400 font-bold">{t.retry_count}</span>
                      ) : (
                        <span className="text-slate-500">0</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      {t.evidence_uri ? (
                        <span className="inline-flex items-center gap-1 text-emerald-400 text-[11px]">
                          <FileCheck className="w-3.5 h-3.5" />
                          <span>Attached</span>
                        </span>
                      ) : (
                        <span className="text-slate-600 text-[11px]">None</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
