# ADR 0004: Next.js / TypeScript Progressive Web Application (PWA) for Mission Control

## Status
**Accepted**

## Context
Agent-X requires an interactive, high-performance web interface to serve as the Mission Control cockpit. Operators must visualize dynamic DAG graphs in real time, stream high-frequency terminal logs, inspect complex code diffs, and receive urgent push notifications on desktop or mobile when human intervention (HITL) is required.

We evaluated Vite + React SPA, Next.js (App Router), SvelteKit, and Electron.

## Decision
We select **Next.js (App Router) with TypeScript** deployed as an installable **Progressive Web Application (PWA)**:
- **UI Framework**: React 19 + Next.js App Router.
- **Graph Visualization**: `@xyflow/react` (React Flow) with Dagre layout engine.
- **Telemetry Streaming**: Server-Sent Events (SSE) client + xterm.js / virtualized log viewer.
- **Styling**: Vanilla Tailwind CSS with custom cyber-ops dark mode tokens.
- **PWA Capabilities**: Service Worker for push notifications, Web App Manifest for native desktop/mobile installation.

## Rationale
- **Single Universal Codebase**: Delivers a rich web experience and an installable desktop/mobile PWA without maintaining separate native apps.
- **High-Performance Canvas**: React Flow enables interactive panning, zooming, and node inspection on complex graphs with hundreds of nodes.
- **Real-Time Push Alerts**: Service Worker integration ensures Mission Commanders receive instant notifications for HITL pauses or mission completions even when the browser tab is in the background.
- **Server Components & Streaming**: Next.js App Router optimizes initial page loads while client components handle live WebSocket/SSE streaming.

## Consequences
- **Positive**: Exceptional developer ergonomics, rich ecosystem of components (React Flow, Lucide, diff viewers), cross-platform PWA reach, high visual polish.
- **Negative**: Requires careful separation of server and client components when integrating live WebSockets and Firestore client SDKs.
