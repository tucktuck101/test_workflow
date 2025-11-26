# Security Notes (MVP)

- Authentication: none for MVP (anonymous play). Plan to add auth/leaderboards later; assume hostile client.
- Input validation: strict coordinate and game-state validation; reject invalid/duplicate/out-of-order moves; enforce bounds on payload sizes.
- Data handling: no PII stored; in-memory game state only; model artifacts read-only and verified by hash.
- Dependencies: run dependency and secrets scanning in CI; prefer maintained, open-source packages.
- Config/secrets: use env vars for keys/paths; avoid committing secrets; support k8s secrets later.
- Networking: add rate limiting/DoS protections when exposed beyond local; keep backend authoritative to prevent client-side tampering; consider simple request shaping/backoff.
- Threats to note:
  - Tampered clients sending invalid coordinates or replaying moves → handled by validation and status checks.
  - DoS via spamming game creation/moves → mitigate with rate limits and caps on active sessions per client/IP.
  - Model integrity risk → verify hash on startup; fail readiness if mismatch.
  - Path traversal on model path → restrict to configured directory and validate path.
- Logging: avoid storing payloads; ensure no secrets or model paths beyond necessity; structured logs with game_id only.

## Threat Model (STRIDE-lite, key surfaces)
- Start game (`POST /api/games`): abuse via creation spam → mitigated by `MAX_ACTIVE_GAMES` cap (429) and planned per-IP rate limits; malformed payloads → schema validation with size bounds; tampered model readiness → readiness gate blocks.
- Move submission (`POST /api/games/{id}/moves`): invalid/out-of-bounds/duplicate moves → strict validation; replay or desync attempts → finished-game/duplicate checks; DoS via brute-force moves → planned rate limits and per-game ordering enforcement; inference misuse → deterministic stub for tests only, production uses real model or fails.
- Quit (`POST /api/games/{id}/quit`): low risk; ensure idempotent and rejects finished games to prevent abuse of state machine.
- Health endpoints: avoid leaking internals; readiness returns minimal model metadata; on failure, return generic error_code and not full stack traces.
- Model artifacts: tampering/path traversal → validate root, hash-check on startup; refuse to serve if mismatch; version/hash logged with load.

## Mitigations and Controls
- Validation: coordinate bounds, finished-game/duplicate guards, payload size (<1KB), strict schemas (reject unexpected fields).
- Availability: `MAX_ACTIVE_GAMES` cap; planned 429 rate limiting/backoff guidance to clients; circuit-breaker on repeated inference failures (mark game aborted, readiness 503).
- Integrity: SHA256 verification of model artifacts; restrict load path to configured root; deterministic mode gated to non-production use.
- Least privilege: run without elevated perms; avoid writing model directories; keep dependencies minimal and scanned.
- Observability safeguards: structured logs with `game_id`, no payloads or secrets; metrics/traces avoid high-cardinality user data.

## Log Scrubbing Rules
- Do not log request bodies, coordinates, or model paths by default; emit coarse validation error codes only.
- Ensure hashes/versions are logged once at startup/readiness; avoid repeating in every request log.

## Red-Flag Areas (mandatory human review)
- Auth/permissions/identity (future features such as leaderboards/logins).
- Data schema changes or migrations (when persistence is introduced).
- Public API contracts (any changes to `/api/games` endpoints or health/readiness payloads).
- Security-sensitive code paths (model integrity checks, validation logic, rate limiting, path validation).

## Security Checks in CI
- Dependency and secrets scanning on every PR; SAST/IaC lint when available.
- Ensure no secrets/PII in logs; structured logging with minimal fields.
