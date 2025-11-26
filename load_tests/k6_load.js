import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,
  duration: '30s',
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  const start = http.post(`${BASE_URL}/api/games`);
  check(start, { 'start 200/503': (r) => [200, 503].includes(r.status) });
  if (start.status !== 200) {
    sleep(1);
    return;
  }
  const gameId = start.json('game_id');
  const move = http.post(`${BASE_URL}/api/games/${gameId}/moves`, JSON.stringify({ x: 0, y: 0 }), {
    headers: { 'Content-Type': 'application/json' },
  });
  check(move, { 'move 200/409/429/503': (r) => [200, 409, 429, 503].includes(r.status) });
  sleep(1);
}
