import './globals.css';
import type { Metadata } from 'next';
import { MissionProvider } from '@/lib/context';
import { Shell } from '@/components/layout/Shell';

export const metadata: Metadata = {
  title: 'Agent-X Mission Control',
  description: 'Autonomous Mission Operating System PWA',
  manifest: '/manifest.json',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 min-h-screen">
        <MissionProvider>
          <Shell>{children}</Shell>
        </MissionProvider>
      </body>
    </html>
  );
}
