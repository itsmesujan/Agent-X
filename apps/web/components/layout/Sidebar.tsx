'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useMission } from '@/lib/context';
import {
  LayoutDashboard,
  PlusCircle,
  Activity,
  GitBranch,
  CheckSquare,
  Bot,
  Cpu,
  FileCheck2,
  AlertTriangle,
  HelpCircle,
  Layers,
  Settings,
} from 'lucide-react';

export function Sidebar() {
  const pathname = usePathname();
  const { activeMissionId } = useMission();
  const mid = activeMissionId || 'current';

  const navItems = [
    { label: 'Dashboard', href: '/', icon: LayoutDashboard, exact: true },
    { label: 'New Mission', href: '/missions/new', icon: PlusCircle },
    { label: 'Overview', href: `/missions/${mid}`, icon: Activity, requiresMission: true },
    { label: 'Graph', href: `/missions/${mid}/graph`, icon: GitBranch, requiresMission: true },
    { label: 'Tasks', href: `/missions/${mid}/tasks`, icon: CheckSquare, requiresMission: true },
    { label: 'Agents', href: `/missions/${mid}/agents`, icon: Bot, requiresMission: true },
    { label: 'Resources', href: `/missions/${mid}/resources`, icon: Cpu, requiresMission: true },
    { label: 'Evidence', href: `/missions/${mid}/evidence`, icon: FileCheck2, requiresMission: true },
    { label: 'Failures', href: `/missions/${mid}/failures`, icon: AlertTriangle, requiresMission: true },
    { label: 'Decisions', href: `/missions/${mid}/decisions`, icon: HelpCircle, requiresMission: true },
    { label: 'Artifacts', href: `/missions/${mid}/artifacts`, icon: Layers, requiresMission: true },
    { label: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-56 bg-slate-950/80 border-r border-slate-800 flex flex-col justify-between shrink-0">
      <nav className="p-3 space-y-1 overflow-y-auto">
        <div className="text-[10px] font-mono uppercase text-slate-500 px-3 py-1.5 font-semibold tracking-wider">
          NAVIGATION
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = item.exact
            ? pathname === item.href
            : pathname.startsWith(item.href) && item.href !== '/';

          return (
            <Link
              key={item.label}
              href={item.href}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-mono transition-colors ${
                isActive
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-medium'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span className="truncate">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer System Info */}
      <div className="p-3 border-t border-slate-900 text-[11px] font-mono text-slate-600">
        <div>Agent-X OS v0.1.0</div>
        <div>Google ADK + GenAI</div>
      </div>
    </aside>
  );
}
