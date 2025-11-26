# Summary
- [ ] User-facing/behavioural summary
- [ ] Linked Issues/ADRs

# Quality Gate
- risk_level: [ ] low [ ] medium [ ] high [ ] regulated
- task tier (change type): [ ] quick_fix [ ] standard [ ] strategic
- Applied Quality Gate row (Risk x Tier): __________________
- Evidence of required checks:
  - Tests: __________________
  - Coverage meets gate? [ ] Yes (evidence: ________)
  - Security checks (deps/secrets/SAST/DAST per gate): [ ] Done (details: ________)
  - Observability updated (metrics/logs/traces per gate): [ ] Done (details: ________)
  - SLO/SLI docs updated if applicable: [ ] N/A [ ] Updated
- Pattern Playbook applied? [ ] No [ ] Yes — name: __________ (all steps completed)

# Testing
- [ ] Unit
- [ ] Integration
- [ ] E2E/Contract
- [ ] Regression/Smoke for impacted flows
- [ ] Other: __________________

# Observability
- Primary impacted operation/flow: __________________
- Metrics/logs/traces added or updated: [ ] Yes (describe) __________________
- Dashboards/alerts updated if relevant: [ ] N/A [ ] Updated

# Critic Pass Procedure (Contract §15.1)
- [ ] Perspective Flip (user intent + success/failure described)
- [ ] Failure Scenarios (≥2 identified; covered by tests or documented)
- [ ] Red-Flag check (auth/permissions/data schema/public API/security-sensitive). If triggered: mark PR “Needs Human Review.”
- [ ] Critic notes added to PR/Issue: link __________________

# CI / Hygiene
- [ ] All required CI jobs passing
- [ ] Pre-commit hooks run/updated if needed
- [ ] No unexplained coverage drops (>2pp) on affected components
