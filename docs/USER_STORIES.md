# User Stories (MVP)

- As a visitor, I can land on a homepage to understand I’m about to play Battleship against an RL agent.
  - Acceptance: homepage loads without auth; clear call to start a game.

- As a player, I can start a new game and receive the initial board state/game_id.
  - Acceptance: start action returns game_id and initial state; game is playable immediately.

- As a player, I can submit a move and see whether it is a hit/miss/sunk plus the updated board.
  - Acceptance: move endpoint validates coordinates, rejects invalid/duplicate moves, and responds with outcome and remaining ships.

- As a player, I can see the RL agent’s responding move and its effect on my board.
  - Acceptance: each turn returns the agent move/result and updated state; no desync between client and server.

- As a player, I can quit a game early.
  - Acceptance: quit request ends the session and frees server state; further moves are rejected for that game_id.

- As an operator, I can check service health/readiness.
  - Acceptance: health endpoints surface readiness/liveness, failing when dependencies or model load are unhealthy.
