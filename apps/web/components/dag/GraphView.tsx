'use client';

import React, { useState } from 'react';
import { WorkflowGraph, GraphNode, TaskItem } from '@/lib/api';
import { StatusBadge } from '@/components/common/StatusBadge';
import { X, Bot } from 'lucide-react';

interface GraphViewProps {
  graph: WorkflowGraph;
  tasks?: TaskItem[];
}

export function GraphView({ graph, tasks = [] }: GraphViewProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const selectedNode = graph.nodes.find((n) => n.id === selectedNodeId);
  const selectedTask = tasks.find((t) => t.task_id === selectedNodeId);

  // Compute simple grid/layer layout coordinates for visual SVG DAG
  const nodeColumns: Record<string, number> = {};
  const inDegree: Record<string, number> = {};

  graph.nodes.forEach((n) => {
    inDegree[n.id] = 0;
  });
  graph.edges.forEach((e) => {
    inDegree[e.target] = (inDegree[e.target] || 0) + 1;
  });

  // Layer assignment
  const roots = graph.nodes.filter((n) => inDegree[n.id] === 0);
  roots.forEach((r) => {
    nodeColumns[r.id] = 0;
  });

  graph.edges.forEach((e) => {
    const srcCol = nodeColumns[e.source] || 0;
    nodeColumns[e.target] = Math.max(nodeColumns[e.target] || 0, srcCol + 1);
  });

  const columnsMap: Record<number, GraphNode[]> = {};
  graph.nodes.forEach((n) => {
    const col = nodeColumns[n.id] || 0;
    if (!columnsMap[col]) columnsMap[col] = [];
    columnsMap[col]?.push(n);
  });

  const colKeys = Object.keys(columnsMap)
    .map(Number)
    .sort((a, b) => a - b);

  return (
    <div className="relative bg-slate-900/60 border border-slate-800 rounded-xl p-6 min-h-[480px] overflow-x-auto flex items-start gap-8">
      {/* DAG Column Layers */}
      {colKeys.length === 0 ? (
        <div className="w-full text-center py-20 text-slate-500 font-mono text-xs">
          No tasks found in mission DAG.
        </div>
      ) : (
        colKeys.map((colIdx) => {
          const colNodes = columnsMap[colIdx] || [];
          return (
            <div key={colIdx} className="flex flex-col gap-4 min-w-[240px]">
              <div className="text-[10px] font-mono uppercase text-slate-500 font-semibold px-1">
                LAYER {colIdx + 1}
              </div>
              {colNodes.map((node) => {
                const isSelected = node.id === selectedNodeId;
                return (
                  <div
                    key={node.id}
                    onClick={() => setSelectedNodeId(node.id)}
                    className={`cursor-pointer bg-slate-900 border rounded-lg p-3.5 transition-all hover:border-cyan-500/80 ${
                      isSelected
                        ? 'border-cyan-400 ring-1 ring-cyan-400/50 bg-slate-800/90 shadow-lg shadow-cyan-950/40'
                        : 'border-slate-800'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <span className="text-xs font-mono font-bold text-slate-200 truncate">
                        {node.name}
                      </span>
                      <StatusBadge status={node.status} />
                    </div>
                    <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                      <div className="flex items-center gap-1">
                        <Bot className="w-3 h-3 text-cyan-400" />
                        <span>{node.agent_role}</span>
                      </div>
                      {node.retry_count > 0 && (
                        <span className="text-amber-400">Retries: {node.retry_count}</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          );
        })
      )}

      {/* Selected Task Inspector Drawer */}
      {selectedNode && (
        <div className="absolute top-4 right-4 w-80 bg-slate-950 border border-slate-700 rounded-xl p-5 shadow-2xl z-20 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <div className="text-[10px] font-mono uppercase text-cyan-400">TASK INSPECTOR</div>
              <div className="text-sm font-bold text-slate-100">{selectedNode.name}</div>
            </div>
            <button
              onClick={() => setSelectedNodeId(null)}
              className="text-slate-400 hover:text-slate-200"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-2.5 text-xs font-mono">
            <div>
              <span className="text-slate-500">Task ID:</span>{' '}
              <span className="text-slate-300">{selectedNode.id}</span>
            </div>
            <div>
              <span className="text-slate-500">Status:</span>{' '}
              <StatusBadge status={selectedNode.status} />
            </div>
            <div>
              <span className="text-slate-500">Assigned Agent:</span>{' '}
              <span className="text-cyan-400">{selectedNode.agent_role}</span>
            </div>
            {selectedTask && (
              <>
                <div>
                  <span className="text-slate-500">Description:</span>
                  <div className="text-slate-300 text-[11px] mt-1 p-2 bg-slate-900 rounded border border-slate-800">
                    {selectedTask.description}
                  </div>
                </div>
                <div>
                  <span className="text-slate-500">Dependencies:</span>{' '}
                  <span className="text-slate-300">
                    {selectedTask.dependencies.length > 0
                      ? selectedTask.dependencies.join(', ')
                      : 'None (Root Node)'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">Allocated Tokens:</span>{' '}
                  <span className="text-slate-300">
                    {selectedTask.allocated_tokens.toLocaleString()}
                  </span>
                </div>
                {selectedTask.evidence_uri && (
                  <div>
                    <span className="text-slate-500">Evidence Proof:</span>
                    <div className="text-emerald-400 truncate text-[11px] mt-0.5">
                      {selectedTask.evidence_uri}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
