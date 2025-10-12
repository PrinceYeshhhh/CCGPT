import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '1m', target: 50 },  // Ramp up to 50 users
    { duration: '3m', target: 100 }, // Stay at 100 users
    { duration: '1m', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'], // 95% of requests must complete below 5s
    http_req_failed: ['rate<0.2'],     // Error rate must be below 20%
  },
};

const BASE_URL = 'http://localhost:8000';

export default function () {
  // High frequency health checks
  let response = http.get(`${BASE_URL}/health`);
  check(response, {
    'health check status is 200': (r) => r.status === 200,
  });

  sleep(0.5);

  // API health check
  response = http.get(`${BASE_URL}/api/v1/health`);
  check(response, {
    'API health check status is 200': (r) => r.status === 200,
  });

  sleep(0.5);

  // Ready check
  response = http.get(`${BASE_URL}/ready`);
  check(response, {
    'ready check status is 200': (r) => r.status === 200,
  });

  sleep(0.5);

  // Stress authentication test
  const authPayload = JSON.stringify({
    email: `stress${Math.floor(Math.random() * 100000)}@example.com`,
    password: 'StressTest123!',
    full_name: `Stress User ${Math.floor(Math.random() * 100000)}`,
  });

  const authParams = {
    headers: { 'Content-Type': 'application/json' },
  };

  response = http.post(`${BASE_URL}/api/v1/auth/register`, authPayload, authParams);
  check(response, {
    'auth register status is acceptable': (r) => [200, 201, 400, 409].includes(r.status),
  });

  sleep(1);
}