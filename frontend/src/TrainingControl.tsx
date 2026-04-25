import { useEffect, useMemo, useState } from 'react';
import YAML from 'js-yaml';
import { cancelTraining, getTraining, getTrainingMetrics, mapError, startTraining } from './api';
import type { TrainingMetricsResponse, TrainingRunResponse, TrainingRunStatus } from './types';

const DEFAULT_CURRICULUM = {
  version: 'v1',
  phases: [
    {
      id: 'bootcamp',
      name: 'Boot Camp',
      description: 'Warm-up vs simple scripted opponents.',
      gating: { min_episodes: 0, min_win_rate: 0.0 },
      opponents: [
        { opponent: 'random', weight: 0.7 },
        { opponent: 'hunt_target', weight: 0.3 },
      ],
    },
    {
      id: 'skirmish',
      name: 'Skirmish Control',
      description: 'Mix of hunt_target and probability bot.',
      gating: { min_episodes: 2000, min_rounds: 1, min_win_rate: 0.55 },
      opponents: [
        { opponent: 'hunt_target', weight: 0.5 },
        { opponent: 'probability', weight: 0.5 },
      ],
    },
  ],
};

interface Props {
  onError?: (msg: string) => void;
}

const DEFAULT_CONFIG = {
  train: {
    output_dir: './artifacts',
    artifact_name: 'dqn_agent.npz',
    device: 'cpu' as const,
    version: 'dqn-curriculum',
    log_interval: 10,
    epochs: 100,
    seed: 42,
    lr: 0.01,
    epsilon: 0.2,
    epsilon_decay: 0.99,
    reward_step_base: -0.05,
    reward_step_decay: 0,
    reward_step_cap: -0.5,
    reward_hit: 1,
    reward_miss: 0,
    reward_sink_mult: 1,
    reward_win_max: 5,
    reward_win_decay_k: 82,
    reward_loss: -10,
    reward_perfect_move: 17,
  },
  dqn: {
    model: 'cnn' as const,
    conv_channels: [16, 32] as [number, number],
    use_dueling: true,
    double_dqn: true,
    use_huber: true,
    huber_delta: 1,
    clip_norm: 1,
    lr: 0.0003,
    target_update: 200,
    epsilon_start: 1,
    epsilon_end: 0.05,
    epsilon_min: 0.05,
    epsilon_decay: 8000,
    buffer_size: 20000,
    batch_size: 64,
    warmup_steps: 1000,
    hidden: 256,
    gamma: 0.99,
  },
  selfplay: {
    chunk_episodes: 500,
    max_rounds: 200000,
    max_episodes: null as number | null,
    max_duration_sec: null as number | null,
    snapshot_interval: 5000,
    baseline_games: 100,
    baseline_threshold: 0.99,
    baseline_workers: 4,
    eval_games: 200,
    eval_threshold: 0.8,
    eval_workers: 4,
    loss_penalty: 5,
    rollout_workers: 4,
    batch_size: 1,
    move_gate: null as number | null,
    progress_log: true,
    metrics_path: null as string | null,
    progress_path: null as string | null,
  },
};

export function TrainingControl({ onError }: Props) {
  const [epochs, setEpochs] = useState(100);
  const [seed, setSeed] = useState(42);
  const [boardSize, setBoardSize] = useState(10);
  const [learningRate, setLearningRate] = useState(0.01);
  const [epsilon, setEpsilon] = useState(0.2);
  const [epsilonDecay, setEpsilonDecay] = useState(0.99);
  const [outputDir, setOutputDir] = useState('./artifacts');
  const [artifactName, setArtifactName] = useState('dqn_agent.npz');
  const [device, setDevice] = useState<'cpu' | 'cuda'>('cpu');
  const [version, setVersion] = useState('dqn-curriculum');
  const [logInterval, setLogInterval] = useState(10);
  const [rewardStepBase, setRewardStepBase] = useState(-0.05);
  const [rewardStepDecay, setRewardStepDecay] = useState(0);
  const [rewardStepCap, setRewardStepCap] = useState(-0.5);
  const [rewardHit, setRewardHit] = useState(1);
  const [rewardMiss, setRewardMiss] = useState(0);
  const [rewardSinkMult, setRewardSinkMult] = useState(1);
  const [rewardWinMax, setRewardWinMax] = useState(5);
  const [rewardWinDecayK, setRewardWinDecayK] = useState(82);
  const [rewardLoss, setRewardLoss] = useState(-10);
  const [rewardPerfectMove, setRewardPerfectMove] = useState(17);
  // DQN
  const [dqnModel, setDqnModel] = useState<'mlp' | 'cnn'>('cnn');
  const [convChannels1, setConvChannels1] = useState(16);
  const [convChannels2, setConvChannels2] = useState(32);
  const [useDueling, setUseDueling] = useState(true);
  const [doubleDqn, setDoubleDqn] = useState(true);
  const [useHuber, setUseHuber] = useState(true);
  const [huberDelta, setHuberDelta] = useState(1);
  const [clipNorm, setClipNorm] = useState(1);
  const [dqnLr, setDqnLr] = useState(0.0003);
  const [targetUpdate, setTargetUpdate] = useState(200);
  const [epsilonStart, setEpsilonStart] = useState(1);
  const [epsilonEnd, setEpsilonEnd] = useState(0.05);
  const [epsilonMin, setEpsilonMin] = useState(0.05);
  const [epsilonDecaySteps, setEpsilonDecaySteps] = useState(8000);
  const [bufferSize, setBufferSize] = useState(20000);
  const [batchSize, setBatchSize] = useState(64);
  const [warmupSteps, setWarmupSteps] = useState(1000);
  const [hidden, setHidden] = useState(256);
  const [gamma, setGamma] = useState(0.99);
  // Self-play
  const [chunkEpisodes, setChunkEpisodes] = useState(500);
  const [maxRounds, setMaxRounds] = useState(200000);
  const [maxEpisodes, setMaxEpisodes] = useState<number | ''>('');
  const [maxDuration, setMaxDuration] = useState<number | ''>('');
  const [snapshotInterval, setSnapshotInterval] = useState(5000);
  const [baselineGames, setBaselineGames] = useState(100);
  const [baselineThreshold, setBaselineThreshold] = useState(0.99);
  const [baselineWorkers, setBaselineWorkers] = useState(4);
  const [evalGames, setEvalGames] = useState(200);
  const [evalThreshold, setEvalThreshold] = useState(0.8);
  const [evalWorkers, setEvalWorkers] = useState(4);
  const [lossPenalty, setLossPenalty] = useState(5);
  const [rolloutWorkers, setRolloutWorkers] = useState(4);
  const [selfplayBatchSize, setSelfplayBatchSize] = useState(1);
  const [moveGate, setMoveGate] = useState<number | ''>('');
  const [progressLog, setProgressLog] = useState(true);
  const [metricsPath, setMetricsPath] = useState('');
  const [progressPath, setProgressPath] = useState('');
  const [curriculum, setCurriculum] = useState<any>(DEFAULT_CURRICULUM);
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

  useEffect(() => {
    applyConfig(DEFAULT_CONFIG);
    setCurriculum(DEFAULT_CURRICULUM);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function applyConfig(config: any) {
    const train = config.train || {};
    const dqn = config.dqn || {};
    const selfplay = config.selfplay || {};
    const num = (val: unknown) => (typeof val === 'number' ? val : Number(val));
    const safe = (value: number | null | undefined, fallback: number) =>
      Number.isFinite(value) ? Number(value) : fallback;
    setOutputDir((train.output_dir as string) || outputDir);
    setArtifactName((train.artifact_name as string) || artifactName);
    setDevice((train.device as 'cpu' | 'cuda') || device);
    setVersion((train.version as string) || version);
    setLogInterval(safe(num(train.log_interval), logInterval));
    setEpochs(safe(num(train.epochs), epochs));
    setSeed(safe(num(train.seed), seed));
    setBoardSize(10);
    setLearningRate(safe(num(train.lr), learningRate));
    setEpsilon(safe(num(train.epsilon), epsilon));
    setEpsilonDecay(safe(num(train.epsilon_decay), epsilonDecay));
    setRewardStepBase(safe(num(train.reward_step_base), rewardStepBase));
    setRewardStepDecay(safe(num(train.reward_step_decay), rewardStepDecay));
    setRewardStepCap(safe(num(train.reward_step_cap), rewardStepCap));
    setRewardHit(safe(num(train.reward_hit), rewardHit));
    setRewardMiss(safe(num(train.reward_miss), rewardMiss));
    setRewardSinkMult(safe(num(train.reward_sink_mult), rewardSinkMult));
    setRewardWinMax(safe(num(train.reward_win_max), rewardWinMax));
    setRewardWinDecayK(safe(num(train.reward_win_decay_k), rewardWinDecayK));
    setRewardLoss(safe(num(train.reward_loss), rewardLoss));
    setRewardPerfectMove(safe(num(train.reward_perfect_move), rewardPerfectMove));

    setDqnModel((dqn.model as 'mlp' | 'cnn') || dqnModel);
    if (Array.isArray(dqn.conv_channels) && dqn.conv_channels.length === 2) {
      setConvChannels1(Number(dqn.conv_channels[0]) || convChannels1);
      setConvChannels2(Number(dqn.conv_channels[1]) || convChannels2);
    }
    setUseDueling(typeof dqn.use_dueling === 'boolean' ? dqn.use_dueling : useDueling);
    setDoubleDqn(typeof dqn.double_dqn === 'boolean' ? dqn.double_dqn : doubleDqn);
    setUseHuber(typeof dqn.use_huber === 'boolean' ? dqn.use_huber : useHuber);
    setHuberDelta(safe(num(dqn.huber_delta), huberDelta));
    setClipNorm(safe(num(dqn.clip_norm), clipNorm));
    setDqnLr(safe(num(dqn.lr), dqnLr));
    setTargetUpdate(safe(num(dqn.target_update), targetUpdate));
    setEpsilonStart(safe(num(dqn.epsilon_start), epsilonStart));
    setEpsilonEnd(safe(num(dqn.epsilon_end), epsilonEnd));
    setEpsilonMin(safe(num(dqn.epsilon_min), epsilonMin));
    setEpsilonDecaySteps(safe(num(dqn.epsilon_decay), epsilonDecaySteps));
    setBufferSize(safe(num(dqn.buffer_size), bufferSize));
    setBatchSize(safe(num(dqn.batch_size), batchSize));
    setWarmupSteps(safe(num(dqn.warmup_steps), warmupSteps));
    setHidden(safe(num(dqn.hidden), hidden));
    setGamma(safe(num(dqn.gamma), gamma));

    setChunkEpisodes(safe(num(selfplay.chunk_episodes), chunkEpisodes));
    setMaxRounds(safe(num(selfplay.max_rounds), maxRounds));
    setMaxEpisodes(
      Number.isFinite(num(selfplay.max_episodes)) ? Number(selfplay.max_episodes) : ''
    );
    setMaxDuration(
      Number.isFinite(num(selfplay.max_duration_sec)) ? Number(selfplay.max_duration_sec) : ''
    );
    setSnapshotInterval(safe(num(selfplay.snapshot_interval), snapshotInterval));
    setBaselineGames(safe(num(selfplay.baseline_games), baselineGames));
    setBaselineThreshold(safe(num(selfplay.baseline_threshold), baselineThreshold));
    setBaselineWorkers(safe(num(selfplay.baseline_workers), baselineWorkers));
    setEvalGames(safe(num(selfplay.eval_games), evalGames));
    setEvalThreshold(safe(num(selfplay.eval_threshold), evalThreshold));
    setEvalWorkers(safe(num(selfplay.eval_workers), evalWorkers));
    setLossPenalty(safe(num(selfplay.loss_penalty), lossPenalty));
    setRolloutWorkers(safe(num(selfplay.rollout_workers), rolloutWorkers));
    setSelfplayBatchSize(safe(num(selfplay.batch_size), selfplayBatchSize));
    const parsedMoveGate = num(selfplay.move_gate);
    setMoveGate(Number.isFinite(parsedMoveGate) ? Number(parsedMoveGate) : '');
    setProgressLog(
      typeof selfplay.progress_log === 'boolean' ? selfplay.progress_log : progressLog
    );
    setMetricsPath((selfplay.metrics_path as string) || '');
    setProgressPath((selfplay.progress_path as string) || '');
  }

  function buildConfig() {
    return {
      train: {
        output_dir: outputDir,
        artifact_name: artifactName,
        device,
        version,
        log_interval: Number(logInterval),
        epochs: Number(epochs),
        seed: Number(seed),
        lr: Number(learningRate),
        epsilon: Number(epsilon),
        epsilon_decay: Number(epsilonDecay),
        reward_step_base: Number(rewardStepBase),
        reward_step_decay: Number(rewardStepDecay),
        reward_step_cap: Number(rewardStepCap),
        reward_hit: Number(rewardHit),
        reward_miss: Number(rewardMiss),
        reward_sink_mult: Number(rewardSinkMult),
        reward_win_max: Number(rewardWinMax),
        reward_win_decay_k: Number(rewardWinDecayK),
        reward_loss: Number(rewardLoss),
        reward_perfect_move: Number(rewardPerfectMove),
      },
      dqn: {
        model: dqnModel,
        conv_channels: [Number(convChannels1), Number(convChannels2)],
        use_dueling: useDueling,
        double_dqn: doubleDqn,
        use_huber: useHuber,
        huber_delta: Number(huberDelta),
        clip_norm: Number(clipNorm),
        lr: Number(dqnLr),
        target_update: Number(targetUpdate),
        epsilon_start: Number(epsilonStart),
        epsilon_end: Number(epsilonEnd),
        epsilon_min: Number(epsilonMin),
        epsilon_decay: Number(epsilonDecaySteps),
        buffer_size: Number(bufferSize),
        batch_size: Number(batchSize),
        warmup_steps: Number(warmupSteps),
        hidden: Number(hidden),
        gamma: Number(gamma),
      },
      selfplay: {
        chunk_episodes: Number(chunkEpisodes),
        max_rounds: Number(maxRounds),
        max_episodes: maxEpisodes === '' ? null : Number(maxEpisodes),
        max_duration_sec: maxDuration === '' ? null : Number(maxDuration),
        snapshot_interval: Number(snapshotInterval),
        baseline_games: Number(baselineGames),
        baseline_threshold: Number(baselineThreshold),
        baseline_workers: Number(baselineWorkers),
        eval_games: Number(evalGames),
        eval_threshold: Number(evalThreshold),
        eval_workers: Number(evalWorkers),
        loss_penalty: Number(lossPenalty),
        rollout_workers: Number(rolloutWorkers),
        batch_size: Number(selfplayBatchSize),
        move_gate: moveGate === '' ? null : Number(moveGate),
        progress_log: progressLog,
        metrics_path: metricsPath || null,
        progress_path: progressPath || null,
      },
    };
  }

  function applyYaml(text: string) {
    try {
      const parsed = YAML.load(text);
      if (!parsed || typeof parsed !== 'object' || !('train' in (parsed as any))) {
        throw new Error('YAML must include a top-level "train" section.');
      }
      applyConfig(parsed as any);
    } catch (err: any) {
      const detail = err?.message;
      const msg = detail ? `Invalid YAML: ${detail}` : 'Invalid YAML';
      setMessage(msg);
      onError?.(msg);
    }
  }

  async function handleStart() {
    setLoading(true);
    setMessage(null);
    const config = buildConfig();
    (config as any).curriculum = curriculum;
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
    applyYaml(text);
  }

  const statusBadge = status ? status.toUpperCase() : 'Idle';
  const winRate = metrics?.win_rate ?? null;
  const episodes = metrics?.episodes ?? null;
  const loss = metrics?.loss ?? null;
  const phase = metrics?.curriculum_phase ?? null;
  const startedAt =
    run?.created_at && !Number.isNaN(run.created_at)
      ? new Date(run.created_at * 1000).toLocaleString('en-GB', {
          hour: '2-digit',
          minute: '2-digit',
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
        })
      : null;
  const updatedAt =
    run?.updated_at && !Number.isNaN(run.updated_at)
      ? new Date(run.updated_at * 1000).toLocaleString('en-GB', {
          hour: '2-digit',
          minute: '2-digit',
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
        })
      : null;

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
      <p style={{ marginBottom: 12, color: 'var(--muted)' }}>
        Configure and launch training runs here. The form builds the full YAML config for the
        trainer (data, DQN, self-play) without editing files by hand. To use it: (1) adjust any
        fields you need, or click “Reset to defaults” to restore the bundled mini-run settings; (2)
        optionally upload an existing YAML to prefill the form (the uploaded values apply only to
        this session and do not overwrite files); (3) click “Start training” to launch a run with
        the current form values. Each run writes a timestamped model artifact and metrics to the
        configured output directory. You can also edit the curriculum YAML below to change phases
        and opponent mixes per run.
      </p>
      <div
        className="status-line"
        style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}
      >
        <strong>Training Control</strong>
        <span className="badge">{statusBadge}</span>
      </div>
      <div className="card" style={{ marginTop: 12 }}>
        <strong>Curriculum (phases/opponents)</strong>
        <p className="label" style={{ color: 'var(--muted)', marginTop: 6 }}>
          Configure curriculum phases: gating requirements and opponent mixes. Defaults match the
          bundled curriculum; changes apply only to this run.
        </p>
        <div style={{ display: 'flex', gap: 12, flexDirection: 'column', marginTop: 8 }}>
          {curriculum.phases.map((phase: any, idx: number) => (
            <div key={phase.id} className="card mini" style={{ padding: 12 }}>
              <div className="status-line" style={{ marginBottom: 8, gap: 8, flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', gap: 8 }}>
                  <label className="label" style={{ display: 'flex', flexDirection: 'column' }}>
                    <span>
                      <code>id</code>
                    </span>
                    <input
                      type="text"
                      value={phase.id}
                      onChange={(e) =>
                        setCurriculum((prev: any) => {
                          const next = { ...prev, phases: [...prev.phases] };
                          next.phases[idx] = { ...next.phases[idx], id: e.target.value };
                          return next;
                        })
                      }
                    />
                  </label>
                  <label className="label" style={{ display: 'flex', flexDirection: 'column' }}>
                    <span>
                      <code>name</code>
                    </span>
                    <input
                      type="text"
                      value={phase.name}
                      onChange={(e) =>
                        setCurriculum((prev: any) => {
                          const next = { ...prev, phases: [...prev.phases] };
                          next.phases[idx] = { ...next.phases[idx], name: e.target.value };
                          return next;
                        })
                      }
                    />
                  </label>
                </div>
                <button
                  className="button secondary"
                  type="button"
                  onClick={() =>
                    setCurriculum((prev: any) => {
                      const phases = prev.phases.filter((_: any, i: number) => i !== idx);
                      return { ...prev, phases };
                    })
                  }
                  disabled={curriculum.phases.length <= 1}
                >
                  Remove phase
                </button>
              </div>
              <label className="label" style={{ display: 'flex', flexDirection: 'column' }}>
                <span>
                  <code>description</code>
                </span>
                <input
                  type="text"
                  value={phase.description || ''}
                  onChange={(e) =>
                    setCurriculum((prev: any) => {
                      const next = { ...prev, phases: [...prev.phases] };
                      next.phases[idx] = { ...next.phases[idx], description: e.target.value };
                      return next;
                    })
                  }
                />
              </label>
              <div
                className="form-grid"
                style={{
                  display: 'grid',
                  gap: 8,
                  gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
                }}
              >
                {(['min_episodes', 'min_rounds', 'min_win_rate'] as const).map((field) => (
                  <label
                    key={field}
                    className="label"
                    style={{ display: 'flex', flexDirection: 'column', gap: 4 }}
                  >
                    <span>
                      <code>{field}</code>
                    </span>
                    <input
                      type="number"
                      step={field === 'min_win_rate' ? 0.01 : 1}
                      value={phase.gating?.[field] ?? ''}
                      onChange={(e) =>
                        setCurriculum((prev: any) => {
                          const next = { ...prev, phases: [...prev.phases] };
                          const gating = { ...(next.phases[idx].gating || {}) };
                          gating[field] =
                            e.target.value === ''
                              ? undefined
                              : field === 'min_win_rate'
                                ? Number(e.target.value)
                                : parseInt(e.target.value, 10);
                          next.phases[idx] = { ...next.phases[idx], gating };
                          return next;
                        })
                      }
                    />
                  </label>
                ))}
              </div>
              <div style={{ marginTop: 8 }}>
                <div className="status-line" style={{ marginBottom: 4, gap: 8 }}>
                  <strong>Opponents</strong>
                  <button
                    className="button secondary"
                    type="button"
                    onClick={() =>
                      setCurriculum((prev: any) => {
                        const next = { ...prev, phases: [...prev.phases] };
                        const opponents = [...(next.phases[idx].opponents || [])];
                        opponents.push({ opponent: 'random', weight: 0.5 });
                        next.phases[idx] = { ...next.phases[idx], opponents };
                        return next;
                      })
                    }
                  >
                    Add opponent
                  </button>
                </div>
                {(phase.opponents || []).map((op: any, opIdx: number) => (
                  <div
                    key={`${phase.id}-op-${opIdx}`}
                    style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}
                  >
                    <select
                      value={op.opponent}
                      onChange={(e) =>
                        setCurriculum((prev: any) => {
                          const next = { ...prev, phases: [...prev.phases] };
                          const opponents = [...(next.phases[idx].opponents || [])];
                          opponents[opIdx] = { ...opponents[opIdx], opponent: e.target.value };
                          next.phases[idx] = { ...next.phases[idx], opponents };
                          return next;
                        })
                      }
                    >
                      <option value="random">random</option>
                      <option value="hunt_target">hunt_target</option>
                      <option value="probability">probability</option>
                      <option value="self">self</option>
                    </select>
                    <input
                      type="number"
                      step={0.1}
                      value={op.weight}
                      onChange={(e) =>
                        setCurriculum((prev: any) => {
                          const next = { ...prev, phases: [...prev.phases] };
                          const opponents = [...(next.phases[idx].opponents || [])];
                          opponents[opIdx] = {
                            ...opponents[opIdx],
                            weight: Number(e.target.value),
                          };
                          next.phases[idx] = { ...next.phases[idx], opponents };
                          return next;
                        })
                      }
                    />
                    <button
                      className="button secondary"
                      type="button"
                      onClick={() =>
                        setCurriculum((prev: any) => {
                          const next = { ...prev, phases: [...prev.phases] };
                          const opponents = (next.phases[idx].opponents || []).filter(
                            (_: any, i: number) => i !== opIdx
                          );
                          next.phases[idx] = { ...next.phases[idx], opponents };
                          return next;
                        })
                      }
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ))}
          <button
            className="button secondary"
            type="button"
            onClick={() =>
              setCurriculum((prev: any) => ({
                ...prev,
                phases: [
                  ...prev.phases,
                  {
                    id: `phase${prev.phases.length + 1}`,
                    name: 'New phase',
                    description: '',
                    gating: { min_episodes: 0 },
                    opponents: [{ opponent: 'random', weight: 1 }],
                  },
                ],
              }))
            }
          >
            Add phase
          </button>
          <button
            className="button secondary"
            type="button"
            onClick={() => setCurriculum(DEFAULT_CURRICULUM)}
          >
            Reset curriculum to defaults
          </button>
        </div>
      </div>
      <label className="status-line" style={{ gap: 8, marginBottom: 8 }}>
        <input type="file" accept=".yaml,.yml,text/yaml" onChange={handleUpload} />
        <span style={{ color: 'var(--muted)' }}>Upload YAML to preload config</span>
      </label>
      <div
        className="form-grid"
        style={{ display: 'grid', gap: 8, gridTemplateColumns: '1fr 1fr' }}
      >
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>epochs</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Number of training episodes; more improves quality but costs time.
          </span>
          <input
            type="number"
            value={epochs}
            min={1}
            onChange={(e) => setEpochs(Number(e.target.value))}
          />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>seed</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            RNG seed for reproducibility of training runs.
          </span>
          <input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>output_dir</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Where to write artifacts, metrics, and snapshots.
          </span>
          <input type="text" value={outputDir} onChange={(e) => setOutputDir(e.target.value)} />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>artifact_name</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Base filename for the main artifact (timestamp added automatically).
          </span>
          <input
            type="text"
            value={artifactName}
            onChange={(e) => setArtifactName(e.target.value)}
          />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>device</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Target device for training/runtime (cpu or cuda).
          </span>
          <select value={device} onChange={(e) => setDevice(e.target.value as 'cpu' | 'cuda')}>
            <option value="cpu">CPU</option>
            <option value="cuda">CUDA</option>
          </select>
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>version</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Version tag stored in manifest for traceability.
          </span>
          <input type="text" value={version} onChange={(e) => setVersion(e.target.value)} />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>board_size</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>Board is fixed to 10x10.</span>
          <input type="number" value={10} readOnly />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>lr</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Learning rate for the tabular Q-learner (higher learns faster but can destabilize).
          </span>
          <input
            type="number"
            step="0.001"
            value={learningRate}
            onChange={(e) => setLearningRate(Number(e.target.value))}
          />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>log_interval</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Episodes between progress logs during training.
          </span>
          <input
            type="number"
            value={logInterval}
            min={1}
            onChange={(e) => setLogInterval(Number(e.target.value))}
          />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>epsilon</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Starting exploration rate for the tabular learner.
          </span>
          <input
            type="number"
            step="0.01"
            value={epsilon}
            onChange={(e) => setEpsilon(Number(e.target.value))}
          />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>epsilon_decay</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Multiplicative decay per episode for exploration rate.
          </span>
          <input
            type="number"
            step="0.01"
            value={epsilonDecay}
            onChange={(e) => setEpsilonDecay(Number(e.target.value))}
          />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>reward_step_base</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Per-move penalty to encourage faster wins.
          </span>
          <input
            type="number"
            step="0.01"
            value={rewardStepBase}
            onChange={(e) => setRewardStepBase(Number(e.target.value))}
          />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>reward_step_decay</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Decay applied to the step penalty over time.
          </span>
          <input
            type="number"
            step="0.01"
            value={rewardStepDecay}
            onChange={(e) => setRewardStepDecay(Number(e.target.value))}
          />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>reward_step_cap</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Minimum step penalty when decay is applied.
          </span>
          <input
            type="number"
            step="0.01"
            value={rewardStepCap}
            onChange={(e) => setRewardStepCap(Number(e.target.value))}
          />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>reward_hit</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>Reward for hitting a ship.</span>
          <input
            type="number"
            step="0.1"
            value={rewardHit}
            onChange={(e) => setRewardHit(Number(e.target.value))}
          />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>reward_miss</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>Reward/penalty for a miss.</span>
          <input
            type="number"
            step="0.1"
            value={rewardMiss}
            onChange={(e) => setRewardMiss(Number(e.target.value))}
          />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>reward_sink_mult</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Multiplier for sinking a ship (bonus on top of hit).
          </span>
          <input
            type="number"
            step="0.1"
            value={rewardSinkMult}
            onChange={(e) => setRewardSinkMult(Number(e.target.value))}
          />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>reward_win_max</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Maximum reward granted for winning.
          </span>
          <input
            type="number"
            step="0.1"
            value={rewardWinMax}
            onChange={(e) => setRewardWinMax(Number(e.target.value))}
          />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>reward_win_decay_k</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Controls win reward decay curve; higher keeps reward higher longer.
          </span>
          <input
            type="number"
            step="0.1"
            value={rewardWinDecayK}
            onChange={(e) => setRewardWinDecayK(Number(e.target.value))}
          />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>reward_loss</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Penalty applied when the agent loses.
          </span>
          <input
            type="number"
            step="0.1"
            value={rewardLoss}
            onChange={(e) => setRewardLoss(Number(e.target.value))}
          />
        </label>
        <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>
            <code>reward_perfect_move</code>
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Bonus for finishing in the minimal number of moves.
          </span>
          <input
            type="number"
            value={rewardPerfectMove}
            onChange={(e) => setRewardPerfectMove(Number(e.target.value))}
          />
        </label>
      </div>
      <div className="card" style={{ marginTop: 12 }}>
        <strong>DQN settings</strong>
        <div
          className="form-grid"
          style={{ display: 'grid', gap: 8, gridTemplateColumns: '1fr 1fr' }}
        >
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>model</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Network architecture to use for Q-values.
            </span>
            <select value={dqnModel} onChange={(e) => setDqnModel(e.target.value as 'mlp' | 'cnn')}>
              <option value="mlp">MLP</option>
              <option value="cnn">CNN</option>
            </select>
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>conv_channels</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Filters per CNN layer (only used when model=cnn).
            </span>
            <div style={{ display: 'flex', gap: 6 }}>
              <input
                type="number"
                value={convChannels1}
                min={1}
                onChange={(e) => setConvChannels1(Number(e.target.value))}
              />
              <input
                type="number"
                value={convChannels2}
                min={1}
                onChange={(e) => setConvChannels2(Number(e.target.value))}
              />
            </div>
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>use_dueling</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Enable dueling heads to stabilize value estimation.
            </span>
            <select
              value={useDueling ? 'yes' : 'no'}
              onChange={(e) => setUseDueling(e.target.value === 'yes')}
            >
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>double_dqn</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Use Double DQN to reduce overestimation bias.
            </span>
            <select
              value={doubleDqn ? 'yes' : 'no'}
              onChange={(e) => setDoubleDqn(e.target.value === 'yes')}
            >
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>use_huber</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Switch loss to Huber (better stability than MSE).
            </span>
            <select
              value={useHuber ? 'yes' : 'no'}
              onChange={(e) => setUseHuber(e.target.value === 'yes')}
            >
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>huber_delta</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Transition point between L1/L2 in Huber loss.
            </span>
            <input
              type="number"
              step="0.1"
              value={huberDelta}
              onChange={(e) => setHuberDelta(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>clip_norm</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Gradient norm cap; prevents exploding gradients.
            </span>
            <input
              type="number"
              step="0.1"
              value={clipNorm}
              onChange={(e) => setClipNorm(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>dqn.lr</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Optimizer learning rate for the DQN.
            </span>
            <input
              type="number"
              step="0.0001"
              value={dqnLr}
              onChange={(e) => setDqnLr(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>target_update</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Steps between target network syncs.
            </span>
            <input
              type="number"
              value={targetUpdate}
              onChange={(e) => setTargetUpdate(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>epsilon_start</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Initial exploration rate for DQN.
            </span>
            <input
              type="number"
              step="0.01"
              value={epsilonStart}
              onChange={(e) => setEpsilonStart(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>epsilon_end</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Final exploration floor for DQN schedule.
            </span>
            <input
              type="number"
              step="0.01"
              value={epsilonEnd}
              onChange={(e) => setEpsilonEnd(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>epsilon_min</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Hard minimum epsilon allowed.
            </span>
            <input
              type="number"
              step="0.01"
              value={epsilonMin}
              onChange={(e) => setEpsilonMin(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>epsilon_decay</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Steps over which epsilon anneals from start to end.
            </span>
            <input
              type="number"
              value={epsilonDecaySteps}
              onChange={(e) => setEpsilonDecaySteps(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>buffer_size</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Replay buffer capacity; larger improves diversity but uses RAM.
            </span>
            <input
              type="number"
              value={bufferSize}
              onChange={(e) => setBufferSize(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>batch_size</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Mini-batch size for DQN updates.
            </span>
            <input
              type="number"
              value={batchSize}
              onChange={(e) => setBatchSize(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>warmup_steps</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Steps before training starts to fill the buffer.
            </span>
            <input
              type="number"
              value={warmupSteps}
              onChange={(e) => setWarmupSteps(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>hidden</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Hidden layer width; larger can improve capacity at compute cost.
            </span>
            <input
              type="number"
              value={hidden}
              onChange={(e) => setHidden(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>gamma</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Discount factor for future rewards (closer to 1 values long-term outcomes).
            </span>
            <input
              type="number"
              step="0.01"
              value={gamma}
              onChange={(e) => setGamma(Number(e.target.value))}
            />
          </label>
        </div>
      </div>
      <div className="card" style={{ marginTop: 12 }}>
        <strong>Self-play settings</strong>
        <div
          className="form-grid"
          style={{ display: 'grid', gap: 8, gridTemplateColumns: '1fr 1fr' }}
        >
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>chunk_episodes</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Episodes per training chunk before evaluation.
            </span>
            <input
              type="number"
              value={chunkEpisodes}
              onChange={(e) => setChunkEpisodes(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>max_rounds</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Number of training rounds (chunks) to run.
            </span>
            <input
              type="number"
              value={maxRounds}
              onChange={(e) => setMaxRounds(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>max_episodes</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Hard cap on total episodes (optional).
            </span>
            <input
              type="number"
              value={maxEpisodes}
              onChange={(e) => setMaxEpisodes(e.target.value === '' ? '' : Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>max_duration_sec</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Optional wall-clock cap for training run.
            </span>
            <input
              type="number"
              value={maxDuration}
              onChange={(e) => setMaxDuration(e.target.value === '' ? '' : Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>snapshot_interval</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Episodes between policy snapshots.
            </span>
            <input
              type="number"
              value={snapshotInterval}
              onChange={(e) => setSnapshotInterval(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>baseline_games</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Number of baseline eval games per round.
            </span>
            <input
              type="number"
              value={baselineGames}
              onChange={(e) => setBaselineGames(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>baseline_threshold</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Win rate required to pass baseline gate.
            </span>
            <input
              type="number"
              step="0.01"
              value={baselineThreshold}
              onChange={(e) => setBaselineThreshold(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>baseline_workers</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Parallel workers for baseline eval.
            </span>
            <input
              type="number"
              value={baselineWorkers}
              onChange={(e) => setBaselineWorkers(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>eval_games</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Number of self-play eval games per round.
            </span>
            <input
              type="number"
              value={evalGames}
              onChange={(e) => setEvalGames(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>eval_threshold</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Win rate needed to progress to next curriculum phase.
            </span>
            <input
              type="number"
              step="0.01"
              value={evalThreshold}
              onChange={(e) => setEvalThreshold(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>eval_workers</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Parallel workers for self-play eval.
            </span>
            <input
              type="number"
              value={evalWorkers}
              onChange={(e) => setEvalWorkers(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>loss_penalty</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Penalty applied for losing during self-play eval.
            </span>
            <input
              type="number"
              step="0.1"
              value={lossPenalty}
              onChange={(e) => setLossPenalty(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>rollout_workers</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Parallel workers for self-play rollouts.
            </span>
            <input
              type="number"
              value={rolloutWorkers}
              onChange={(e) => setRolloutWorkers(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>batch_size</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Number of parallel envs per rollout batch.
            </span>
            <input
              type="number"
              value={selfplayBatchSize}
              onChange={(e) => setSelfplayBatchSize(Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>move_gate</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Optional gate on moves (e.g., confidence threshold).
            </span>
            <input
              type="number"
              value={moveGate}
              onChange={(e) => setMoveGate(e.target.value === '' ? '' : Number(e.target.value))}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>progress_log</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Whether to emit progress JSONL during training.
            </span>
            <select
              value={progressLog ? 'yes' : 'no'}
              onChange={(e) => setProgressLog(e.target.value === 'yes')}
            >
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>metrics_path</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Override path for self-play metrics CSV.
            </span>
            <input
              type="text"
              value={metricsPath}
              onChange={(e) => setMetricsPath(e.target.value)}
            />
          </label>
          <label className="label" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span>
              <code>progress_path</code>
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              Override path for progress JSONL logs.
            </span>
            <input
              type="text"
              value={progressPath}
              onChange={(e) => setProgressPath(e.target.value)}
            />
          </label>
        </div>
      </div>
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
        <button className="button secondary" onClick={() => applyConfig(DEFAULT_CONFIG)}>
          Reset to defaults
        </button>
        {run && (
          <span style={{ color: 'var(--muted)', fontSize: 13 }}>
            Run ID: <code>{run.run_id}</code>
          </span>
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
          <div className="value">
            {episodes !== null && episodes !== undefined ? `${episodes}/${epochs}` : `0/${epochs}`}
          </div>
        </div>
        <div className="card mini">
          <div className="label">Win rate</div>
          <div className="value">
            {winRate !== null ? `${((winRate as number) * 100).toFixed(1)}%` : '—'}
          </div>
        </div>
        <div className="card mini">
          <div className="label">Loss</div>
          <div className="value">{loss !== null ? (loss as number).toFixed(3) : '—'}</div>
        </div>
        <div className="card mini">
          <div className="label">Curriculum</div>
          <div className="value">{phase ?? '—'}</div>
        </div>
        <div className="card mini">
          <div className="label">Started</div>
          <div className="value">{startedAt ?? '—'}</div>
        </div>
        <div className="card mini">
          <div className="label">Last updated</div>
          <div className="value">{updatedAt ?? '—'}</div>
        </div>
      </div>
      <div style={{ marginTop: 12 }}>
        <div className="label">Win rate trend</div>
        {metricHistory.length === 0 ? (
          <div className="message warn" style={{ marginTop: 6 }}>
            No metrics yet.
          </div>
        ) : (
          <svg width="100%" height="40" viewBox="0 0 100 30" preserveAspectRatio="none">
            <path d={sparklinePath} stroke="var(--accent)" fill="none" strokeWidth="1.5" />
          </svg>
        )}
      </div>
    </div>
  );
}
