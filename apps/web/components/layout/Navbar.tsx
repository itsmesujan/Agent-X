'use client';

import React from 'react';
import Link from 'next/link';
import { useMission } from '@/lib/context';
import { Shield, Plus, Activity, RefreshCw } from 'lucide-react';

export function Navbar() {
  const { missions, activeMissionId, selectMission, isLiveConnected, refreshMissions } = useMission();

  return (
    <header className="h-14 bg-slate-950 border-b border-slate-800 px-4 flex items-center justify-between sticky top-0 z-40">
      {/* Brand & Mission Selector */}
      <div className="flex items-center gap-4">
        <Link href="/" className="flex items-center gap-2 font-mono font-bold text-slate-100 tracking-wider">
          <div className="w-7 h-7 rounded bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
            <Shield className="w-4 h-4" />
          </div>
          <span>AGENT-X</span>
          <span className="hidden sm:inline-block text-xs bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded font-normal">
            MISSION CONTROL
          </span>
        </Link>

        {/* Mission Switcher */}
        {missions.length > 0 && (
          <div className="hidden md:flex items-center gap-2 ml-4">
            <span className="text-xs font-mono text-slate-500 uppercase">Mission:</span>
            <select
              value={activeMissionId || ''}
              onChange={(e) => selectMission(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded px-2.5 py-1 font-mono focus:outline-none focus:border-cyan-500 max-w-[240px] truncate"
            >
              {missions.map((m) => (
                <option key={m.mission_id} value={m.mission_id}>
                  {m.title} ({m.status})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* Live Sync Status */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-900 border border-slate-800 rounded text-xs font-mono">
          <span
            className={`w-2 h-2 rounded-full ${
              isLiveConnected ? 'bg-emerald-400 animate-ping' : 'bg-rose-500'
            }`}
          />
          <span className={isLiveConnected ? 'text-emerald-400' : 'text-rose-400'}>
            {isLiveConnected ? 'LIVE SYNC' : 'OFFLINE'}
          </span>
          <button
            onClick={() => refreshMissions()}
            title="Refresh State"
            className="ml-1 text-slate-400 hover:text-slate-200"
          >
            <RefreshCw className="w-3 h-3" />
          </button>
        </div>

        {/* Operator Badge */}
        <div className="hidden sm:flex items-center gap-1.5 text-xs font-mono text-slate-400 px-2 py-1 bg-slate-900/60 border border-slate-800 rounded">
          <Activity className="w-3.5 h-3.5 text-cyan-400" />
          <span>OPERATOR</span>
        </div>

        {/* New Mission CTA */}
        <Link
          href="/missions/new"
          className="flex items-center gap-1 bg-cyan-500 hover:bg-cyan-400 text-slate-950 px-3 py-1.5 rounded text-xs font-semibold font-mono transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>NEW MISSION</span>
        </Link>
      </div>
    </header>
  );
}
