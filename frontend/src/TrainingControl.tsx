import { useEffect, useState } from 'react';
import YAML from 'js-yaml';
import { cancelTraining, getTraining, mapError, startTraining } from './api';
import type { TrainingRunResponse, TrainingRunStatus } from './types';

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

  useEffect(() => {
    setStatus(run?.status ?? null);
  }, [run]);

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
    </div>
  );
}
