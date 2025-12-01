export type GameStatus = 'in_progress' | 'player_won' | 'agent_won' | 'quit' | 'aborted';

export type CellState = 'unknown' | 'miss' | 'hit' | 'sunk' | 'ship';

export interface GameStartResponse {
  game_id: string;
  board: CellState[][];
  agent_board_masked: CellState[][];
  status: GameStatus;
  model_version: string;
  model_hash: string;
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
