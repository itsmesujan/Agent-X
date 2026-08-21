'use client';

import React, { useEffect, useState, use } from 'react';
import { api, ResourceSummary } from '@/lib/api';
import { Bot, Wrench } from 'lucide-react';

export default function MissionAgentsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const missionId = resolvedParams.id;

  const [resources, setResources] = useState<ResourceSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchResources = async () => {
    try {
      const data = await api.getMissionResources(missionId);
      setResources(data);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchResources();
    const interval = setInterval(fetchResources, 3000);
    return () => clearInterval(interval);
  }, [missionId]);

  const agentRoster = [
    {
      role: 'COORDINATOR',
      name: 'Coordinator Agent',
      desc: 'Owns mission state machine, goal deconstruction, DAG scheduling, and deliverable certification.',
      capabilities: ['mission-engine', 'resource-brain', 'workflow-engine', 'agent-orchestration'],
    },
    {
      role: 'ARCHITECT',
      name: 'Architect Agent',
      desc: 'Extracts World Model semantic facts, identifies unknowns, and designs module boundaries.',
      capabilities: ['architecture', 'world-model', 'unknowns-engine', 'database'],
    },
    {
      role: 'CODER',
      name: 'Coder Agent',
      desc: 'Executes verified implementation in Python 3.12, TypeScript, Next.js, and Google ADK.',
      capabilities: ['python', 'fastapi', 'nextjs', 'typescript', 'google-adk', 'gemini'],
    },
    {
      role: 'TESTER',
      name: 'Tester Agent',
      desc: 'Constructs automated unit, integration, mock, and benchmark test suites with 85%+ coverage.',
      capabilities: ['testing', 'evaluation', 'pytest', 'vitest'],
    },
    {
      role: 'DEVOPS',
      name: 'DevOps Agent',
      desc: 'Provisions Google Cloud Run v2, Cloud Pub/Sub topics, and Firestore collections via Terraform.',
      capabilities: ['terraform', 'cloud-run', 'pubsub', 'firestore', 'security'],
    },
    {
      role: 'AUDITOR',
      name: 'Auditor Agent',
      desc: 'Enforces the 4-Level Evidence Verification protocol, HMAC signatures, and recovery audits.',
      capabilities: ['evidence', 'verification', 'recovery', 'observability'],
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-100 font-mono tracking-tight flex items-center gap-2">
          <Bot className="w-5 h-5 text-cyan-400" />
          <span>AUTONOMOUS AGENT COLLECTIVE</span>
        </h1>
        <p className="text-xs text-slate-400 font-mono mt-1">
          Specialized Google ADK subagent personas operating under strict capability boundaries with real-time lease tracking.
        </p>
      </div>

      {isLoading ? (
        <div className="p-12 text-center text-xs font-mono text-slate-500">
          Loading subagent roster and lease states...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {agentRoster.map((agent) => {
            const activeLeases = resources?.active_agent_leases[agent.role] || [];
            const isLeased = activeLeases.length > 0;

            return (
              <div
                key={agent.role}
                className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col justify-between space-y-4"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2 font-mono font-bold text-sm text-slate-100">
                      <Bot className="w-4 h-4 text-cyan-400" />
                      <span>{agent.name}</span>
                    </div>
                    <span
                      className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded border ${
                        isLeased
                          ? 'bg-cyan-950 text-cyan-400 border-cyan-500/40 animate-pulse'
                          : 'bg-slate-950 text-slate-400 border-slate-800'
                      }`}
                    >
                      {isLeased ? `ACTIVE LEASE (${activeLeases.length})` : 'IDLE / READY'}
                    </span>
                  </div>
                  <p className="text-xs font-mono text-slate-400 leading-relaxed">{agent.desc}</p>
                </div>

                <div className="space-y-3 pt-3 border-t border-slate-800/80 text-xs font-mono">
                  <div>
                    <div className="text-[10px] uppercase text-slate-500 font-bold mb-1.5 flex items-center gap-1">
                      <Wrench className="w-3 h-3 text-slate-400" />
                      <span>ALLOWED SKILLS</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {agent.capabilities.map((cap) => (
                        <span
                          key={cap}
                          className="bg-slate-950 text-slate-300 border border-slate-800 px-2 py-0.5 rounded text-[10px]"
                        >
                          {cap}
                        </span>
                      ))}
                    </div>
                  </div>

                  {isLeased && (
                    <div className="p-2.5 bg-cyan-950/40 border border-cyan-500/30 rounded text-[11px] text-cyan-300">
                      <span className="font-bold">Claimed Tasks:</span> {activeLeases.join(', ')}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
