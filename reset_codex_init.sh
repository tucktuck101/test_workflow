#!/usr/bin/env bash
set -euo pipefail

echo "=== Codex Init Reset Utility ==="
echo "Working directory: $(pwd)"
echo

# Helper to ask y/n
ask_yn() {
  local prompt default var
  prompt="$1"
  default="$2"  # y or n
  local default_label
  if [ "$default" = "y" ]; then
    default_label="Y/n"
  else
    default_label="y/N"
  fi
  while true; do
    read -r -p "$prompt [$default_label]: " var || true
    if [ -z "$var" ]; then
      var="$default"
    fi
    case "$var" in
      y|Y) echo "true"; return 0 ;;
      n|N) echo "false"; return 0 ;;
      *) echo "Please answer y or n." ;;
    esac
  done
}

# 1. Always safe to remove: Codex-specific config files
echo "Step 1: Remove Codex policy and checklist files"

if [ -f "PROJECT_POLICY.yaml" ]; then
  echo "  - Found PROJECT_POLICY.yaml -> will remove"
  rm -f PROJECT_POLICY.yaml
else
  echo "  - PROJECT_POLICY.yaml not found (nothing to do)"
fi

if [ -f "CODEX_ONBOARDING_CHECKLIST.md" ]; then
  echo "  - Found CODEX_ONBOARDING_CHECKLIST.md -> will remove"
  rm -f CODEX_ONBOARDING_CHECKLIST.md
else
  echo "  - CODEX_ONBOARDING_CHECKLIST.md not found (nothing to do)"
fi

echo

# 2. Optional: remove AGENT_CONTRACT.md if it looks like the generated one
echo "Step 2: Optional removal of AGENT_CONTRACT.md"

if [ -f "AGENT_CONTRACT.md" ]; then
  if grep -q "Project binding summary" AGENT_CONTRACT.md 2>/dev/null; then
    if [ "$(ask_yn "AGENT_CONTRACT.md looks like the generated file. Delete it?" "y")" = "true" ]; then
      rm -f AGENT_CONTRACT.md
      echo "  - AGENT_CONTRACT.md removed."
    else
      echo "  - Keeping AGENT_CONTRACT.md."
    fi
  else
    echo "  - AGENT_CONTRACT.md exists, but does not look like the generated version."
    echo "    (No 'Project binding summary' marker found.)"
    if [ "$(ask_yn "Do you still want to delete AGENT_CONTRACT.md?" "n")" = "true" ]; then
      rm -f AGENT_CONTRACT.md
      echo "  - AGENT_CONTRACT.md removed."
    else
      echo "  - Keeping AGENT_CONTRACT.md."
    fi
  fi
else
  echo "  - AGENT_CONTRACT.md not found (nothing to do)"
fi

echo

# 3. Optional: remove .gitignore if it looks like the generated minimal one
echo "Step 3: Optional removal of .gitignore"

if [ -f ".gitignore" ]; then
  # Heuristic: check for the Python/Node/general block we seeded
  if grep -q "__pycache__/" .gitignore && grep -q "node_modules/" .gitignore; then
    if [ "$(ask_yn ".gitignore looks like the generated minimal file. Delete it?" "n")" = "true" ]; then
      rm -f .gitignore
      echo "  - .gitignore removed."
    else
      echo "  - Keeping .gitignore."
    fi
  else
    echo "  - .gitignore exists but does not look like the generated minimal one."
    echo "    (It may be your own file.)"
  fi
else
  echo "  - .gitignore not found (nothing to do)"
fi

echo

# 4. Optional: nuke the git repository entirely
echo "Step 4: Optional removal of the entire git repository (.git directory)"
if [ -d ".git" ]; then
  echo "Warning: deleting .git will:"
  echo "  - Remove all git history"
  echo "  - Remove remotes (origin, etc.)"
  echo "  - Reset this folder to a non-git directory"
  echo
  if [ "$(ask_yn "Do you want to delete the entire .git directory?" "n")" = "true" ]; then
    rm -rf .git
    echo "  - .git directory removed. This folder is no longer a git repository."
  else
    echo "  - Keeping .git directory and git history."
  fi
else
  echo "  - .git directory not found (nothing to do)"
fi

echo
echo "Reset complete."
echo "You can now rerun the init script for another test run."
