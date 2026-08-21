'use client';

import React, { useEffect, useState, use } from 'react';
import { api, WorkflowGraph, TaskItem } from '@/lib/api';
import { GraphView } from '@/components/dag/GraphView';
import { GitBranch, RefreshCw } from 'lucide-react';

export default function MissionGraphPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const missionId = resolvedParams.id;

  const [graph, setGraph] = useState<WorkflowGraph | null>(null);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchGraph = async () => {
    try {
      const [g, t] = await Promise.all([
        api.getMissionGraph(missionId),
        api.getMissionTasks(missionId),
      ]);
      setGraph(g);
      setTasks(t);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph();
    const interval = setInterval(fetchGraph, 3000);
    return () => clearInterval(interval);
  }, [missionId]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100 font-mono tracking-tight flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-cyan-400" />
            <span>INTERACTIVE MISSION DAG GRAPH</span>
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Topological task dependency flow. Click any node to inspect execution inputs, verification status, and evidence.
          </p>
        </div>
        <button
          onClick={fetchGraph}
          className="flex items-center gap-1 text-xs font-mono text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>REFRESH GRAPH</span>
        </button>
      </div>

      {isLoading || !graph ? (
        <div className="p-12 text-center text-xs font-mono text-slate-500">
          Loading DAG graph topology...
        </div>
      ) : (
        <GraphView graph={graph} tasks={tasks} />
      )}
    </div>
  );
}
