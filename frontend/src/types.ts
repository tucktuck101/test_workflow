export type GameStatus = 'in_progress' | 'player_won' | 'agent_won' | 'quit' | 'aborted';

export type PlayerType = 'human' | 'random_bot' | 'heuristic_bot' | 'dqn_agent';

export type CellState = 'unknown' | 'miss' | 'hit' | 'sunk' | 'ship';

export type TrainingRunStatus = 'pending' | 'running' | 'succeeded' | 'failed' | 'canceled';

export interface GameStartResponse {
  game_id: string;
  board: CellState[][];
  agent_board_masked: CellState[][];
  status: GameStatus;
  model_version?: string;
  model_hash?: string;
  player_type?: PlayerType;
  agent_type?: PlayerType;
  auto_play?: boolean;
}

export interface MoveRequest {
  x: number;
  y: number;
}

export interface MoveResponse {
  player_result: { outcome: CellState; ship?: string };
  agent_move: { x: number; y: number; outcome: CellState; ship?: string };
  board: CellState[][];
  agent_board_masked: CellState[][];
  status: GameStatus;
}

export interface QuitResponse {
  status: 'ended';
}

export interface TrainingRunResponse {
  run_id: string;
  status: TrainingRunStatus;
  config: Record<string, unknown>;
  error?: string | null;
  created_at?: number;
  updated_at?: number;
}

export interface TrainingMetricsResponse {
  run_id: string;
  metrics: {
    episodes?: number;
    win_rate?: number;
    loss?: number;
    curriculum_phase?: string;
    [key: string]: unknown;
  };
}

export type ErrorCode =
  | 'invalid_coordinates'
  | 'duplicate_move'
  | 'game_not_found'
  | 'game_finished'
  | 'capacity_exceeded'
  | 'rate_limited'
  | 'model_not_ready'
  | 'inference_failed'
  | 'no_available_moves'
  | 'training_not_found'
  | 'invalid_payload'
  | 'path_invalid'
  | 'hash_mismatch'
  | 'path_outside_root';

export interface ApiError {
  error_code: ErrorCode;
  message: string;
  details?: Record<string, unknown> | null;
}

export interface ErrorResponse {
  detail: ApiError;
}

export interface ReadyResponse {
  status: 'ready';
  model_version: string;
  model_hash: string;
  device: string;
}

export interface ModelInfo {
  name: string;
  path: string;
  hash: string;
  size_bytes: number;
  modified_at: number;
  version?: string;
  device?: string;
}

export interface ModelListResponse {
  active: ModelInfo | null;
  models: ModelInfo[];
}
