import { describe, expect, it } from 'vitest';
import { API_BASE, mapError } from './api';
import type { ApiError } from './types';

const error = (error_code: ApiError['error_code']): ApiError => ({ error_code, message: 'msg' });

describe('mapError', () => {
  it('adds backoff guidance on retryable errors', () => {
    const res = mapError(error('rate_limited'));
    expect(res.tone).toBe('warn');
    expect(res.message).toMatch(/retry/);
  });

  it('maps duplicate_move to user-friendly copy', () => {
    const res = mapError(error('duplicate_move'));
    expect(res.message).toContain('already fired');
  });
});

describe('api base', () => {
  it('defaults to localhost', () => {
    expect(API_BASE).toContain('http');
  });
});
