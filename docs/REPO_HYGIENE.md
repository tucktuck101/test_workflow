# Repo Hygiene & Branch Protection (MVP)

- **Branch protection (main/stage branches):** require PR, CI checks (`CI`, `security`, `pre-commit`), no direct pushes. Enable status checks to block merge on failures.
- **CI gating:** `ci/run_quality_gates.sh` runs pytest with coverage (via pytest-cov), and detects mypy/Node type checks when configured. Add npm scripts/mypy configs as scaffolds land.
- **CODE_MAP updates:** update `CODE_MAP.md` whenever backend/frontend/training scaffolds add new modules (see TASK-030 for follow-ups).
- **README/CONTRIBUTING alignment:** keep setup commands and required checks current as code is added (backend/frontend/training).
- **Secrets/logging:** gitleaks runs in CI; do not log payloads/coords/model paths; keep `.env` local; no secrets committed.
