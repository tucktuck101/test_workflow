# Requirements

## Functional
- Users can access a homepage and start a new Battleship game against an RL agent.
- Gameplay loop: submit moves, receive results (hit/miss/sunk), view RL agent responses, continue until game end.
- Quit flow: user can end a game early; backend cleans up any in-memory state.
- RL agent served as a static, pre-trained model for inference in runtime environments.
- Training pipeline runs separately from dev/test/prod to produce model artifacts for deployment.
- Health/diagnostic endpoint(s) for readiness/liveness checks.

## Nonfunctional
- Local-first development; be Kubernetes-ready for dev/test/prod plus an isolated training environment.
- Anonymous MVP (no auth, no persistence of user identity); future accounts/leaderboards will be added later.
- Security posture: baseline best practices (input validation, dependency/secrets scanning), least privilege defaults.
- Testing: rigorous; high coverage on game logic and agent integration; load testing for gameplay endpoints.
- Observability: metrics/logging/tracing on key flows (game start, move handling, RL inference latency).
- Performance: responsive turn handling; aim for low-latency move responses suitable for real-time play.
- Cost: avoid paid SaaS/cloud during MVP; prefer open-source components suitable for self-hosting in k8s.
