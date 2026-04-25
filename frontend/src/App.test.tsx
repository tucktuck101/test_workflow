import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';

type FetchHandler = (url: string, init?: RequestInit) => Response;

const BOARD_SIZE = 10;

const makeBoard = (fill: string) =>
  Array.from({ length: BOARD_SIZE }, () => Array.from({ length: BOARD_SIZE }, () => fill));

const startPayload = {
  game_id: 'g-1',
  board: (() => {
    const board = makeBoard('unknown');
    // mark a few ships so we can assert visibility
    board[0][0] = 'ship';
    board[0][1] = 'ship';
    board[1][0] = 'ship';
    return board;
  })(),
  agent_board_masked: makeBoard('unknown'),
  status: 'in_progress',
  model_version: 'stub',
  model_hash: 'hash',
};

const movePayload = {
  player_result: { outcome: 'hit' },
  agent_move: { x: 0, y: 1, outcome: 'miss' },
  board: makeBoard('unknown'),
  agent_board_masked: makeBoard('unknown'),
  status: 'in_progress',
};

const autoPlayPayload = {
  game_id: 'auto-1',
  board: makeBoard('unknown'),
  agent_board_masked: (() => {
    const b = makeBoard('unknown');
    b[0][0] = 'hit';
    b[1][1] = 'miss';
    return b;
  })(),
  status: 'player_won',
  player_type: 'random_bot',
  agent_type: 'heuristic_bot',
  auto_play: true,
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

function placeFleet() {
  const anchors: [number, number][] = [
    [0, 0], // Carrier (5) horizontal
    [0, 1], // Battleship (4)
    [0, 2], // Cruiser (3)
    [0, 3], // Submarine (3)
    [0, 4], // Destroyer (2)
  ];
  anchors.forEach(([x, y]) => {
    const cell = screen.getByLabelText(
      new RegExp(`Your Board \\(place your ships\\) cell ${x},${y} \\(unknown\\)`, 'i')
    );
    fireEvent.click(cell);
  });
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe('App', () => {
  it('renders readiness badge when ready', async () => {
    const fetchMock = makeFetcher((url) => {
      if (url.includes('/health/ready'))
        return jsonResponse({
          status: 'ready',
          model_version: 'v',
          model_hash: 'h',
          device: 'cpu',
        });
      return jsonResponse(startPayload);
    });
    vi.stubGlobal('fetch', fetchMock as any);

    render(<App />);

    expect(await screen.findByText(/Ready/)).toBeInTheDocument();
  });

  it('can start and make a move', async () => {
    const fetchMock = makeFetcher((url, init) => {
      if (url.includes('/health/ready'))
        return jsonResponse({
          status: 'ready',
          model_version: 'v',
          model_hash: 'h',
          device: 'cpu',
        });
      if (url.endsWith('/api/games')) return jsonResponse(startPayload);
      if (url.includes('/moves')) return jsonResponse(movePayload);
      return jsonResponse({ status: 'ended' });
    });
    vi.stubGlobal('fetch', fetchMock as any);

    render(<App />);
    const startBtn = await screen.findByRole('button', { name: /^Start Game$/i });
    fireEvent.click(startBtn);

    placeFleet();

    const confirmBtn = screen.getByRole('button', { name: /confirm placements/i });
    fireEvent.click(confirmBtn);
    await screen.findByText(/Fleet deployed/);
    expect(screen.getByLabelText(/Your Board .*0,0 \(ship\)/i)).toBeInTheDocument();

    const cells = screen.getAllByRole('button', { name: /Agent Board.*cell/ });
    fireEvent.click(cells[0]);

    await waitFor(() => expect(screen.getByText(/Agent fired/)).toBeInTheDocument());
  });

  it('auto-plays bot vs bot and renders outcome', async () => {
    const fetchMock = makeFetcher((url, init) => {
      if (url.includes('/health/ready'))
        return jsonResponse({
          status: 'ready',
          model_version: 'v',
          model_hash: 'h',
          device: 'cpu',
        });
      if (url.endsWith('/api/games')) {
        const body = init?.body ? JSON.parse(init.body.toString()) : {};
        expect(body?.config?.auto_play).toBe(true);
        expect(body?.config?.player_type).toBe('random_bot');
        expect(body?.config?.agent_type).toBe('heuristic_bot');
        return jsonResponse(autoPlayPayload);
      }
      return jsonResponse({ status: 'ended' });
    });
    vi.stubGlobal('fetch', fetchMock as any);

    render(<App />);
    const readyText = await screen.findByText(/Ready/);
    expect(readyText).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/^You$/), { target: { value: 'random_bot' } });
    fireEvent.change(screen.getByLabelText(/Opponent/), { target: { value: 'heuristic_bot' } });
    fireEvent.click(screen.getByLabelText(/Auto-play/));

    const startBtn = screen.getByRole('button', { name: /^Start Game$/i });
    fireEvent.click(startBtn);

    await screen.findByText(/Auto-play completed/);
    expect(screen.getByText(/Auto-play completed: You won/i)).toBeInTheDocument();
    const agentBoardCells = screen.getAllByRole('button', { name: /Agent Board/ });
    expect(
      agentBoardCells.some((c) => c.className.includes('hit') || c.className.includes('miss'))
    ).toBe(true);
  });

  it('blocks auto-play when a human is selected', async () => {
    const fetchMock = makeFetcher((url) => {
      if (url.includes('/health/ready'))
        return jsonResponse({
          status: 'ready',
          model_version: 'v',
          model_hash: 'h',
          device: 'cpu',
        });
      return jsonResponse(startPayload);
    });
    vi.stubGlobal('fetch', fetchMock as any);

    render(<App />);
    await screen.findByText(/Ready/);
    fireEvent.click(screen.getByLabelText(/Auto-play/));

    const startBtn = screen.getByRole('button', { name: /^Start Game$/i });
    fireEvent.click(startBtn);

    expect(await screen.findByRole('alert')).toHaveTextContent(/Auto-play requires both players/);
  });

  it('shows backoff guidance on 429', async () => {
    const fetchMock = makeFetcher((url) => {
      if (url.includes('/health/ready'))
        return jsonResponse({
          status: 'ready',
          model_version: 'v',
          model_hash: 'h',
          device: 'cpu',
        });
      if (url.endsWith('/api/games'))
        return jsonResponse({ detail: { error_code: 'rate_limited', message: 'Too many' } }, 429);
      return jsonResponse({});
    });
    vi.stubGlobal('fetch', fetchMock as any);

    render(<App />);
    const startBtn = await screen.findByRole('button', { name: /^Start Game$/i });
    fireEvent.click(startBtn);
    placeFleet();

    const confirmBtn = screen.getByRole('button', { name: /confirm placements/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/retry/);
    });
  });
});
