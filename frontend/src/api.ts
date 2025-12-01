import type {
  GameStartResponse,
  MoveRequest,
  MoveResponse,
  QuitResponse,
  ErrorResponse,
  ReadyResponse,
  ApiError,
  PlayerType,
  TrainingRunResponse,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function buildUrl(path: string) {
  return `${API_BASE}${path}`;
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as Partial<ErrorResponse>;
    const detail = body.detail as ApiError | undefined;
    const error: ApiError =
      detail || {
        error_code: 'model_not_ready',
        message: 'Unexpected error',
      };
    throw error;
  }
  return res.json() as Promise<T>;
}

export async function fetchReadiness(): Promise<ReadyResponse> {
  const res = await fetch(buildUrl('/health/ready'));
  return handle<ReadyResponse>(res);
}

type GameConfigPayload = {
  placements?: { name: string; coordinates: number[][] }[];
  config?: { player_type: PlayerType; agent_type: PlayerType; auto_play: boolean };
};

export async function startGame(payload?: GameConfigPayload): Promise<GameStartResponse> {
  const res = await fetch(buildUrl('/api/games'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: payload ? JSON.stringify(payload) : '{}',
  });
  return handle<GameStartResponse>(res);
}

export async function makeMove(gameId: string, payload: MoveRequest): Promise<MoveResponse> {
  const res = await fetch(buildUrl(`/api/games/${gameId}/moves`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handle<MoveResponse>(res);
}

export async function quitGame(gameId: string): Promise<QuitResponse> {
  const res = await fetch(buildUrl(`/api/games/${gameId}/quit`), { method: 'POST' });
  return handle<QuitResponse>(res);
}

export async function startTraining(config: Record<string, unknown>): Promise<TrainingRunResponse> {
  const res = await fetch(buildUrl('/api/training/runs'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ config }),
  });
  return handle<TrainingRunResponse>(res);
}

export async function getTraining(runId: string): Promise<TrainingRunResponse> {
  const res = await fetch(buildUrl(`/api/training/runs/${runId}`));
  return handle<TrainingRunResponse>(res);
}

export async function cancelTraining(runId: string): Promise<TrainingRunResponse> {
  const res = await fetch(buildUrl(`/api/training/runs/${runId}/cancel`), { method: 'POST' });
  return handle<TrainingRunResponse>(res);
}

export function mapError(err: ApiError): { tone: 'error' | 'warn'; message: string } {
  const retry = err.error_code === 'rate_limited' || err.error_code === 'model_not_ready';
  const backoff = retry ? ' Please retry in a few seconds.' : '';
  const messages: Record<string, string> = {
    invalid_coordinates: 'Move outside board. Pick a valid tile.',
    duplicate_move: 'You already fired there. Choose another coordinate.',
    game_not_found: 'Game not found. Start a new one.',
    game_finished: 'Game finished. Start another round.',
    capacity_exceeded: 'Server is full. Try again shortly.',
    rate_limited: 'Too many requests.',
    model_not_ready: 'Model not ready yet.',
    inference_failed: 'Agent move failed.',
    no_available_moves: 'No moves remain.',
    training_not_found: 'Training run not found.',
    invalid_payload: 'Request was invalid.',
    path_invalid: 'Model path invalid.',
    hash_mismatch: 'Model hash mismatch.',
    path_outside_root: 'Model path outside allowed root.',
  };
  const tone: 'error' | 'warn' = retry || err.error_code === 'capacity_exceeded' ? 'warn' : 'error';
  return { tone, message: (messages[err.error_code] || err.message || 'Error') + backoff };
}

export { API_BASE };
