import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';

type FetchHandler = (url: string, init?: RequestInit) => Response;

const startPayload = {
  game_id: 'g-1',
  board: Array.from({ length: 2 }, () => ['unknown', 'unknown']),
  agent_board_masked: Array.from({ length: 2 }, () => ['unknown', 'unknown']),
  status: 'in_progress',
  model_version: 'stub',
  model_hash: 'hash',
};

const movePayload = {
  player_result: { outcome: 'hit' },
  agent_move: { x: 0, y: 1, outcome: 'miss' },
  board: [['hit', 'unknown'], ['unknown', 'unknown']],
  agent_board_masked: [['unknown', 'unknown'], ['unknown', 'unknown']],
  status: 'in_progress',
};

function makeFetcher(handler: FetchHandler) {
  return vi.fn(async (url: string, init?: RequestInit) => handler(url.toString(), init));
}

function jsonResponse(payload: any, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe('App', () => {
  it('renders readiness badge when ready', async () => {
    const fetchMock = makeFetcher((url) => {
      if (url.includes('/health/ready')) return jsonResponse({ status: 'ready', model_version: 'v', model_hash: 'h', device: 'cpu' });
      return jsonResponse(startPayload);
    });
    vi.stubGlobal('fetch', fetchMock as any);

    render(<App />);

    expect(await screen.findByText(/Ready/)).toBeInTheDocument();
  });

  it('can start and make a move', async () => {
    const fetchMock = makeFetcher((url, init) => {
      if (url.includes('/health/ready')) return jsonResponse({ status: 'ready', model_version: 'v', model_hash: 'h', device: 'cpu' });
      if (url.endsWith('/api/games')) return jsonResponse(startPayload);
      if (url.includes('/moves')) return jsonResponse(movePayload);
      return jsonResponse({ status: 'ended' });
    });
    vi.stubGlobal('fetch', fetchMock as any);

    render(<App />);
    const startBtn = await screen.findByRole('button', { name: /start/i });
    fireEvent.click(startBtn);
    await screen.findByText(/Game started/);

    const cells = screen.getAllByRole('button', { name: /Agent Board.*cell/ });
    fireEvent.click(cells[0]);

    await waitFor(() => expect(screen.getByText(/Agent fired/)).toBeInTheDocument());
  });

  it('shows backoff guidance on 429', async () => {
    const fetchMock = makeFetcher((url) => {
      if (url.includes('/health/ready')) return jsonResponse({ status: 'ready', model_version: 'v', model_hash: 'h', device: 'cpu' });
      if (url.endsWith('/api/games'))
        return jsonResponse({ detail: { error_code: 'rate_limited', message: 'Too many' } }, 429);
      return jsonResponse({});
    });
    vi.stubGlobal('fetch', fetchMock as any);

    render(<App />);
    const startBtn = await screen.findByRole('button', { name: /start/i });
    fireEvent.click(startBtn);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/retry/);
    });
  });
});
