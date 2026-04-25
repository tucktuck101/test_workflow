# Repository Bootstrap

Doc status: Draft  
Capability status: Planned  
Last verified: 2026-04-25  
Review trigger: GitHub repo, Project, label, environment, or branch-protection setup changes.

## Goal
Create a clean presentation repository named `battleships-rl-platform` while keeping this local workspace as the dev/test source during migration.

## Fresh Import
Use the clean-import helper from this workspace:

```bash
VISIBILITY=private scripts/bootstrap/create_presentation_repo.sh
```

The script copies the current files to `/tmp/battleships-rl-platform-import`, excludes generated/local outputs, initializes a new Git repository, and creates/pushes `tucktuck101/battleships-rl-platform`.

Keep the current `test_workflow` repository private or archived as development history.

## GitHub Setup
After the new repo exists, run:

```bash
scripts/bootstrap/setup_github_repo.sh
```

This bootstraps labels, GitHub Environments, the delivery project, and repository variables used by project automation.

Manual follow-ups:
- Add `PROJECT_PAT` if `GITHUB_TOKEN` cannot update the user-level Project.
- Add environment reviewers for `model-promotion`, `local-demo`, and `k3s-prod`.
- Add branch protection to `main` after `PR CI` has run once.
- Add the future k3s self-hosted runner with labels `self-hosted`, `k3s`, and `battleship`.
- If GHCR packages remain private, create a k3s `imagePullSecret` for GHCR and reference it from the runtime manifests before deployment.

## Project Fields
The project-admin workflow expects these ProjectV2 fields:

| Field | Type / Options |
| --- | --- |
| Board Column | Backlog, Ready, In Progress, In Review, Ready for Human Review, Done |
| Type | Epic, Feature, Task, Bug, ADR, Incident |
| Component | backend, frontend, training, model, ci-cd, infra, docs |
| Environment | local, ci, local-demo, k3s-prod |
| Risk | low, medium, high, regulated |
| Agent Status | blocked, ready, working, needs-human, complete |
| Human Review | needed, approved, blocked |
| Release/Image Tag | text |
| Model Version | text |
| Deployment Status | text |

## Verification
Once setup is complete:

```bash
gh repo view tucktuck101/battleships-rl-platform
gh variable list --repo tucktuck101/battleships-rl-platform
gh project list --owner tucktuck101
```
