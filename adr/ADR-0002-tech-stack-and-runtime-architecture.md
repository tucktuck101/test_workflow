# ADR-0002-tech-stack-and-runtime-architecture

- Status: Accepted
- Date: 2025-11-26
- Deciders: Supervisor, Codex

## Context
- Production-ready Battleship web app with anonymous play against an RL agent; local-first with future Kubernetes deployment.
- Environments: dev, test, prod runtimes, plus isolated training; monorepo preferred; no paid SaaS/cloud during MVP.
- Requirements: rigorous testing/observability, load testing, CPU/GPU-capable training, cost-free/open-source components.
- MVP state: no auth/leaderboards, no persistent game history; in-memory state acceptable.

## Decision
- Frontend: React + TypeScript (Vite or similar bundler) SPA.
- Backend: Python + FastAPI providing REST API for game start/move/quit, enforcing game rules and validation.
- RL stack: PyTorch for training and inference.
- Runtime shape: single backend service hosts both game engine and in-process RL inference; frontend served separately as static assets/container.
- Model lifecycle: offline training pipeline produces versioned artifacts; runtime loads a static model at startup (CPU by default, GPU-supported when available).
- State: in-memory session/game state for MVP; defer persistence until accounts/leaderboards/history are added.
- Deployment targets: containerized services for local development and k8s readiness across dev/test/prod; training runs as a separate job/pipeline outside runtime services.

## Consequences
- Pros: cohesive monorepo and small number of services; low-latency inference by avoiding network hops; open-source stack with strong ecosystem; straightforward k8s packaging.
- Cons: backend coupling to inference increases startup time and resource footprint; model artifact management required; deterministic testing needs stubs/seeds; future persistence will need migration/ADR.
- Follow-ups: add ADR for persistence/DB choice when history/accounts arrive; document model artifact build/promotion flow; keep load testing and observability wired to move/inference paths.***
