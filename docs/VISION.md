# Vision

- Build a production-ready Battleship web app where everyday users anonymously play against a pre-trained RL agent.
- Deliver smooth gameplay: land on homepage, start a game, play turns, quit gracefully.
- Run locally first, but be deployment-ready for Kubernetes (dev/test/prod) with a separate training environment.
- Keep MVP anonymous; add accounts/leaderboards later without blocking current scope.
- Favor open-source, cost-free components; no paid SaaS or cloud until deployment is explicitly approved.
- Priorities (initial order): 1) MVP gameplay API + rules + RL inference stub/real path; 2) Frontend play loop; 3) Observability and test coverage; 4) Training pipeline bootstrap for model artifacts.
