---
name: typescript
description: Enforces 100% strict TypeScript types, schema synchronization, and frontend data safety for Agent-X.
---

# TypeScript Engineering Skill

## 1. Purpose
Enforce complete type safety across the Agent-X frontend, ensure synchronized data contracts between Python backend Pydantic models and TypeScript interfaces, and eliminate runtime type errors.

## 2. When to Use
- When writing or editing any `.ts` or `.tsx` file in the frontend.
- When generating or maintaining TypeScript type definitions matching backend API and Firestore schemas.
- When configuring `tsconfig.json` compiler options.

## 3. Constraints
- `noImplicitAny: true`, `strictNullChecks: true`, `strict: true` must be enabled.
- The `any` type is strictly prohibited (use `unknown`, generics, or discriminated unions).
- All API payloads must use typed response interfaces.

## 4. Inputs
- Python Pydantic models from backend `/agentx/models/`.
- Frontend component props, state hooks, and API client methods.

## 5. Outputs
- Synchronized TypeScript interfaces and type aliases (`types/mission.ts`, `types/dag.ts`, `types/entity.ts`).
- Type-safe API client wrappers using `fetch` or `ky`.
- Discriminated union types for state machine statuses and error classes.

## 6. Implementation Rules
1. Define discriminated unions for polymorphic types (e.g. `type TaskStatus = 'PENDING' | 'READY' | 'RUNNING' | 'VERIFIED' | 'FAILED'`).
2. Use Zod schemas for client-side validation when parsing SSE or WebSocket events.
3. Export reusable types from centralized type declaration files.

## 7. Testing Requirements
- Type validation with `tsc --noEmit` on every build and CI gate.

## 8. Failure Conditions
- Committing code with `as any` type casts to bypass type checking.
- Desynchronized type models causing runtime `undefined` property crashes.
