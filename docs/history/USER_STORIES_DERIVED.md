# User Stories (Derived from BR/FR)

## US-001 Start a Game (Player)
- Parent FR: FR-001
- Story: As a player, I want to start a new Battleship game so that I can play against the RL agent.
- Scenario Acceptance Criteria: Start returns game_id and initial state; readiness passes; errors surfaced for capacity/model-not-ready.
- Dependencies & Conditions: Requires readiness/model load; MAX_ACTIVE_GAMES cap.
- Traceability: BR-001; FR-001; NFR-001/002/003/004.

## US-002 Submit Moves and See Results
- Parent FR: FR-001
- Story: As a player, I want to submit moves and see hit/miss/sunk plus updated boards so that I can progress the game.
- Scenario Acceptance Criteria: Validates coordinates/bounds/duplicates/finished state; returns player + agent outcomes; handles 400/404/409/429/503.
- Dependencies & Conditions: Board state deterministic per game; agent response per FR-002.
- Traceability: BR-001; FR-001/FR-002; NFR-001/002/003/004.

## US-003 See RL Agent Response
- Parent FR: FR-002
- Story: As a player, I want to see the RL agent’s responding move so that I understand the game state.
- Scenario Acceptance Criteria: Agent move rendered each turn; deterministic in test mode; errors surfaced if inference unavailable.
- Dependencies & Conditions: Agent adapter availability; model load; deterministic mode for tests.
- Traceability: BR-001; FR-002; NFR-001/002/003/004.

## US-004 Quit a Game Early
- Parent FR: FR-001
- Story: As a player, I want to quit a game early so that I can stop playing without leaving lingering state.
- Scenario Acceptance Criteria: Quit ends session; further moves rejected; state freed; response confirms end.
- Dependencies & Conditions: Session tracking; capacity caps.
- Traceability: BR-001; FR-001; NFR-002/003.

## US-005 See System Health/Readiness
- Parent FR: FR-004
- Story: As an operator, I want to see health/readiness status so that I know if the service and model are ready.
- Scenario Acceptance Criteria: /health/live returns ok; /health/ready reflects model load/hash; failures surface 503; readiness shown in UI.
- Dependencies & Conditions: Model path/hash/device config; probes wired.
- Traceability: BR-002/BR-004; FR-004/FR-006; NFR-002/003/006.
