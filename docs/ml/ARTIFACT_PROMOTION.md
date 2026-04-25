# Artifact Promotion

Doc status: Reviewed  
Capability status: Partial  
Last verified: 2026-04-25  
Review trigger: artifact validation, promotion command, runtime config, readiness, or rollback changes.

## Goal
Move a trained Battleships agent artifact from training output into runtime serving in a repeatable, observable way.

## Current Truth
Artifact validation tooling and model readiness checks exist. Promotion is currently documented as an operational flow rather than a fully automated pipeline.

## Intended Promotion Gate
- Artifact exists under an allowed root.
- Manifest exists and matches artifact hash.
- Device/runtime configuration is supported.
- Validation command returns success.
- Runtime readiness reports the expected version/hash after deployment.

## Implemented
- `tools.validate_artifact.py` validates artifact/manifest/root/device inputs.
- Runtime readiness verifies configured artifact state before serving.
- Promotion and rollback operator steps are documented in `docs/RUNBOOKS.md`.

## Planned
- Single promotion command or Make target.
- Sample manifest fixture.
- CI/manual workflow documentation for artifact validation.
- Stronger links from promotion steps to rollback and incident runbooks.

## Roadmap
- Keep promotion evidence in `docs/VERIFICATION.md` or a small linked evidence note, not in generated artifact files.
- Promote capability status only after validation, promotion, readiness, and rollback have a verified command path.

## Verification
Reconciled on 2026-04-25 against `tools/validate_artifact.py`, `app/health.py`, `app/config.py`, `docker-compose.yml`, and `docs/RUNBOOKS.md`.
