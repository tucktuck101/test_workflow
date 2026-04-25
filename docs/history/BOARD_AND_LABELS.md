# Board and Labels Configuration (Stage 4)

## Labels (create in repo)
- Work type: `Epic`, `Feature`, `Task`, `Bug`, `Tech Debt`, `Refactor`, `Incident`, `BLOCKER`.
- Risk: `risk:low`, `risk:medium`, `risk:high`, `risk:regulated`.
- Status (optional): `needs-info`, `ready`, `in-review`.

## Board (columns)
- Backlog → Ready → In Progress → In Review → Ready for Human Review → Done.
- Apply tag scheme: `epic-<id>-start`, `epic-<id>-feature-<name>-done`, `epic-<id>-complete`.
- GitHub Project (v2) created: **Delivery Board** (project #6). Fields include:
  - `Board Column` (single select): Backlog, Ready, In Progress, In Review, Ready for Human Review, Done.
  - `Type` (single select): Epic, Feature, Task, Bug, Tech Debt, Refactor, Incident, BLOCKER.
  - Use Status field as needed; prefer `Board Column` for workflow stage.
  - Workflows auto-add items to the board (requires `PROJECT_PAT` secret):
    - `.github/workflows/project-issues.yml`: issues → Board Column = Backlog.
    - `.github/workflows/project-prs.yml`: PRs → In Review on open; Done on close/merge.

## Usage
- Every issue/task includes: acceptance criteria, linked requirements/ADRs, risk level, task tier, Quality Gate row, DoD (tests/coverage/obs/docs/CI), dependencies, and Critic Pass reminder.
- Move cards through columns as work progresses; use labels to filter by risk/type; apply tags at epic milestones.
