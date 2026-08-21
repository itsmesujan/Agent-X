'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useMission } from '@/lib/context';
import { Shield, Sparkles, AlertCircle, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function NewMissionPage() {
  const router = useRouter();
  const { refreshMissions, selectMission } = useMission();

  const [title, setTitle] = useState('');
  const [goalStatement, setGoalStatement] = useState('');
  const [budgetUsd, setBudgetUsd] = useState(5.0);
  const [runtimeMinutes, setRuntimeMinutes] = useState(60);
  const [deliverables, setDeliverables] = useState('verified_report.md, terraform.tf');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !goalStatement.trim()) {
      setError('Title and Goal Statement are required.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const delivList = deliverables
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);

      const res = await api.createMission({
        title,
        goal_statement: goalStatement,
        max_usd_budget: budgetUsd,
        max_runtime_minutes: runtimeMinutes,
        deliverables: delivList,
      });

      await refreshMissions();
      selectMission(res.mission_id);
      router.push(`/missions/${res.mission_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to initialize mission.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Back Link */}
      <Link
        href="/"
        className="inline-flex items-center gap-1 text-xs font-mono text-slate-400 hover:text-slate-200"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Dashboard</span>
      </Link>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl space-y-6">
        <div>
          <h1 className="text-lg font-bold text-slate-100 font-mono tracking-tight flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-cyan-400" />
            <span>FORMULATE NEW MISSION</span>
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Specify the high-level intent. Agent-X will deconstruct objectives, construct World Model facts, formulate DAG tasks, and allocate compute budgets.
          </p>
        </div>

        {error && (
          <div className="p-3.5 bg-rose-950/80 border border-rose-800 rounded-lg flex items-center gap-2 text-rose-300 text-xs font-mono">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs font-mono">
          <div>
            <label className="block text-slate-300 font-semibold mb-1">Mission Title</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Remediate Cloud Run IAM Violations"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">
              Goal Statement & Objective
            </label>
            <textarea
              required
              rows={4}
              value={goalStatement}
              onChange={(e) => setGoalStatement(e.target.value)}
              placeholder="Describe the end state, required actions, security constraints, and expected outcome..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-500 resize-none"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Max USD Budget ($)</label>
              <input
                type="number"
                step="0.5"
                min="0.5"
                value={budgetUsd}
                onChange={(e) => setBudgetUsd(parseFloat(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-slate-100 focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-semibold mb-1">
                Max Runtime (Minutes)
              </label>
              <input
                type="number"
                min="5"
                max="1440"
                value={runtimeMinutes}
                onChange={(e) => setRuntimeMinutes(parseInt(e.target.value, 10))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-slate-100 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">
              Expected Deliverables (Comma-separated)
            </label>
            <input
              type="text"
              value={deliverables}
              onChange={(e) => setDeliverables(e.target.value)}
              placeholder="verified_outcome.json, terraform.tf"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="pt-4 border-t border-slate-800 flex justify-end">
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-2 bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 px-5 py-2.5 rounded-lg font-bold font-mono transition-colors shadow-lg shadow-cyan-500/20"
            >
              <Shield className="w-4 h-4" />
              <span>{isSubmitting ? 'INITIALIZING MISSION...' : 'LAUNCH MISSION'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
