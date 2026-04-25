# SRE And Platform Story

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: CI, deployment, observability, runbook, or orchestration changes.

## Narrative
This repo is intended to show how ML training and inference systems are operated, not just how an agent plays Battleships.

## Current Truth
The project has Docker Compose services, Dockerfiles, smoke scripts, runbook seeds, and observability documentation. Some platform features are stubs or placeholders, especially real API-triggered training orchestration and dashboard/alert examples.

## Practices To Showcase
- Health and readiness checks tied to model availability.
- Smoke tests for runtime and training paths.
- Artifact validation before promotion.
- Runbooks for promotion, rollback, readiness failures, and training failures.
- SLOs and alerting around API availability, model readiness, inference latency, and training job success.
- Containerized local runtime with a path toward Kubernetes job execution.

## Implemented
- Health and readiness checks tied to model availability.
- Runtime and training smoke command surfaces.
- Artifact validation before promotion.
- Promotion, rollback, incident-response, SLO, alerting, and dashboard documentation.
- Containerized local runtime with a path toward Kubernetes job execution.

## Planned
- Clearer CI/platform evidence staging.
- Dashboard and alert examples.
- Real incident/RCA walkthrough after evidence exists.
- Validated Kubernetes manifests or explicit illustrative labeling.

## Roadmap
- Keep platform claims tied to `docs/VERIFICATION.md` command summaries.
- Keep Kubernetes and alerting language cautious until artifacts and command evidence exist.

## Verification
Reconciled on 2026-04-25 against `docker-compose.yml`, Dockerfiles, `Makefile`, operations docs, and training orchestration docs.
