# Documentation Source Of Truth

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: any change to API contracts, runtime flow, training flow, CI, deployment behavior, or documentation lifecycle rules.

## Purpose
This file is the canonical entrypoint for documentation. It defines trust order, navigation, lifecycle status, and conflict resolution for both humans and coding agents.

## Current Truth
The repository is an active Battleships AI/ML training environment with backend, frontend, training, container, and test code. Some capabilities are fully implemented, some are partial, and some platform targets remain planned. Use this docs suite to understand current behavior without treating historical planning docs as source truth.

## Trust Order
When documents disagree, use this precedence:

1. Runtime truth from code, tests, configs, Dockerfiles, package manifests, and observed command output.
2. Active operational docs: this file, `docs/CURRENT_STATE.md`, `docs/VERIFICATION.md`, and `CODE_MAP.md`.
3. Active thematic docs in `docs/portfolio/`, `docs/operations/`, and `docs/ml/`.
4. Historical docs in `docs/history/`, governance history, ADRs, and older planning artifacts.
5. Generated notes, screenshots, diagnostics, metrics, or ad hoc artifacts.

## Conflict Rule
If docs conflict with code/tests/config, treat the docs as outdated and open a docs correction task. Do not treat stale text as authority.

## Status Model
Docs use two status layers:

- `Doc status: Reviewed` means the document has been reconciled against current source or verified command output.
- `Doc status: Needs evidence` means the document shape is useful, but a claim needs fresh runtime, CI, dashboard, or demo evidence.
- `Doc status: Historical` means the document is preserved context, not current operating guidance.
- `Capability status: Implemented` means the described behavior exists and is verifiable in current source/tests/runtime.
- `Capability status: Partial` means some behavior exists, but known gaps or planned work remain.
- `Capability status: Planned` means the behavior is intentional but not currently implemented.

`Partial` describes capability maturity, not whether a document is unfinished.

## Question Index
Use this to answer most questions within two clicks.

- What does the system do today:
  `docs/CURRENT_STATE.md` (`Reviewed`, capability `Partial`)
- What has been checked recently:
  `docs/VERIFICATION.md` (`Reviewed`, capability `Partial`)
- How do I run/demo it:
  `docs/DEMO_PATH.md` (`Reviewed`, capability `Partial`)
- How do I bootstrap the fresh GitHub repo:
  `docs/REPOSITORY_BOOTSTRAP.md` (`Draft`, capability `Planned`)
- How is the system architected:
  `docs/ARCHITECTURE.md` (`Reviewed`, capability `Partial`)
- API behavior and contracts:
  `docs/API_SPEC.md` (`Reviewed`, capability `Partial`)
- Model lifecycle and promotion:
  `docs/ml/MODEL_LIFECYCLE.md` and `docs/ml/ARTIFACT_PROMOTION.md` (`Reviewed`, capability `Partial`)
- Training orchestration truth and roadmap:
  `docs/ml/TRAINING_ORCHESTRATION.md` (`Reviewed`, capability `Partial`)
- SLOs, alerts, dashboards, incident process:
  `docs/operations/SLOS.md`, `docs/operations/ALERTING.md`, `docs/operations/DASHBOARDS.md`, `docs/operations/INCIDENT_RESPONSE.md` (`Reviewed`, capability `Partial`)
- Promotion/rollback run steps:
  `docs/RUNBOOKS.md` (`Reviewed`, capability `Partial`)
- Portfolio narrative:
  `docs/portfolio/CASE_STUDY.md` and companions (`Reviewed`, capability `Partial`)
- Historical planning/governance context:
  `docs/history/README.md` (`Historical`, capability `Historical`)

## Active Doc Register
| Document | Doc status | Capability status | Primary question | Review trigger |
| --- | --- | --- | --- | --- |
| `docs/CURRENT_STATE.md` | Reviewed | Partial | What is real right now? | Runtime/API/training behavior changes |
| `docs/VERIFICATION.md` | Reviewed | Partial | What was checked recently? | Verification command reruns |
| `docs/DEMO_PATH.md` | Reviewed | Partial | How do I demo from checkout? | Setup/compose/smoke changes |
| `docs/REPOSITORY_BOOTSTRAP.md` | Draft | Planned | How is the presentation repo created? | GitHub setup changes |
| `docs/API_SPEC.md` | Reviewed | Partial | What endpoints/behaviors exist? | Route/schema/error changes |
| `docs/ARCHITECTURE.md` | Reviewed | Partial | How components interact? | Module boundary changes |
| `docs/DEPLOYMENT.md` | Reviewed | Partial | How is this packaged/deployed? | Docker/k8s/env changes |
| `docs/OBSERVABILITY_SPEC.md` | Reviewed | Partial | What should be measured? | Instrumentation/alert changes |
| `docs/RUNBOOKS.md` | Reviewed | Partial | How do operators promote/rollback? | Lifecycle or on-call flow changes |
| `docs/ml/*` | Reviewed | Partial | How does the ML lifecycle work? | Training/promotion changes |
| `docs/operations/*` | Reviewed | Partial | How is the system operated? | SLO/alert/dashboard/process changes |
| `docs/portfolio/*` | Reviewed | Partial | What is the portfolio story? | Material capability changes |
| `docs/history/*` | Historical | Historical | What was planned before? | Link fixes only |

## Roadmap
- Keep active docs source-verified and concise.
- Keep planned capabilities honest, especially real training orchestration, dashboard artifacts, alert rules, and Kubernetes execution.
- Move capability status toward `Implemented` only after source, tests, or runtime evidence proves the capability.
- Keep verification summaries small; do not commit generated logs, screenshots, coverage, or model artifacts unless explicitly requested.

## Verification
This file was reconciled against the active docs tree, `docs/CURRENT_STATE.md`, `CODE_MAP.md`, `Makefile`, API routes/schemas, trainer orchestration source, and Docker Compose configuration on 2026-04-25. See `docs/VERIFICATION.md` for command summaries.
