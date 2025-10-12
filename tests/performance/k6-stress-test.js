// K6 Stress Test Script
// Tests system behavior under extreme load conditions

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');
const responseTime = new Trend('response_time');

export let options = {
  stages: [
    { duration: '1m', target: 10 },  // Ramp up to 10 users
    { duration: '2m', target: 50 },  // Ramp up to 50 users
    { duration: '5m', target: 100 }, // Ramp up to 100 users
    { duration: '10m', target: 200 }, // Ramp up to 200 users
    { duration: '5m', target: 100 }, // Ramp down to 100 users
    { duration: '2m', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'], // 95% of requests must complete below 5s
    http_req_failed: ['rate<0.05'],    // Error rate must be below 5%
    error_rate: ['rate<0.05'],         // Custom error rate below 5%
  },
};

const BASE_URL = 'http://localhost:8000';

export default function() {
  // Test data
  const testUser = {
    email: `stress${Math.random().toString(36).substr(2, 9)}@example.com`,
    password: 'StressPassword123!',
    full_name: `Stress User ${Math.random().toString(36).substr(2, 9)}`,
    mobile_phone: `+123456789${Math.floor(Math.random() * 9000) + 1000}`
  };

  let accessToken = null;

  // Health check
  let healthResponse = http.get(`${BASE_URL}/health`);
  check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  errorRate.add(healthResponse.status !== 200);
  responseTime.add(healthResponse.timings.duration);

  // Readiness check
  let readyResponse = http.get(`${BASE_URL}/ready`);
  check(readyResponse, {
    'readiness check status is 200': (r) => r.status === 200,
    'readiness check response time < 2000ms': (r) => r.timings.duration < 2000,
  });
  errorRate.add(readyResponse.status !== 200);
  responseTime.add(readyResponse.timings.duration);

  // User registration (stress test)
  let registerResponse = http.post(`${BASE_URL}/api/v1/auth/register`, JSON.stringify(testUser), {
    headers: { 'Content-Type': 'application/json' },
  });
  check(registerResponse, {
    'registration status is 201': (r) => r.status === 201,
    'registration response time < 5000ms': (r) => r.timings.duration < 5000,
  });
  errorRate.add(registerResponse.status !== 201);
  responseTime.add(registerResponse.timings.duration);

  // User login (stress test)
  let loginResponse = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
    identifier: testUser.email,
    password: testUser.password
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  if (loginResponse.status === 200) {
    accessToken = JSON.parse(loginResponse.body).access_token;
  }

  check(loginResponse, {
    'login status is 200': (r) => r.status === 200,
    'login response time < 3000ms': (r) => r.timings.duration < 3000,
  });
  errorRate.add(loginResponse.status !== 200);
  responseTime.add(loginResponse.timings.duration);

  if (accessToken) {
    // Multiple document uploads (stress test)
    for (let i = 0; i < 3; i++) {
      let uploadResponse = http.post(`${BASE_URL}/api/v1/documents/upload`, {
        file: http.file(`Stress test document ${i} content`, `stress-test-${i}.txt`, 'text/plain')
      }, {
        headers: { 'Authorization': `Bearer ${accessToken}` },
      });
      
      check(uploadResponse, {
        'upload status is 200': (r) => r.status === 200,
        'upload response time < 10000ms': (r) => r.timings.duration < 10000,
      });
      errorRate.add(uploadResponse.status !== 200);
      responseTime.add(uploadResponse.timings.duration);
    }

    // Multiple chat messages (stress test)
    for (let i = 0; i < 5; i++) {
      let chatResponse = http.post(`${BASE_URL}/api/v1/chat/message`, JSON.stringify({
        message: `Stress test message ${i} - ${Math.random().toString(36).substr(2, 9)}`,
        session_id: `stress-session-${Math.random().toString(36).substr(2, 9)}`
      }), {
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}` 
        },
      });
      
      check(chatResponse, {
        'chat status is 200': (r) => r.status === 200,
        'chat response time < 15000ms': (r) => r.timings.duration < 15000,
      });
      errorRate.add(chatResponse.status !== 200);
      responseTime.add(chatResponse.timings.duration);
    }

    // Analytics queries (stress test)
    for (let i = 0; i < 3; i++) {
      let analyticsResponse = http.get(`${BASE_URL}/api/v1/analytics/overview`, {
        headers: { 'Authorization': `Bearer ${accessToken}` },
      });
      
      check(analyticsResponse, {
        'analytics status is 200': (r) => r.status === 200,
        'analytics response time < 5000ms': (r) => r.timings.duration < 5000,
      });
      errorRate.add(analyticsResponse.status !== 200);
      responseTime.add(analyticsResponse.timings.duration);
    }
  }

  sleep(0.5); // Wait 500ms between iterations
}

export function handleSummary(data) {
  return {
    'k6-stress-results.json': JSON.stringify(data, null, 2),
    'k6-stress-results.html': htmlReport(data),
  };
}

function htmlReport(data) {
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <title>K6 Stress Test Results</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .metric { margin: 10px 0; padding: 10px; border: 1px solid #ddd; }
        .pass { background-color: #d4edda; }
        .fail { background-color: #f8d7da; }
        .warning { background-color: #fff3cd; }
      </style>
    </head>
    <body>
      <h1>K6 Stress Test Results</h1>
      <div class="metric">
        <h3>Test Summary</h3>
        <p>Duration: ${data.state.testRunDurationMs / 1000}s</p>
        <p>Max VUs: ${data.metrics.vus.values.max}</p>
        <p>Iterations: ${data.metrics.iterations.values.count}</p>
      </div>
      <div class="metric ${data.metrics.http_req_failed.values.rate < 0.05 ? 'pass' : 'fail'}">
        <h3>Error Rate</h3>
        <p>${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%</p>
        <p>Threshold: < 5%</p>
      </div>
      <div class="metric ${data.metrics.http_req_duration.values.p95 < 5000 ? 'pass' : 'warning'}">
        <h3>Response Time (P95)</h3>
        <p>${data.metrics.http_req_duration.values.p95.toFixed(2)}ms</p>
        <p>Threshold: < 5000ms</p>
      </div>
      <div class="metric">
        <h3>Throughput</h3>
        <p>${data.metrics.http_reqs.values.rate.toFixed(2)} requests/second</p>
      </div>
    </body>
    </html>
  `;
}
