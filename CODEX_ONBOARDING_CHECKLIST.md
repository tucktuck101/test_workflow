Codex Onboarding Checklist (Minimal Bootstrap)
This repository has been bootstrapped only enough for Codex
to begin Interview Mode. All project-specific decisions must be
made by Codex and the supervisor during the interview.
Before Codex starts
 AGENT_CONTRACT.md contains the full AGENT_CONTRACT v1.4 text
 PROJECT_POLICY.yaml skeleton exists
 docs/ directory exists
 adr/ directory exists
 Branch protection enabled on main integration branch
 CI set up to run at least basic tests on PRs
First Codex Epic (e.g. EPIC-000 Onboard Codex Agent)
When the supervisor instructs Codex to begin Interview Mode, Codex must:
Run Interview Mode and:
Ask about supervision_mode and supervisor_response_window_hours
Ask about workflow_profile, tier, repo_strategy, security_profile
Ask about tech stack constraints, environments, and domain toggles
Update PROJECT_POLICY.yaml to replace all TO_BE_SET_BY_CODEX values
Create initial ADRs:
ADR-0001-workflow-profile-and-tier.md
ADRs for tech stack and key architectural decisions
Create initial docs:
docs/VISION.md
docs/REQUIREMENTS.md
docs/USER_STORIES.md
docs/RISK_REGISTER.md (or in docs/)
Create or update:
docs/ARCHITECTURE.md
OBSERVABILITY_SPEC.md
SECURITY_NOTES.md or THREAT_MODEL.md
Set up:
Project boards (Backlog, Ready, In Progress, In Review, Ready for Human Review, Done)
Issue labels (Epic, Feature, Task, Bug, Tech Debt, Refactor, Incident, BLOCKER)
