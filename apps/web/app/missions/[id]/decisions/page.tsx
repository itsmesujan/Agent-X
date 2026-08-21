'use client';

import React, { useEffect, useState, use } from 'react';
import { api } from '@/lib/api';
import { useMission } from '@/lib/context';
import { HelpCircle, Check, X, ShieldAlert, CheckCircle2, MessageSquare } from 'lucide-react';

interface ApprovalItem {
  approval_id: string;
  mission_id: string;
  task_id: string;
  reason: string;
  details: Record<string, unknown>;
  status: string;
}

export default function MissionDecisionsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const missionId = resolvedParams.id;
  const { refreshActiveMission } = useMission();

  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [decisionNotes, setDecisionNotes] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Load approvals from state/events
  const loadApprovals = async () => {
    try {
      const events = await api.getMissionEvents(missionId);
      const hitlEvents = events.filter((e) => e.event_type === 'HITL_ESCALATION');
      const apps: ApprovalItem[] = hitlEvents.map((e) => ({
        approval_id: (e.payload.approval_id as string) || e.event_id,
        mission_id: missionId,
        task_id: (e.payload.task_id as string) || 'task_pending',
        reason: (e.payload.reason as string) || 'Human approval required for high-risk action.',
        details: e.payload,
        status: (e.payload.status as string) || 'PENDING',
      }));
      setApprovals(apps);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    loadApprovals();
    const interval = setInterval(loadApprovals, 3000);
    return () => clearInterval(interval);
  }, [missionId]);

  const handleDecision = async (approvalId: string, action: 'approve' | 'reject') => {
    setIsSubmitting(approvalId);
    setSuccessMsg(null);
    const notes = decisionNotes[approvalId] || (action === 'approve' ? 'Approved by operator' : 'Rejected by operator');

    try {
      if (action === 'approve') {
        await api.approveDecision(approvalId, notes);
        setSuccessMsg(`Approval ${approvalId} granted. Mission execution resumed.`);
      } else {
        await api.rejectDecision(approvalId, notes);
        setSuccessMsg(`Approval ${approvalId} rejected.`);
      }
      await refreshActiveMission();
      await loadApprovals();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to submit decision.');
    } finally {
      setIsSubmitting(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-100 font-mono tracking-tight flex items-center gap-2">
          <HelpCircle className="w-5 h-5 text-cyan-400" />
          <span>HUMAN-IN-THE-LOOP OPERATOR DECISIONS</span>
        </h1>
        <p className="text-xs text-slate-400 font-mono mt-1">
          Review, steer, and authorize privileged operations, cloud mutations, and strategic replanning escalations.
        </p>
      </div>

      {successMsg && (
        <div className="p-3.5 bg-emerald-950/80 border border-emerald-800 rounded-lg flex items-center gap-2 text-emerald-300 text-xs font-mono">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{successMsg}</span>
        </div>
      )}

      {approvals.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center space-y-2 font-mono">
          <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
          <div className="text-sm font-bold text-slate-200">Zero pending operator escalations.</div>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Autonomous subagents are executing within authorized autonomy boundaries.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {approvals.map((app) => (
            <div
              key={app.approval_id}
              className="bg-slate-900 border border-amber-500/30 rounded-xl p-5 shadow-xl space-y-4 font-mono text-xs"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
                    <ShieldAlert className="w-4 h-4" />
                    <span>AUTHORIZATION REQUEST: {app.approval_id}</span>
                  </div>
                  <div className="text-slate-300 mt-1">{app.reason}</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">Task ID: {app.task_id}</div>
                </div>
                <span className="px-2.5 py-1 rounded bg-amber-950 text-amber-400 border border-amber-500/40 text-[10px] font-bold">
                  {app.status}
                </span>
              </div>

              {/* Payload Details */}
              <pre className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-[11px] text-slate-300 overflow-x-auto">
                {JSON.stringify(app.details, null, 2)}
              </pre>

              {/* Operator Notes Input */}
              <div>
                <label className="block text-slate-400 text-[11px] font-semibold mb-1 flex items-center gap-1">
                  <MessageSquare className="w-3 h-3 text-cyan-400" />
                  <span>Operator Feedback / Reason</span>
                </label>
                <input
                  type="text"
                  placeholder="Optional decision justification notes..."
                  value={decisionNotes[app.approval_id] || ''}
                  onChange={(e) =>
                    setDecisionNotes({ ...decisionNotes, [app.approval_id]: e.target.value })
                  }
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-500"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-800">
                <button
                  onClick={() => handleDecision(app.approval_id, 'reject')}
                  disabled={isSubmitting === app.approval_id}
                  className="flex items-center gap-1.5 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 px-4 py-2 rounded-lg font-bold transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                  <span>REJECT</span>
                </button>
                <button
                  onClick={() => handleDecision(app.approval_id, 'approve')}
                  disabled={isSubmitting === app.approval_id}
                  className="flex items-center gap-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-4 py-2 rounded-lg font-bold transition-colors shadow-lg shadow-emerald-500/20"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>APPROVE & RESUME</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
