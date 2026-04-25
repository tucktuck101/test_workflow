# Frontend Agent Guide

## Purpose
Use this guide for changes under `frontend/`. The root `AGENTS.md` still applies; this file covers the React/Vite gameplay UI and separate training UI entrypoint.

## Local Source Truth
- `src/App.tsx` is the gameplay UI.
- `src/TrainingControl.tsx` is the training control UI.
- `src/api.ts` owns browser API calls and error mapping.
- `src/types.ts` mirrors frontend-facing API and UI types.
- `src/main.tsx` and `index.html` are the gameplay entrypoint.
- `src/training.tsx`, `training.html`, and `vite.training.config.ts` are the training UI entrypoint and build.
- `vite.config.ts`, `vitest.config.ts`, `playwright.config.ts`, and `package.json` define the frontend command surface.

## Editing Guidance
- Keep `api.ts`, `types.ts`, backend schemas, and component tests aligned when API payloads change.
- Preserve the gameplay/training UI split. Do not accidentally make the training build depend on gameplay-only entrypoint assumptions.
- Keep UI behavior testable through accessible labels, roles, and stable user-visible states.
- Follow existing Vite, React Testing Library, and Vitest patterns before adding new frontend dependencies.
- Avoid editing or committing generated outputs such as `dist/`, `dist-training/`, and `coverage/` unless the task explicitly asks for generated artifacts.

## Focused Checks
- Type-only or API-client changes: `cd frontend && npm run typecheck`.
- Gameplay UI changes: targeted Vitest for `src/App.test.tsx`, then `npm run build` when build risk exists.
- Training UI changes: targeted Vitest for `src/TrainingControl.test.tsx`, then `npm run build:training` when build risk exists.
- API helper changes: targeted Vitest for `src/api.test.ts`.
- End-to-end flow changes: `cd frontend && npm run test:e2e` only when browser workflow coverage is needed.

## Docs Triggers
- Update `docs/CURRENT_STATE.md` when verified UI capabilities change.
- Update `docs/DEMO_PATH.md` or deployment docs when ports, entrypoints, or demo commands change.
- Update `CODE_MAP.md` when frontend entrypoints, command surfaces, or major component boundaries change.

## Pitfalls
- Do not rely on built assets under `frontend/dist*` as source.
- Do not run Playwright by reflex for small component-only changes.
- If both gameplay and training UIs consume the same API field, verify both surfaces before calling the change complete.
