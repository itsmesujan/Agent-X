'use client';

import React, { useState } from 'react';
import { useMission } from '@/lib/context';
import { api } from '@/lib/api';
import { Settings, Save, CheckCircle2, Activity } from 'lucide-react';

export default function SettingsPage() {
  const { apiUrl, authToken, setApiUrl, setAuthToken, refreshMissions } =
    useMission();

  const [inputUrl, setInputUrl] = useState(apiUrl);
  const [inputToken, setInputToken] = useState(authToken);
  const [healthStatus, setHealthStatus] = useState<string | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [savedMsg, setSavedMsg] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setApiUrl(inputUrl);
    setAuthToken(inputToken);
    setSavedMsg(true);
    setTimeout(() => setSavedMsg(false), 3000);
    refreshMissions();
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setHealthStatus(null);
    try {
      const res = await api.getHealth();
      setHealthStatus(`Connected! Version: ${res.version}, Status: ${res.status}`);
    } catch (err: unknown) {
      setHealthStatus(
        `Failed: ${err instanceof Error ? err.message : 'Could not reach backend API.'}`
      );
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-100 font-mono tracking-tight flex items-center gap-2">
          <Settings className="w-5 h-5 text-cyan-400" />
          <span>MISSION CONTROL SETTINGS</span>
        </h1>
        <p className="text-xs text-slate-400 font-mono mt-1">
          Configure backend API endpoints, authentication tokens, and cluster telemetry synchronization.
        </p>
      </div>

      {savedMsg && (
        <div className="p-3.5 bg-emerald-950/80 border border-emerald-800 rounded-lg flex items-center gap-2 text-emerald-300 text-xs font-mono">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>Settings saved successfully. Reconnecting telemetry stream...</span>
        </div>
      )}

      <form onSubmit={handleSave} className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl space-y-5 font-mono text-xs">
        <div>
          <label className="block text-slate-300 font-semibold mb-1">FastAPI Backend URL</label>
          <input
            type="text"
            required
            value={inputUrl}
            onChange={(e) => setInputUrl(e.target.value)}
            placeholder="http://localhost:8000"
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-500"
          />
          <div className="text-[11px] text-slate-500 mt-1">
            Endpoint where Agent-X FastAPI service is hosted.
          </div>
        </div>

        <div>
          <label className="block text-slate-300 font-semibold mb-1">
            Operator Bearer Authentication Token
          </label>
          <input
            type="text"
            required
            value={inputToken}
            onChange={(e) => setInputToken(e.target.value)}
            placeholder="dev-token-operator"
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-500 font-mono"
          />
          <div className="text-[11px] text-slate-500 mt-1">
            JWT or simulated dev token passed in Authorization: Bearer header.
          </div>
        </div>

        <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
          <button
            type="button"
            onClick={handleTestConnection}
            disabled={isTesting}
            className="flex items-center gap-1.5 text-slate-300 hover:text-slate-100 bg-slate-950 border border-slate-800 px-3.5 py-2 rounded-lg font-medium transition-colors"
          >
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            <span>{isTesting ? 'Testing...' : 'Test Connection'}</span>
          </button>

          <button
            type="submit"
            className="flex items-center gap-1.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 px-5 py-2 rounded-lg font-bold transition-colors shadow-lg shadow-cyan-500/20"
          >
            <Save className="w-4 h-4" />
            <span>SAVE CONFIGURATION</span>
          </button>
        </div>

        {healthStatus && (
          <div
            className={`p-3 rounded-lg border text-xs font-mono mt-3 ${
              healthStatus.startsWith('Connected')
                ? 'bg-emerald-950/60 border-emerald-800 text-emerald-300'
                : 'bg-rose-950/60 border-rose-800 text-rose-300'
            }`}
          >
            {healthStatus}
          </div>
        )}
      </form>
    </div>
  );
}
