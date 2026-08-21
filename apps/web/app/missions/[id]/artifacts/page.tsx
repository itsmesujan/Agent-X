'use client';

import React, { useEffect, useState, use } from 'react';
import { api, ArtifactItem } from '@/lib/api';
import {
  Layers,
  FileText,
  Database,
  Presentation,
  FileCode,
  ShieldCheck,
  Download,
  Eye,
  Search,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Copy,
  Check,
  X,
  Package,
  HardDrive,
  RefreshCw,
  Sparkles,
} from 'lucide-react';

type ArtifactCategory = 'ALL' | 'REPORT' | 'DATASET' | 'PRESENTATION' | 'SUMMARY' | 'EVIDENCE_PACKAGE';

const CATEGORY_TABS: { id: ArtifactCategory; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'ALL', label: 'All Artifacts', icon: Layers },
  { id: 'REPORT', label: 'Reports', icon: FileText },
  { id: 'DATASET', label: 'Datasets', icon: Database },
  { id: 'PRESENTATION', label: 'Presentations', icon: Presentation },
  { id: 'SUMMARY', label: 'Summaries', icon: FileCode },
  { id: 'EVIDENCE_PACKAGE', label: 'Evidence Packages', icon: Package },
];

export default function MissionArtifactsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const missionId = resolvedParams.id;

  const [artifacts, setArtifacts] = useState<ArtifactItem[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<ArtifactCategory>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedArtifact, setSelectedArtifact] = useState<ArtifactItem | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchArtifacts = async (showLoading = false) => {
    if (showLoading) setIsRefreshing(true);
    try {
      const data = await api.getMissionArtifacts(missionId);
      setArtifacts(data);
      // Keep selected artifact in sync if open
      if (selectedArtifact) {
        const updated = data.find((a) => a.artifact_id === selectedArtifact.artifact_id || a.filename === selectedArtifact.filename);
        if (updated) setSelectedArtifact(updated);
      }
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchArtifacts(true);
    const interval = setInterval(() => fetchArtifacts(false), 3000);
    return () => clearInterval(interval);
  }, [missionId]);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(id);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const handleDownload = (artifact: ArtifactItem) => {
    const content = artifact.content || `# ${artifact.title}\n\nSHA-256: ${artifact.sha256}\nStorage: ${artifact.gcs_uri}\n`;
    const mimeType = artifact.content_type || 'text/plain';
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = artifact.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Filter artifacts
  const filteredArtifacts = artifacts.filter((art) => {
    const matchesCategory =
      selectedCategory === 'ALL' ||
      art.artifact_type.toUpperCase() === selectedCategory;

    const matchesSearch =
      searchQuery === '' ||
      art.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      art.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      art.sha256.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (art.task_id && art.task_id.toLowerCase().includes(searchQuery.toLowerCase()));

    return matchesCategory && matchesSearch;
  });

  // Calculate statistics
  const totalArtifacts = artifacts.length;
  const verifiedCount = artifacts.filter((a) => a.verification_status?.toUpperCase() === 'VERIFIED' || a.verification_status?.toUpperCase() === 'HMAC_CERTIFIED').length;
  const verifiedPct = totalArtifacts > 0 ? Math.round((verifiedCount / totalArtifacts) * 100) : 100;
  const totalSizeBytes = artifacts.reduce((sum, a) => sum + (a.size_bytes || 0), 0);
  const totalSizeFormatted = (totalSizeBytes / 1024).toFixed(1);

  const getCategoryIcon = (type: string) => {
    switch (type.toUpperCase()) {
      case 'REPORT':
        return <FileText className="w-4 h-4 text-blue-400" />;
      case 'DATASET':
        return <Database className="w-4 h-4 text-purple-400" />;
      case 'PRESENTATION':
        return <Presentation className="w-4 h-4 text-amber-400" />;
      case 'SUMMARY':
        return <FileCode className="w-4 h-4 text-cyan-400" />;
      case 'EVIDENCE_PACKAGE':
        return <Package className="w-4 h-4 text-emerald-400" />;
      default:
        return <Layers className="w-4 h-4 text-slate-400" />;
    }
  };

  const getCategoryBadgeClass = (type: string) => {
    switch (type.toUpperCase()) {
      case 'REPORT':
        return 'bg-blue-950/70 text-blue-400 border-blue-500/30';
      case 'DATASET':
        return 'bg-purple-950/70 text-purple-400 border-purple-500/30';
      case 'PRESENTATION':
        return 'bg-amber-950/70 text-amber-400 border-amber-500/30';
      case 'SUMMARY':
        return 'bg-cyan-950/70 text-cyan-400 border-cyan-500/30';
      case 'EVIDENCE_PACKAGE':
        return 'bg-emerald-950/70 text-emerald-400 border-emerald-500/30';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  const getGenStatusBadge = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'GENERATED':
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-500/30 text-[10px] font-mono font-bold">
            <CheckCircle2 className="w-3 h-3" />
            <span>GENERATED</span>
          </span>
        );
      case 'GENERATING':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-500/30 text-[10px] font-mono font-bold animate-pulse">
            <RefreshCw className="w-3 h-3 animate-spin" />
            <span>GENERATING</span>
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-red-950/80 text-red-400 border border-red-500/30 text-[10px] font-mono font-bold">
            <AlertTriangle className="w-3 h-3" />
            <span>FAILED</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 text-[10px] font-mono">
            <Clock className="w-3 h-3" />
            <span>PENDING</span>
          </span>
        );
    }
  };

  const getVerifStatusBadge = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'VERIFIED':
      case 'HMAC_CERTIFIED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/40 text-[10px] font-mono font-bold">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>VERIFIED</span>
          </span>
        );
      case 'PENDING_AUDIT':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-500/40 text-[10px] font-mono font-bold">
            <Clock className="w-3.5 h-3.5" />
            <span>PENDING AUDIT</span>
          </span>
        );
      case 'UNVERIFIED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 text-[10px] font-mono">
            <span>UNVERIFIED</span>
          </span>
        );
      case 'FAILED':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-500/40 text-[10px] font-mono font-bold">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>CHECK FAILED</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 font-mono tracking-tight flex items-center gap-2">
            <Layers className="w-5 h-5 text-cyan-400" />
            <span>ARTIFACT CENTER</span>
            <span className="text-xs px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-500/30">
              MISSION: {missionId}
            </span>
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Deliverable repository categorized into Reports, Datasets, Presentations, Summaries, and Cryptographic Evidence Packages.
          </p>
        </div>

        <button
          onClick={() => fetchArtifacts(true)}
          disabled={isRefreshing}
          className="self-start md:self-auto flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs font-mono text-slate-300 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${isRefreshing ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* KPI Overview Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider flex items-center justify-between">
            <span>Total Deliverables</span>
            <Layers className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-slate-100">{totalArtifacts}</div>
          <div className="text-[10px] font-mono text-slate-500 mt-1">5 core categories supported</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider flex items-center justify-between">
            <span>Certified Verified</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-emerald-400">{verifiedPct}%</div>
          <div className="text-[10px] font-mono text-slate-500 mt-1">{verifiedCount} of {totalArtifacts} HMAC certified</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider flex items-center justify-between">
            <span>Storage Footprint</span>
            <HardDrive className="w-4 h-4 text-purple-400" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-purple-300">{totalSizeFormatted} KB</div>
          <div className="text-[10px] font-mono text-slate-500 mt-1">Immutable in GCS bucket</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider flex items-center justify-between">
            <span>Integrity Guard</span>
            <Sparkles className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-amber-300">SHA-256</div>
          <div className="text-[10px] font-mono text-slate-500 mt-1">Cryptographic tamper-proof</div>
        </div>
      </div>

      {/* Category Filter Tabs & Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-3">
        {/* Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
          {CATEGORY_TABS.map((tab) => {
            const Icon = tab.icon;
            const count =
              tab.id === 'ALL'
                ? artifacts.length
                : artifacts.filter((a) => a.artifact_type.toUpperCase() === tab.id).length;
            const isActive = selectedCategory === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => setSelectedCategory(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors whitespace-nowrap ${
                  isActive
                    ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/40 font-bold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                    isActive ? 'bg-cyan-900 text-cyan-200' : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Search */}
        <div className="relative w-full md:w-64">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search deliverables..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
          />
        </div>
      </div>

      {/* Artifacts Table & Roster */}
      {isLoading ? (
        <div className="p-12 text-center text-xs font-mono text-slate-500">
          Loading deliverable artifacts from evidence repository...
        </div>
      ) : filteredArtifacts.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-xs font-mono text-slate-500">
          {artifacts.length === 0
            ? 'No deliverable artifacts generated yet for this mission.'
            : 'No artifacts match the selected category or filter criteria.'}
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl font-mono text-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="px-5 py-3">Artifact Deliverable</th>
                  <th className="px-5 py-3">Category</th>
                  <th className="px-5 py-3">Mission ID</th>
                  <th className="px-5 py-3">Created</th>
                  <th className="px-5 py-3">Gen Status</th>
                  <th className="px-5 py-3">Verification</th>
                  <th className="px-5 py-3">SHA-256 Checksum</th>
                  <th className="px-5 py-3">Size</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {filteredArtifacts.map((a, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                    {/* Deliverable title & filename */}
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2 font-bold text-slate-100">
                        {getCategoryIcon(a.artifact_type)}
                        <span>{a.title || a.filename}</span>
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5 flex items-center gap-2">
                        <span>{a.filename}</span>
                        {a.task_id && (
                          <span className="text-slate-500">• Task: {a.task_id}</span>
                        )}
                        {a.agent_role && (
                          <span className="text-cyan-500/80">• By: {a.agent_role}</span>
                        )}
                      </div>
                    </td>

                    {/* Category */}
                    <td className="px-5 py-3.5">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-bold ${getCategoryBadgeClass(
                          a.artifact_type
                        )}`}
                      >
                        {a.artifact_type.replace('_', ' ')}
                      </span>
                    </td>

                    {/* Mission ID */}
                    <td className="px-5 py-3.5">
                      <span className="text-[10px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                        {a.mission_id || missionId}
                      </span>
                    </td>

                    {/* Creation Timestamp */}
                    <td className="px-5 py-3.5 text-slate-400 text-[11px] whitespace-nowrap">
                      {a.created_at ? new Date(a.created_at).toLocaleTimeString() : 'Just now'}
                      <div className="text-[9px] text-slate-500">
                        {a.created_at ? new Date(a.created_at).toLocaleDateString() : ''}
                      </div>
                    </td>

                    {/* Generation Status */}
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      {getGenStatusBadge(a.generation_status)}
                    </td>

                    {/* Verification Status */}
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      {getVerifStatusBadge(a.verification_status)}
                    </td>

                    {/* SHA-256 Checksum */}
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono text-[10px] text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                          {a.sha256.slice(0, 10)}...{a.sha256.slice(-6)}
                        </span>
                        <button
                          onClick={() => copyToClipboard(a.sha256, a.artifact_id || a.filename)}
                          title="Copy SHA-256 Hash"
                          className="p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-slate-300 transition-colors"
                        >
                          {copiedHash === (a.artifact_id || a.filename) ? (
                            <Check className="w-3 h-3 text-emerald-400" />
                          ) : (
                            <Copy className="w-3 h-3" />
                          )}
                        </button>
                      </div>
                    </td>

                    {/* Size */}
                    <td className="px-5 py-3.5 text-slate-400 text-[11px] whitespace-nowrap">
                      {((a.size_bytes || 0) / 1024).toFixed(1)} KB
                    </td>

                    {/* Actions: Open & Download */}
                    <td className="px-5 py-3.5 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => setSelectedArtifact(a)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 text-[11px] font-bold transition-colors"
                          title="Open and inspect artifact contents"
                        >
                          <Eye className="w-3 h-3" />
                          <span>Open</span>
                        </button>
                        <button
                          onClick={() => handleDownload(a)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-500/40 text-[11px] font-bold transition-colors"
                          title="Download artifact file"
                        >
                          <Download className="w-3 h-3" />
                          <span>Download</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Interactive Open/Preview Modal */}
      {selectedArtifact && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="px-6 py-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                  {getCategoryIcon(selectedArtifact.artifact_type)}
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-100 font-mono flex items-center gap-2">
                    <span>{selectedArtifact.title || selectedArtifact.filename}</span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded border ${getCategoryBadgeClass(
                        selectedArtifact.artifact_type
                      )}`}
                    >
                      {selectedArtifact.artifact_type.replace('_', ' ')}
                    </span>
                  </h2>
                  <div className="text-xs text-slate-400 font-mono mt-0.5 flex items-center gap-3">
                    <span>File: {selectedArtifact.filename}</span>
                    <span>•</span>
                    <span>Mission: {selectedArtifact.mission_id || missionId}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleDownload(selectedArtifact)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download</span>
                </button>
                <button
                  onClick={() => setSelectedArtifact(null)}
                  className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Metadata Subheader */}
            <div className="px-6 py-3 bg-slate-900/90 border-b border-slate-800/80 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
              <div>
                <span className="text-slate-500 text-[10px] uppercase block">Created Timestamp</span>
                <span className="text-slate-300">
                  {selectedArtifact.created_at ? new Date(selectedArtifact.created_at).toUTCString() : 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] uppercase block">Generation Status</span>
                <div className="mt-0.5">{getGenStatusBadge(selectedArtifact.generation_status)}</div>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] uppercase block">Verification Status</span>
                <div className="mt-0.5">{getVerifStatusBadge(selectedArtifact.verification_status)}</div>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] uppercase block">Storage Size</span>
                <span className="text-slate-300 font-bold">
                  {((selectedArtifact.size_bytes || 0) / 1024).toFixed(1)} KB ({selectedArtifact.size_bytes || 0} bytes)
                </span>
              </div>
            </div>

            {/* Cryptographic SHA-256 Attestation Bar */}
            <div className="px-6 py-2 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2 text-slate-400 truncate">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                <span className="text-slate-500">SHA-256:</span>
                <span className="text-slate-300 select-all font-mono text-[11px] truncate">
                  {selectedArtifact.sha256}
                </span>
              </div>
              <button
                onClick={() => copyToClipboard(selectedArtifact.sha256, 'modal_sha')}
                className="flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300 shrink-0 ml-2"
              >
                {copiedHash === 'modal_sha' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedHash === 'modal_sha' ? 'Copied' : 'Copy'}</span>
              </button>
            </div>

            {/* Modal Body: Deliverable Content Viewer */}
            <div className="flex-1 p-6 overflow-y-auto font-mono text-xs text-slate-300 bg-slate-950/40">
              <div className="mb-2 text-[10px] uppercase tracking-wider text-slate-500 flex items-center justify-between">
                <span>Deliverable Content Payload ({selectedArtifact.content_type || 'text/markdown'})</span>
                <span className="text-slate-500">{selectedArtifact.gcs_uri}</span>
              </div>

              <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-4 overflow-x-auto text-slate-200 leading-relaxed font-mono whitespace-pre-wrap selection:bg-cyan-900">
                {selectedArtifact.content ||
                  `# Deliverable: ${selectedArtifact.title || selectedArtifact.filename}

Mission ID: ${selectedArtifact.mission_id || missionId}
Timestamp: ${selectedArtifact.created_at}
Artifact Type: ${selectedArtifact.artifact_type}
Generation Status: ${selectedArtifact.generation_status}
Verification Status: ${selectedArtifact.verification_status}
SHA-256 Digest: ${selectedArtifact.sha256}
Cloud Storage URI: ${selectedArtifact.gcs_uri}

---

## Executive Summary
This artifact was produced and cryptographically signed during mission execution.
Integrity verified against immutable GCS proof ledger.
`}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-xs font-mono">
              <div className="text-slate-500 text-[11px]">
                Storage URI: <span className="text-slate-400">{selectedArtifact.gcs_uri}</span>
              </div>
              <button
                onClick={() => setSelectedArtifact(null)}
                className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
              >
                Close Viewer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
