import { useEffect, useMemo, useState } from 'react';
import YAML from 'js-yaml';
import { cancelTraining, getTraining, getTrainingMetrics, mapError, startTraining } from './api';
import type { TrainingMetricsResponse, TrainingRunResponse, TrainingRunStatus } from './types';

const SAMPLE_YAML = `# Example trainer config
train:
  epochs: 5
  seed: 123
  board_size: 10
`;

interface Props {
  onError?: (msg: string) => void;
}

export function TrainingControl({ onError }: Props) {
  const [yamlText, setYamlText] = useState(SAMPLE_YAML);
  const [run, setRun] = useState<TrainingRunResponse | null>(null);
  const [status, setStatus] = useState<TrainingRunStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<TrainingMetricsResponse['metrics'] | null>(null);
  const [metricHistory, setMetricHistory] = useState<number[]>([]);

  useEffect(() => {
    setStatus(run?.status ?? null);
  }, [run]);

  useEffect(() => {
    let interval: number | undefined;
    if (run && status && ['pending', 'running'].includes(status)) {
      interval = window.setInterval(() => {
        getTrainingMetrics(run.run_id)
          .then((res) => {
            setMetrics(res.metrics);
            if (typeof res.metrics.win_rate === 'number') {
              setMetricHistory((prev) => [...prev.slice(-20), res.metrics.win_rate as number]);
            }
          })
          .catch((err) => {
            const mapped = mapError(err);
            setMessage(mapped.message);
            onError?.(mapped.message);
          });
      }, 2000);
    }
    return () => {
      if (interval) window.clearInterval(interval);
    };
  }, [run, status]);

  function parseYaml(): Record<string, unknown> | null {
    try {
      const parsed = YAML.load(yamlText);
      if (parsed && typeof parsed === 'object') return parsed as Record<string, unknown>;
      throw new Error('YAML must define a mapping/object.');
    } catch (err: any) {
      const msg = err?.message || 'Invalid YAML';
      setMessage(msg);
      onError?.(msg);
      return null;
    }
  }

  async function handleStart() {
    setLoading(true);
    setMessage(null);
    const config = parseYaml();
    if (!config) {
      setLoading(false);
      return;
    }
    try {
      const res = await startTraining(config);
      setRun(res);
      setStatus(res.status);
      setMetrics(null);
      setMetricHistory([]);
      setMessage(`Started training run ${res.run_id}`);
    } catch (err: any) {
      const mapped = mapError(err);
      setMessage(mapped.message);
      onError?.(mapped.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleRefresh() {
    if (!run) return;
    try {
      const res = await getTraining(run.run_id);
      setRun(res);
      setStatus(res.status);
    } catch (err: any) {
      const mapped = mapError(err);
      setMessage(mapped.message);
      onError?.(mapped.message);
    }
  }

  async function handleCancel() {
    if (!run) return;
    try {
      const res = await cancelTraining(run.run_id);
      setRun(res);
      setStatus(res.status);
      setMessage(`Canceled training run ${res.run_id}`);
    } catch (err: any) {
      const mapped = mapError(err);
      setMessage(mapped.message);
      onError?.(mapped.message);
    }
  }

  async function handleUpload(ev: React.ChangeEvent<HTMLInputElement>) {
    const file = ev.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    setYamlText(text);
  }

  const statusBadge = status ? status.toUpperCase() : 'Idle';
  const winRate = metrics?.win_rate ?? null;
  const episodes = metrics?.episodes ?? null;
  const loss = metrics?.loss ?? null;
  const phase = metrics?.curriculum_phase ?? null;

  const sparklinePath = useMemo(() => {
    if (metricHistory.length === 0) return '';
    const max = Math.max(...metricHistory, 1);
    const min = Math.min(...metricHistory, 0);
    const width = 100;
    const height = 30;
    const step = width / Math.max(metricHistory.length - 1, 1);
    return metricHistory
      .map((val, idx) => {
        const x = idx * step;
        const y = height - ((val - min) / (max - min || 1)) * height;
        return `${idx === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .join(' ');
  }, [metricHistory]);

  return (
    <div className="card" style={{ marginTop: 12 }}>
      <div className="status-line" style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
        <strong>Training Control</strong>
        <span className="badge">{statusBadge}</span>
      </div>
      <label className="status-line" style={{ gap: 8, marginBottom: 8 }}>
        <input type="file" accept=".yaml,.yml,text/yaml" onChange={handleUpload} />
        <span style={{ color: 'var(--muted)' }}>Upload YAML to preload config</span>
      </label>
      <textarea
        aria-label="Training YAML"
        value={yamlText}
        onChange={(e) => setYamlText(e.target.value)}
        rows={12}
        style={{ width: '100%', fontFamily: 'monospace', fontSize: 14 }}
      />
      <div className="controls" style={{ marginTop: 8, gap: 8 }}>
        <button className="button" onClick={handleStart} disabled={loading}>
          Start training
        </button>
        <button className="button secondary" onClick={handleRefresh} disabled={!run}>
          Refresh status
        </button>
        <button className="button secondary" onClick={handleCancel} disabled={!run}>
          Cancel run
        </button>
        {run && (
          <span style={{ color: 'var(--muted)', fontSize: 13 }}>Run ID: <code>{run.run_id}</code></span>
        )}
      </div>
      {message && (
        <div role="alert" className="message info" style={{ marginTop: 8 }}>
          {message}
        </div>
      )}
      <div className="status-line" style={{ marginTop: 12, gap: 12, flexWrap: 'wrap' }}>
        <div className="card mini">
          <div className="label">Episodes</div>
          <div className="value">{episodes ?? '—'}</div>
        </div>
        <div className="card mini">
          <div className="label">Win rate</div>
          <div className="value">{winRate !== null ? `${(winRate as number * 100).toFixed(1)}%` : '—'}</div>
        </div>
        <div className="card mini">
          <div className="label">Loss</div>
          <div className="value">{loss !== null ? (loss as number).toFixed(3) : '—'}</div>
        </div>
        <div className="card mini">
          <div className="label">Curriculum</div>
          <div className="value">{phase ?? '—'}</div>
        </div>
      </div>
      <div style={{ marginTop: 12 }}>
        <div className="label">Win rate trend</div>
        {metricHistory.length === 0 ? (
          <div className="message warn" style={{ marginTop: 6 }}>No metrics yet.</div>
        ) : (
          <svg width="100%" height="40" viewBox="0 0 100 30" preserveAspectRatio="none">
            <path d={sparklinePath} stroke="var(--accent)" fill="none" strokeWidth="1.5" />
          </svg>
        )}
      </div>
    </div>
  );
}
