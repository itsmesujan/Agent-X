'use client';

import React, { useEffect, useState, use } from 'react';
import { api, EvidenceSummary } from '@/lib/api';
import { StatusBadge } from '@/components/common/StatusBadge';
import { MetricCard } from '@/components/common/MetricCard';
import {
  FileCheck2,
  ShieldCheck,
  Database,
  Link as LinkIcon,
  AlertTriangle,
  FileCode,
  Clock,
  CheckCircle2,
  Search,
} from 'lucide-react';

export default function MissionEvidencePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const missionId = resolvedParams.id;

  const [evidence, setEvidence] = useState<EvidenceSummary | null>(null);
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);

  const fetchEvidence = async () => {
    try {
      const data = await api.getMissionEvidence(missionId);
      setEvidence(data);
      if (data.claims.length > 0 && !selectedClaimId) {
        setSelectedClaimId(data.claims[0]?.claim_id ?? null);
      }
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEvidence();
    const interval = setInterval(fetchEvidence, 3000);
    return () => clearInterval(interval);
  }, [missionId]);

  if (isLoading || !evidence) {
    return (
      <div className="p-12 text-center text-xs font-mono text-slate-500">
        Loading Evidence Explorer empirical proofs...
      </div>
    );
  }

  const filteredClaims = evidence.claims.filter((c) => {
    const matchesSearch =
      c.statement.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.predicate.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || c.status.toUpperCase() === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const selectedClaim =
    evidence.claims.find((c) => c.claim_id === selectedClaimId) ||
    evidence.claims[0] ||
    null;

  const getReliabilityBadge = (rel: string) => {
    switch (rel) {
      case 'AUTHORITATIVE':
        return 'bg-emerald-950 text-emerald-400 border-emerald-500/40';
      case 'PRIMARY_EVIDENCE':
        return 'bg-cyan-950 text-cyan-400 border-cyan-500/40';
      case 'SECONDARY_DOCS':
        return 'bg-blue-950 text-blue-400 border-blue-500/40';
      case 'HEURISTIC_INFERENCE':
        return 'bg-amber-950 text-amber-400 border-amber-500/40';
      default:
        return 'bg-slate-900 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-100 font-mono tracking-tight flex items-center gap-2">
          <FileCheck2 className="w-5 h-5 text-cyan-400" />
          <span>AGENT-X EVIDENCE EXPLORER</span>
        </h1>
        <p className="text-xs text-slate-400 font-mono mt-1">
          Inspect empirical claims, supporting stored evidence artifacts, contradictory sources, timestamps, and causal decision rationales.
        </p>
      </div>

      {/* KPI Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          label="Empirical Claims"
          value={evidence.total_claims}
          subValue="Asserted system facts"
          icon={<Database className="w-4 h-4 text-cyan-400" />}
        />
        <MetricCard
          label="Verified Claims"
          value={evidence.verified_claims}
          subValue={`${Math.round(
            (evidence.verified_claims / (evidence.total_claims || 1)) * 100
          )}% certified`}
          icon={<ShieldCheck className="w-4 h-4 text-emerald-400" />}
        />
        <MetricCard
          label="Detected Contradictions"
          value={evidence.conflicts.length}
          subValue={`${evidence.conflicts.filter((c) => !c.is_resolved).length} unresolved`}
          icon={<AlertTriangle className="w-4 h-4 text-amber-400" />}
        />
      </div>

      {/* Main Evidence Explorer Workspace: Master-Detail Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start font-mono text-xs">
        {/* Left Column: Claims Selection List */}
        <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl space-y-3 p-4">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">
              CLAIMS ROSTER ({filteredClaims.length})
            </span>
            <span className="text-[10px] text-slate-500">Select to inspect</span>
          </div>

          {/* Search and Filters */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search claims by topic..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500 text-[11px]"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-cyan-500 text-[11px]"
            >
              <option value="ALL">ALL</option>
              <option value="VERIFIED">VERIFIED</option>
              <option value="PROPOSED">PROPOSED</option>
              <option value="REFUTED">REFUTED</option>
              <option value="INVALIDATED">INVALIDATED</option>
            </select>
          </div>

          {/* Claims List */}
          <div className="space-y-2 max-h-[560px] overflow-y-auto pr-1">
            {filteredClaims.length === 0 ? (
              <div className="p-8 text-center text-slate-500">No matching claims found.</div>
            ) : (
              filteredClaims.map((claim) => {
                const isSelected = claim.claim_id === selectedClaim?.claim_id;
                const hasConflicts = claim.conflict_ids.length > 0;

                return (
                  <div
                    key={claim.claim_id}
                    onClick={() => setSelectedClaimId(claim.claim_id)}
                    className={`cursor-pointer p-3 rounded-lg border transition-all ${
                      isSelected
                        ? 'bg-slate-800/90 border-cyan-500/80 shadow-lg shadow-cyan-950/40 ring-1 ring-cyan-500/40'
                        : 'bg-slate-950/70 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/60'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <span className="text-[10px] text-cyan-400 font-bold truncate">
                        {claim.subject} &rarr; {claim.predicate}
                      </span>
                      <StatusBadge status={claim.status} />
                    </div>

                    <div className="font-bold text-slate-200 line-clamp-2 leading-relaxed text-[11px]">
                      {claim.statement}
                    </div>

                    <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-800/60 text-[10px] text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <span>Confidence:</span>
                        <span className="font-bold text-cyan-300">
                          {Math.round(claim.confidence * 100)}%
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        {hasConflicts && (
                          <span className="text-amber-400 flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3" />
                            <span>{claim.conflict_ids.length} conflict</span>
                          </span>
                        )}
                        <span className="text-slate-500">
                          {claim.evidence_items.length} proof(s)
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Selected Claim Inspector */}
        <div className="lg:col-span-7 space-y-5">
          {selectedClaim ? (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl space-y-6">
              {/* Claim Header & Proposition */}
              <div className="space-y-3 pb-4 border-b border-slate-800">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-[10px] uppercase text-cyan-400 font-bold tracking-wider">
                    CLAIM INSPECTOR: {selectedClaim.claim_id}
                  </span>
                  <StatusBadge status={selectedClaim.status} />
                </div>

                <h2 className="text-base font-bold text-slate-100 leading-snug">
                  &ldquo;{selectedClaim.statement}&rdquo;
                </h2>

                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex flex-wrap gap-4 text-[11px]">
                  <div>
                    <span className="text-slate-500">Subject:</span>{' '}
                    <span className="text-cyan-400 font-bold">{selectedClaim.subject}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Predicate:</span>{' '}
                    <span className="text-slate-300 font-bold">{selectedClaim.predicate}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Asserted Value:</span>{' '}
                    <span className="text-emerald-400 font-bold">
                      {String(selectedClaim.value)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Confidence & Timestamps Bar */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Confidence Card */}
                <div className="p-4 bg-slate-950/80 rounded-lg border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 font-semibold text-[11px]">
                      CONFIDENCE & CREDIBILITY
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getReliabilityBadge(
                        selectedClaim.source_reliability
                      )}`}
                    >
                      {selectedClaim.source_reliability}
                    </span>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-bold text-cyan-400">
                      {Math.round(selectedClaim.confidence * 100)}%
                    </span>
                    <span className="text-[10px] text-slate-500">Empirical certainty score</span>
                  </div>
                  <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
                    <div
                      className="bg-cyan-400 h-full transition-all duration-500"
                      style={{ width: `${Math.round(selectedClaim.confidence * 100)}%` }}
                    />
                  </div>
                </div>

                {/* Timestamps Card */}
                <div className="p-4 bg-slate-950/80 rounded-lg border border-slate-800 space-y-2 text-[11px]">
                  <div className="text-slate-400 font-semibold flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-blue-400" />
                    <span>TIMESTAMPS & LIFECYCLE</span>
                  </div>
                  <div className="space-y-1 text-slate-300">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Created:</span>
                      <span>{new Date(selectedClaim.created_at).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Updated:</span>
                      <span>{new Date(selectedClaim.updated_at).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Verified:</span>
                      <span>
                        {selectedClaim.verified_at
                          ? new Date(selectedClaim.verified_at).toLocaleString()
                          : 'Pending Verification'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Prominent Reason for Final Decision */}
              <div className="p-4 bg-slate-950 rounded-xl border border-cyan-500/30 space-y-2">
                <div className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-cyan-400" />
                  <span>REASON FOR FINAL DECISION</span>
                </div>
                <p className="text-slate-200 text-xs leading-relaxed font-semibold">
                  {selectedClaim.final_decision_reason}
                </p>
                {selectedClaim.invalidation_reason && (
                  <div className="text-rose-400 text-[11px] mt-1 pt-1 border-t border-rose-950">
                    <strong>Invalidation:</strong> {selectedClaim.invalidation_reason}
                  </div>
                )}
              </div>

              {/* Supporting Sources & Actual Stored Evidence */}
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs font-bold text-slate-200 uppercase tracking-wider">
                  <div className="flex items-center gap-1.5">
                    <FileCode className="w-4 h-4 text-emerald-400" />
                    <span>
                      SUPPORTING SOURCES & STORED EVIDENCE ({selectedClaim.evidence_items.length})
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-normal">
                    Cryptographic Proofs
                  </span>
                </div>

                {/* Primary Origin Source */}
                <div className="p-3 bg-slate-950/90 rounded-lg border border-slate-800 flex items-start justify-between gap-4">
                  <div>
                    <div className="text-[10px] text-slate-500 uppercase font-bold">
                      Primary Source Reference
                    </div>
                    <div className="text-slate-200 font-bold text-xs mt-0.5">
                      {selectedClaim.source_ref}
                    </div>
                    {selectedClaim.content_ref && (
                      <div className="text-[11px] text-slate-400 mt-1 italic">
                        &ldquo;{selectedClaim.content_ref}&rdquo;
                      </div>
                    )}
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getReliabilityBadge(
                      selectedClaim.source_reliability
                    )}`}
                  >
                    {selectedClaim.source_reliability}
                  </span>
                </div>

                {/* Attached Immutable Evidence Items */}
                {selectedClaim.evidence_items.length === 0 ? (
                  <div className="p-4 bg-slate-950/60 rounded-lg border border-slate-800 text-center text-slate-500 text-xs">
                    No additional raw evidence artifacts attached yet.
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    {selectedClaim.evidence_items.map((item) => (
                      <div
                        key={item.evidence_id}
                        className="p-3.5 bg-slate-950 rounded-lg border border-slate-800 space-y-2 hover:border-emerald-500/40 transition-colors"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-2 text-emerald-400 font-bold">
                            <LinkIcon className="w-3.5 h-3.5" />
                            <span className="truncate max-w-sm">{item.source_uri}</span>
                          </div>
                          <span className="text-[10px] text-slate-500 font-mono">
                            {(item.byte_size / 1024).toFixed(1)} KB
                          </span>
                        </div>

                        {/* Content Snippet */}
                        {item.content_ref && (
                          <pre className="p-2.5 bg-slate-900 rounded text-[11px] text-slate-300 font-mono overflow-x-auto border border-slate-800/80">
                            {item.content_ref}
                          </pre>
                        )}

                        <div className="flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-500 pt-1 border-t border-slate-900">
                          <div>
                            SHA-256:{' '}
                            <span className="text-slate-400 font-mono">
                              {item.raw_data_hash.slice(0, 16)}...{item.raw_data_hash.slice(-8)}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            {item.collected_by_agent && (
                              <span>Agent: {item.collected_by_agent}</span>
                            )}
                            <span>{new Date(item.timestamp).toLocaleTimeString()}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Conflicting Sources & Contradictions */}
              <div className="space-y-3 pt-2">
                <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  <span>CONFLICTING SOURCES & CONTRADICTIONS ({selectedClaim.conflicts.length})</span>
                </div>

                {selectedClaim.conflicts.length === 0 ? (
                  <div className="p-4 bg-slate-950/60 rounded-lg border border-slate-800 text-center text-slate-400 flex items-center justify-center gap-2 text-xs">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>Zero contradictions detected. All source corroborations agree.</span>
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    {selectedClaim.conflicts.map((conf) => (
                      <div
                        key={conf.conflict_id}
                        className="p-3.5 bg-slate-950 rounded-lg border border-amber-500/30 space-y-2 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-500/40 text-[10px] font-bold">
                            {conf.severity} CONFLICT
                          </span>
                          <span
                            className={`text-[10px] font-semibold ${
                              conf.is_resolved ? 'text-emerald-400' : 'text-amber-400'
                            }`}
                          >
                            {conf.is_resolved ? 'RESOLVED' : 'UNRESOLVED'}
                          </span>
                        </div>

                        <div className="text-slate-200 font-medium leading-relaxed">
                          {conf.reason}
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-[11px] p-2 bg-slate-900 rounded border border-slate-800">
                          <div>
                            <span className="text-slate-500">Value A ({conf.claim_a_id}):</span>{' '}
                            <span className="text-slate-300 font-bold">{String(conf.value_a)}</span>
                          </div>
                          <div>
                            <span className="text-slate-500">Value B ({conf.claim_b_id}):</span>{' '}
                            <span className="text-slate-300 font-bold">{String(conf.value_b)}</span>
                          </div>
                        </div>

                        {conf.resolution_notes && (
                          <div className="text-[11px] text-emerald-400 pt-1 border-t border-slate-800">
                            <strong>Resolution:</strong> {conf.resolution_notes}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-500">
              Select a claim from the roster to inspect its evidence trace.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
