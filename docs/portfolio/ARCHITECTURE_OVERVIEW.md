# Architecture Overview

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: architecture, deployment, orchestration, or subsystem boundary changes.

## Current Truth
The portfolio architecture is a source-backed full-stack ML training and runtime system. The training API lifecycle exists, but real job execution remains planned.

## System Shape
Battleships is the bounded domain. The portfolio system surrounds it with training, validation, inference, and operations workflows.

```text
Training configs -> Trainer/self-play -> Artifact + manifest -> Validation
        |                                                   |
        v                                                   v
Training UI/API status                             Runtime model load
                                                            |
Gameplay UI -> FastAPI gameplay API -> Agent adapter -> Move response
                                                            |
                                             Health, metrics, logs, runbooks
```

## Active Components
- Backend API: FastAPI routes, gameplay engine, model readiness, rate limiting, and trainer run endpoints.
- Gameplay UI: browser surface for placing ships, playing turns, and inspecting model readiness.
- Training UI: browser control surface for training config, curriculum, run actions, and metrics polling.
- Training pipeline: trainer, DQN/self-play, curriculum, evaluation, artifact validation, and configs.
- Platform layer: Docker Compose, Dockerfiles, CI, smoke scripts, runbooks, and Kubernetes job stubs.

## Implemented
- Backend, gameplay UI, training UI, training modules, validation tooling, containers, smoke scripts, and runbooks are present.
- Text architecture diagram describes the current source-backed flow.

## Planned
- Maintained diagram once repo structure settles.
- Real training orchestration documentation after simulated orchestration is replaced.
- Deployment topology for local, CI, and Kubernetes-style execution.

## Roadmap
- Keep this diagram in sync with `docs/ARCHITECTURE.md`.
- Do not claim Kubernetes-style execution is production-ready until verification evidence exists.

## Verification
Reconciled on 2026-04-25 against `CODE_MAP.md`, `docs/ARCHITECTURE.md`, `docs/DEPLOYMENT.md`, and training orchestration docs.
