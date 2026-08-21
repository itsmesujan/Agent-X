---
name: nextjs
description: Guides development of the Next.js App Router PWA Mission Control, React 19 components, and state management.
---

# Next.js & React Skill

## 1. Purpose
Architect, build, and optimize the **Agent-X Mission Control** progressive web application using **Next.js (App Router)**, **React 19**, and **Tailwind CSS**.

## 2. When to Use
- When creating or modifying UI pages, layouts, and route handlers under `/app/`.
- When integrating the React Flow interactive DAG canvas or xterm.js streaming terminal.
- When configuring PWA service workers (`next-pwa` / Workbox) and Web App Manifests.
- When managing client state with Zustand and TanStack Query.

## 3. Constraints
- Use Next.js App Router (`/app` directory layout).
- Mark real-time, interactive, and canvas components explicitly with `'use client'`.
- Must support responsive desktop and tablet/mobile viewports.
- Enforce strict dark mode visual design system (`bg-slate-950`, cyan/emerald/rose accents).

## 4. Inputs
- REST API and SSE endpoints from FastAPI backend.
- Firestore client snapshot subscriptions.
- UI wireframes and user journey requirements.

## 5. Outputs
- Next.js page components, layouts, and interactive UI widgets.
- Service Worker registration and Web Push notification handlers.
- Production build bundles (`npm run build`).

## 6. Implementation Rules
1. Keep Server Components for initial static data fetching where possible; use Client Components for reactive DAG rendering and log streaming.
2. Structure UI components modularly: `components/dag/`, `components/terminal/`, `components/world/`, `components/evidence/`.
3. Use Lucide React icons and Tailwind CSS utility classes.
4. Implement error boundaries (`error.tsx`) and loading skeletons (`loading.tsx`) on all mission routes.

## 7. Testing Requirements
- Component unit tests with `Vitest` and `@testing-library/react`.
- Build verification via `next build` ensuring zero TypeScript or ESLint errors.

## 8. Failure Conditions
- Mixing server and client state indiscriminately causing hydration errors.
- Unvirtualized terminal log lists causing UI lag during high-frequency streaming.
