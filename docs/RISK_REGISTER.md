# Risk Register (MVP)

| Risk | Likelihood | Impact | Owner | Mitigation | Status |
| --- | --- | --- | --- | --- | --- |
| Model quality insufficient for fun gameplay | Medium | Medium | RL | Iterate training; add evaluation loop; allow swapping artifacts via config | Open |
| Inference latency too high for interactive play | Medium | High | Backend | Keep inference in-process; optimize model; consider lighter policy for runtime; monitor latency metrics | Open |
| Load under concurrency (move endpoint) | Medium | High | Backend | Load tests; pool management; cap active games; optimize validation paths | Open |
| Model artifact missing/corrupted | Low | High | Backend | Verify hash on startup; fail readiness if mismatch; store version/hash in config | Open |
| No persistence leads to lost games on restart | Medium | Low | Backend | Accept for MVP; plan ADR for persistence later | Accepted for MVP |
| DoS via excessive game creation/moves | Medium | Medium | Backend | Add rate limits and caps; monitor active sessions; readiness unaffected | Open |
| Determinism gaps cause flaky tests | Low | Medium | QA | Use deterministic/stubbed agent; seed RNG in tests; pin fixture boards | Open |
