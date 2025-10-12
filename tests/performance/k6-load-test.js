import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up
    { duration: '5m', target: 20 }, // Stay at 20 users
    { duration: '2m', target: 0 },  // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests must complete below 2s
    http_req_failed: ['rate<0.1'],     // Error rate must be below 10%
  },
};

const BASE_URL = 'http://localhost:8000';

export default function () {
  // Health check
  let response = http.get(`${BASE_URL}/health`);
  check(response, {
    'health check status is 200': (r) => r.status === 200,
  });

  sleep(1);

  // API health check
  response = http.get(`${BASE_URL}/api/v1/health`);
  check(response, {
    'API health check status is 200': (r) => r.status === 200,
  });

  sleep(1);

  // Ready check
  response = http.get(`${BASE_URL}/ready`);
  check(response, {
    'ready check status is 200': (r) => r.status === 200,
  });

  sleep(1);

  // Authentication test
  const authPayload = JSON.stringify({
    email: `test${Math.floor(Math.random() * 10000)}@example.com`,
    password: 'TestPassword123!',
    full_name: `Test User ${Math.floor(Math.random() * 10000)}`,
  });

  const authParams = {
    headers: { 'Content-Type': 'application/json' },
  };

  response = http.post(`${BASE_URL}/api/v1/auth/register`, authPayload, authParams);
  check(response, {
    'auth register status is acceptable': (r) => [200, 201, 400, 409].includes(r.status),
  });

  sleep(2);
}