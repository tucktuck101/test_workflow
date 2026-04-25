#!/usr/bin/env bash
set -euo pipefail

OWNER="${OWNER:-tucktuck101}"
REPO="${REPO:-battleships-rl-platform}"
PROJECT_TITLE="${PROJECT_TITLE:-Battleships RL Platform Delivery}"

require() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

require gh

repo="${OWNER}/${REPO}"

create_label() {
  local name="$1"
  local color="$2"
  local description="$3"
  gh label create "$name" --repo "$repo" --color "$color" --description "$description" --force >/dev/null
}

echo "[bootstrap] Creating labels"
create_label "Epic" "6f42c1" "Large outcome or initiative"
create_label "Feature" "1d76db" "Deliverable feature capability"
create_label "Task" "0e8a16" "Smallest planned unit of work"
create_label "Bug" "d73a4a" "Defect or failing behavior"
create_label "ADR" "5319e7" "Architecture decision record"
create_label "Incident" "b60205" "Operational incident or failed deployment"
create_label "ci-cd" "0052cc" "CI/CD or release automation"
create_label "backend" "0366d6" "Backend API/runtime"
create_label "frontend" "0e8a16" "Frontend UI"
create_label "training" "fbca04" "Training pipeline"
create_label "model" "c5def5" "Model artifact or inference behavior"
create_label "infra" "bfd4f2" "Infrastructure and Kubernetes"
create_label "docs" "0075ca" "Documentation"
create_label "agent-ready" "2ea44f" "Ready for AI agent execution"
create_label "needs-info" "d93f0b" "Needs more information before work starts"
create_label "source: ci" "ededed" "Created from CI automation"
create_label "deployment" "c2e0c6" "Deployment record or deployment work"
create_label "project-admin" "ededed" "Project automation and hygiene"
create_label "triage: needed" "fbca04" "Needs triage"
create_label "triage: feature-needed" "fef2c0" "Needs parent feature assignment"
create_label "risk:low" "c2e0c6" "Low-risk change"
create_label "risk:medium" "fbca04" "Medium-risk change"
create_label "risk:high" "d93f0b" "High-risk change"
create_label "risk:regulated" "b60205" "Regulated or sensitive change"

echo "[bootstrap] Creating environments"
for env in model-promotion local-demo k3s-prod; do
  gh api --method PUT "repos/${repo}/environments/${env}" >/dev/null
done

echo "[bootstrap] Creating or locating project"
if gh project list --owner "$OWNER" --format json | grep -q "\"title\":\"${PROJECT_TITLE}\""; then
  project_number="$(gh project list --owner "$OWNER" --format json --jq ".projects[] | select(.title == \"${PROJECT_TITLE}\") | .number" | head -n 1)"
else
  gh project create --owner "$OWNER" --title "$PROJECT_TITLE" >/dev/null
  project_number="$(gh project list --owner "$OWNER" --format json --jq ".projects[] | select(.title == \"${PROJECT_TITLE}\") | .number" | head -n 1)"
fi

echo "[bootstrap] Project number: ${project_number}"
gh variable set PROJECT_OWNER --repo "$repo" --body "$OWNER" >/dev/null
gh variable set PROJECT_NUMBER --repo "$repo" --body "$project_number" >/dev/null

echo "[bootstrap] Create these ProjectV2 fields if gh project field-create is unavailable on your gh version:"
cat <<'FIELDS'
- Board Column: Backlog, Ready, In Progress, In Review, Ready for Human Review, Done
- Type: Epic, Feature, Task, Bug, ADR, Incident
- Component: backend, frontend, training, model, ci-cd, infra, docs
- Environment: local, ci, local-demo, k3s-prod
- Risk: low, medium, high, regulated
- Agent Status: blocked, ready, working, needs-human, complete
- Human Review: needed, approved, blocked
- Release/Image Tag: text
- Model Version: text
- Deployment Status: text
FIELDS

if gh project field-create --help >/dev/null 2>&1; then
  gh project field-create "$project_number" --owner "$OWNER" --name "Board Column" --data-type SINGLE_SELECT --single-select-options "Backlog,Ready,In Progress,In Review,Ready for Human Review,Done" || true
  gh project field-create "$project_number" --owner "$OWNER" --name "Type" --data-type SINGLE_SELECT --single-select-options "Epic,Feature,Task,Bug,ADR,Incident" || true
  gh project field-create "$project_number" --owner "$OWNER" --name "Component" --data-type SINGLE_SELECT --single-select-options "backend,frontend,training,model,ci-cd,infra,docs" || true
  gh project field-create "$project_number" --owner "$OWNER" --name "Environment" --data-type SINGLE_SELECT --single-select-options "local,ci,local-demo,k3s-prod" || true
  gh project field-create "$project_number" --owner "$OWNER" --name "Risk" --data-type SINGLE_SELECT --single-select-options "low,medium,high,regulated" || true
  gh project field-create "$project_number" --owner "$OWNER" --name "Agent Status" --data-type SINGLE_SELECT --single-select-options "blocked,ready,working,needs-human,complete" || true
  gh project field-create "$project_number" --owner "$OWNER" --name "Human Review" --data-type SINGLE_SELECT --single-select-options "needed,approved,blocked" || true
  gh project field-create "$project_number" --owner "$OWNER" --name "Release/Image Tag" --data-type TEXT || true
  gh project field-create "$project_number" --owner "$OWNER" --name "Model Version" --data-type TEXT || true
  gh project field-create "$project_number" --owner "$OWNER" --name "Deployment Status" --data-type TEXT || true
fi

echo "[bootstrap] Required manual follow-ups:"
echo "- Add PROJECT_PAT secret with repo + project permissions if GITHUB_TOKEN cannot update the user project."
echo "- Configure environment reviewers for model-promotion, local-demo, and k3s-prod."
echo "- Configure branch protection on main after PR CI appears at least once."
echo "- Install the self-hosted runner on the future k3s node with labels: self-hosted,k3s,battleship."
