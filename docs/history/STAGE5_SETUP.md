# Stage 5 Setup / Repo Hygiene (Plan)

Historical status: `Historical`  
This file is archived planning context. Links below are retained for history and adjusted for moved paths.

- Baseline scaffolding: add `.editorconfig`, formatter/linter configs, and pre-commit hooks (already present; verify stack-specific configs once code is scaffolded).
- CI: ensure workflows run lint/format/tests/type checks/security scans and enforce coverage thresholds per Quality Gates (medium/standard). Update `ci/run_quality_gates.sh` to call project scripts when added.
- CODE_MAP updates: expand once backend/frontend/training code is created; keep in sync with new modules.
- Branch protection: enable required checks from `.github/workflows/ci.yml` on `main`; prevent direct merges without PR + Critic Pass.
- Templates: Issue/PR templates already present—validate they include ADR check and Critic Pass reminders (done).
- Docs: update README/CONTRIBUTING as code scaffolding lands (commands, scripts, run instructions).
- Tracking: ensure `docs/history/EPIC_LOG.md` and `docs/history/BACKLOG.md` stay updated as Epics/Features move; tag epics/features per PROCESS_CHECKLIST.
