import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { TrainingControl } from './TrainingControl';

const runResponse = { run_id: 'r1', status: 'pending', config: {} };
const runningResponse = { run_id: 'r1', status: 'running', config: {} };
const canceledResponse = { run_id: 'r1', status: 'canceled', config: {} };

describe('TrainingControl', () => {
  it('starts a training run with YAML config', async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (url.endsWith('/api/training/runs')) return new Response(JSON.stringify(runResponse), { status: 200 });
      if (url.endsWith('/api/training/runs/r1')) return new Response(JSON.stringify(runningResponse), { status: 200 });
      if (url.endsWith('/api/training/runs/r1/metrics')) return new Response(JSON.stringify({ run_id: 'r1', metrics: { win_rate: 0.5, episodes: 10 } }), { status: 200 });
      return new Response('{}', { status: 200 });
    });
    vi.stubGlobal('fetch', fetchMock as any);

    render(<TrainingControl />);
    fireEvent.click(screen.getByRole('button', { name: /start training/i }));

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(/Started training/));
    expect(fetchMock).toHaveBeenCalled();
  });

  it('handles YAML parse errors', async () => {
    render(<TrainingControl />);
    const textarea = screen.getByLabelText(/Training YAML/i);
    fireEvent.change(textarea, { target: { value: '::bad' } });
    fireEvent.click(screen.getByRole('button', { name: /start training/i }));
    await screen.findByRole('alert');
    expect(screen.getByRole('alert')).toHaveTextContent(/Invalid YAML/);
  });

  it('can cancel a run', async () => {
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/api/training/runs')) return new Response(JSON.stringify(runResponse), { status: 200 });
      if (url.endsWith('/api/training/runs/r1/cancel')) return new Response(JSON.stringify(canceledResponse), { status: 200 });
      if (url.endsWith('/api/training/runs/r1/metrics')) return new Response(JSON.stringify({ run_id: 'r1', metrics: {} }), { status: 200 });
      return new Response(JSON.stringify(runningResponse), { status: 200 });
    });
    vi.stubGlobal('fetch', fetchMock as any);

    render(<TrainingControl />);
    fireEvent.click(screen.getByRole('button', { name: /start training/i }));
    await screen.findByText(/Started training/);

    fireEvent.click(screen.getByRole('button', { name: /Cancel run/i }));
    await screen.findByText(/Canceled training run/);
  });
});
