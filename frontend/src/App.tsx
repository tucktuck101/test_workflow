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
                {cell === 'unknown' ? '' : cell === 'miss' ? '•' : '×'}
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
    return { tone: 'ready', text: `Ready · ${readiness.model_version}` };
  }, [readiness]);

  async function handleStart() {
    setLoading(true);
    setError(null);
    try {
      const res = await startGame();
      setGameId(res.game_id);
      setBoard(res.board);
      setAgentBoard(res.agent_board_masked);
      setStatus(res.status);
      setModelMeta({ version: res.model_version, hash: res.model_hash });
      setLogs([{ tone: 'info', message: 'Game started. Take your shot.' }]);
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
  const moveDisabled = !gameId || moveLoading || isFinished;

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
            {gameId ? 'Restart' : 'Start Game'}
          </button>
          <button className="button secondary" onClick={handleQuit} disabled={!gameId || loading}>
            Quit
          </button>
          <span style={{ color: 'var(--muted)', fontSize: 14 }}>API: {API_BASE}</span>
        </div>
        {error && (
          <div role="alert" className="message error" style={{ marginTop: 10 }}>
            {error}
          </div>
        )}
      </div>

      <div className="board-wrap" aria-live="polite">
        <Board grid={board} label="Your Board" disabled={moveDisabled} onCellClick={handleMove} />
        <Board grid={agentBoard} label="Agent Board (masked)" disabled onCellClick={undefined} />
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
