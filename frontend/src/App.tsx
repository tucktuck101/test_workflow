import { useEffect, useMemo, useState } from 'react';
import { API_BASE, fetchReadiness, makeMove, mapError, quitGame, startGame } from './api';
import type { CellState, GameStatus, MoveResponse, ReadyResponse } from './types';

interface BoardProps {
  grid: CellState[][];
  label: string;
  disabled: boolean;
  onCellClick?: (x: number, y: number) => void;
}

function Board({ grid, label, disabled, onCellClick }: BoardProps) {
  const renderSymbol = (cell: CellState) => {
    if (cell === 'unknown') return '';
    if (cell === 'ship') return '⬢';
    if (cell === 'miss') return '•';
    return '×';
  };

  return (
    <div aria-label={label} className="card">
      <div className="status-line" style={{ marginBottom: 8 }}>
        <strong>{label}</strong>
      </div>
      <div className="board" role="grid" aria-disabled={disabled}>
        {grid.map((row, y) => (
          <div className="board-row" role="row" key={y}>
            {row.map((cell, x) => (
              <button
                key={`${x}-${y}`}
                className={`cell ${cell}`}
                disabled={disabled}
                onClick={() => onCellClick && onCellClick(x, y)}
                aria-label={`${label} cell ${x},${y} (${cell})`}
              >
                {renderSymbol(cell)}
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

interface LogEntry {
  tone: 'info' | 'warn' | 'error';
  message: string;
}

const emptyBoard = (size: number): CellState[][] => Array.from({ length: size }, () => Array.from({ length: size }, () => 'unknown' as CellState));

const statusCopy: Record<GameStatus | 'ready', string> = {
  ready: 'Ready to start',
  in_progress: 'In progress',
  player_won: 'You won! 🎉',
  agent_won: 'Agent won',
  quit: 'Quit',
  aborted: 'Aborted',
};

const isReady = (val: ReadyResponse | { status: 'checking' | 'error'; reason?: string }): val is ReadyResponse =>
  val.status === 'ready';

const SHIPS = [
  { name: 'Carrier', size: 5 },
  { name: 'Battleship', size: 4 },
  { name: 'Cruiser', size: 3 },
  { name: 'Submarine', size: 3 },
  { name: 'Destroyer', size: 2 },
];
const FLEET_SIZE = SHIPS.reduce((sum, ship) => sum + ship.size, 0);

function App() {
  const [board, setBoard] = useState<CellState[][]>(emptyBoard(10));
  const [agentBoard, setAgentBoard] = useState<CellState[][]>(emptyBoard(10));
  const [gameId, setGameId] = useState<string | null>(null);
  const [status, setStatus] = useState<GameStatus | 'ready'>('ready');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [moveLoading, setMoveLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [readiness, setReadiness] = useState<ReadyResponse | { status: 'checking' | 'error'; reason?: string }>({ status: 'checking' });
  const [modelMeta, setModelMeta] = useState<{ version?: string; hash?: string }>({});
  const [placementMode, setPlacementMode] = useState(false);
  const [placementMap, setPlacementMap] = useState<Record<string, number[][]>>({});
  const [currentShipIdx, setCurrentShipIdx] = useState(0);
  const [orientation, setOrientation] = useState<'horizontal' | 'vertical'>('horizontal');

  useEffect(() => {
    fetchReadiness()
      .then((res) => {
        setReadiness(res);
        setModelMeta({ version: res.model_version, hash: res.model_hash });
      })
      .catch((err) => {
        const mapped = mapError(err);
        setReadiness({ status: 'error', reason: mapped.message });
      });
  }, []);

  const readyBadge = useMemo(() => {
    if (readiness.status === 'checking') return { tone: 'loading', text: 'Checking readiness…' };
    if (readiness.status === 'error') return { tone: 'error', text: readiness.reason || 'Not ready' };
    if (isReady(readiness)) return { tone: 'ready', text: `Ready · ${readiness.model_version}` };
    return { tone: 'error', text: 'Not ready' };
  }, [readiness]);

  function resetPlacement() {
    const size = board.length || 10;
    setPlacementMode(true);
    setPlacementMap({});
    setCurrentShipIdx(0);
    setOrientation('horizontal');
    setBoard(emptyBoard(size));
    setAgentBoard(emptyBoard(size));
    setGameId(null);
    setStatus('ready');
    setLogs([{ tone: 'info', message: 'Placement mode: click a cell to place each ship in order.' }]);
  }

  const playerGrid = useMemo(() => {
    if (!placementMode) return board;
    const preview = emptyBoard(board.length || 10);
    Object.values(placementMap).forEach((coords) => {
      coords.forEach(([x, y]) => {
        preview[y][x] = 'ship';
      });
    });
    return preview;
  }, [board, placementMode, placementMap]);

  async function handleStart() {
    setError(null);
    // First click enters placement mode; second confirms once fleet is placed.
    if (!placementMode) {
      resetPlacement();
      return;
    }
    if (Object.keys(placementMap).length !== SHIPS.length) {
      setError(`Place all ships (${FLEET_SIZE} cells) before starting.`);
      return;
    }
    setLoading(true);
    try {
      const placementPayload = buildPlacementsPayload();
      const res = await startGame(placementPayload);
      setGameId(res.game_id);
      setBoard(res.board);
      setAgentBoard(res.agent_board_masked);
      setStatus(res.status);
      setModelMeta({ version: res.model_version, hash: res.model_hash });
      setLogs([{ tone: 'info', message: 'Fleet deployed. Take your shot.' }]);
      setPlacementMode(false);
      setPlacementMap({});
    } catch (err: any) {
      const mapped = mapError(err);
      setError(mapped.message);
      setLogs((prev) => [...prev, { tone: mapped.tone === 'warn' ? 'warn' : 'error', message: mapped.message }]);
    } finally {
      setLoading(false);
    }
  }

  function applyMoveResult(res: MoveResponse) {
    setBoard(res.board);
    setAgentBoard(res.agent_board_masked);
    setStatus(res.status);
    setLogs((prev) => [
      ...prev,
      {
        tone: 'info',
        message: `You fired at (${res.player_result?.outcome ?? '-'})`,
      },
      {
        tone: 'info',
        message: `Agent fired at (${res.agent_move.x},${res.agent_move.y}) → ${res.agent_move.outcome}`,
      },
    ]);
  }

  async function handleMove(x: number, y: number) {
    if (!gameId || status !== 'in_progress') return;
    setMoveLoading(true);
    setError(null);
    try {
      const res = await makeMove(gameId, { x, y });
      applyMoveResult(res);
    } catch (err: any) {
      const mapped = mapError(err);
      setError(mapped.message);
      setLogs((prev) => [...prev, { tone: mapped.tone === 'warn' ? 'warn' : 'error', message: mapped.message }]);
      if (err.error_code === 'game_finished') {
        setStatus('quit');
      }
    } finally {
      setMoveLoading(false);
    }
  }

  function placeShip(x: number, y: number) {
    if (!placementMode) return; // placements only in placement mode
    setError(null);
    const ship = SHIPS[currentShipIdx];
    if (!ship) return;
    const coords =
      orientation === 'horizontal'
        ? Array.from({ length: ship.size }, (_, i) => [x + i, y])
        : Array.from({ length: ship.size }, (_, i) => [x, y + i]);
    if (coords.some(([cx, cy]) => cx < 0 || cy < 0 || cx >= board.length || cy >= board.length)) {
      setError('Ship does not fit on the board with this orientation.');
      return;
    }
    const occupied = new Set<string>();
    Object.entries(placementMap).forEach(([name, coords]) => {
      if (name === ship.name) return;
      coords.forEach((c) => occupied.add(c.join(',')));
    });
    if (coords.some((c) => occupied.has(c.join(',')))) {
      setError('Ships cannot overlap.');
      return;
    }
    const nextMap = { ...placementMap, [ship.name]: coords };
    setPlacementMap(nextMap);
    if (currentShipIdx < SHIPS.length - 1) {
      setCurrentShipIdx(currentShipIdx + 1);
    }
  }

  function buildPlacementsPayload():
    | { placements: { name: string; coordinates: number[][] }[] }
    | undefined {
    const placementsList: { name: string; coordinates: number[][] }[] = [];
    for (const ship of SHIPS) {
      const coords = placementMap[ship.name];
      if (!coords || coords.length !== ship.size) return undefined;
      placementsList.push({ name: ship.name, coordinates: coords });
    }
    return { placements: placementsList };
  }

  async function handleQuit() {
    if (!gameId) return;
    setLoading(true);
    setError(null);
    try {
      await quitGame(gameId);
      setStatus('quit');
      setLogs((prev) => [...prev, { tone: 'info', message: 'You quit the game.' }]);
    } catch (err: any) {
      const mapped = mapError(err);
      setError(mapped.message);
      setLogs((prev) => [...prev, { tone: mapped.tone === 'warn' ? 'warn' : 'error', message: mapped.message }]);
    } finally {
      setLoading(false);
    }
  }

  const isFinished = status !== 'in_progress' && status !== 'ready';
  const moveDisabled = !gameId || moveLoading || isFinished || placementMode;
  const startLabel = placementMode ? 'Confirm placements' : 'Start Game';
  const currentShip = placementMode ? SHIPS[currentShipIdx] : null;

  return (
    <div className="app-shell">
      <header className="header">
        <div>
          <div className="title">Battleship vs RL Agent</div>
          <div className="status-line" aria-live="polite">
            Status: <strong>{statusCopy[status]}</strong>
            {modelMeta.version && <span style={{ color: 'var(--muted)' }}>· Model {modelMeta.version}</span>}
          </div>
        </div>
        <span className={`badge ${readyBadge.tone}`}>{readyBadge.text}</span>
      </header>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="controls">
          <button className="button" onClick={handleStart} disabled={loading} aria-busy={loading}>
            {startLabel}
          </button>
          <button className="button secondary" onClick={handleQuit} disabled={!gameId || loading}>
            Quit
          </button>
          <span style={{ color: 'var(--muted)', fontSize: 14 }}>API: {API_BASE}</span>
        </div>
        {placementMode && currentShip && (
          <div className="status-line" style={{ marginTop: 10, gap: 12, flexWrap: 'wrap' }}>
            <span>
              Placing: <strong>{currentShip.name}</strong> (size {currentShip.size})
            </span>
            <button
              className="button secondary"
              onClick={() => setOrientation((prev) => (prev === 'horizontal' ? 'vertical' : 'horizontal'))}
              type="button"
            >
              Orientation: {orientation === 'horizontal' ? 'Horizontal' : 'Vertical'}
            </button>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {SHIPS.map((ship, idx) => (
                <button
                  key={ship.name}
                  className="button secondary"
                  type="button"
                  onClick={() => setCurrentShipIdx(idx)}
                  aria-pressed={currentShipIdx === idx}
                  style={{
                    borderColor: currentShipIdx === idx ? 'var(--accent)' : undefined,
                    color: currentShipIdx === idx ? 'var(--accent)' : undefined,
                  }}
                >
                  {ship.name}
                </button>
              ))}
            </div>
          </div>
        )}
        {error && (
          <div role="alert" className="message error" style={{ marginTop: 10 }}>
            {error}
          </div>
        )}
      </div>

      <div className="board-wrap" aria-live="polite">
        <Board
          grid={playerGrid}
          label={placementMode ? 'Your Board (place your ships)' : 'Your Board (your fleet)'}
          disabled={Boolean(gameId) && !placementMode}
          onCellClick={placementMode ? placeShip : undefined}
        />
        <Board
          grid={agentBoard}
          label="Agent Board (click to fire)"
          disabled={moveDisabled}
          onCellClick={handleMove}
        />
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="status-line" style={{ marginBottom: 8 }}>
          <strong>Event log</strong>
        </div>
        <div className="log" aria-live="polite">
          {logs.length === 0 && <div className="message warn">No actions yet.</div>}
          {logs.map((entry, idx) => (
            <div key={idx} className={`message ${entry.tone === 'warn' ? 'warn' : entry.tone}`}>{entry.message}</div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
