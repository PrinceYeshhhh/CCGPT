// K6 Load Test Script
// Comprehensive load testing with detailed metrics

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');
const responseTime = new Trend('response_time');

export let options = {
  stages: [
    { duration: '2m', target: 20 }, // Ramp up
    { duration: '5m', target: 20 }, // Stay at 20 users
    { duration: '2m', target: 40 }, // Ramp up to 40 users
    { duration: '5m', target: 40 }, // Stay at 40 users
    { duration: '2m', target: 0 },  // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests must complete below 2s
    http_req_failed: ['rate<0.01'],    // Error rate must be below 1%
    error_rate: ['rate<0.01'],         // Custom error rate below 1%
  },
};

const BASE_URL = 'http://localhost:8000';

export default function() {
  // Test data
  const testUser = {
    email: `test${Math.random().toString(36).substr(2, 9)}@example.com`,
    password: 'TestPassword123!',
    full_name: `Test User ${Math.random().toString(36).substr(2, 9)}`,
    mobile_phone: `+123456789${Math.floor(Math.random() * 9000) + 1000}`
  };

  let accessToken = null;

  // Health check
  let healthResponse = http.get(`${BASE_URL}/health`);
  check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 500ms': (r) => r.timings.duration < 500,
  });
  errorRate.add(healthResponse.status !== 200);
  responseTime.add(healthResponse.timings.duration);

  // Readiness check
  let readyResponse = http.get(`${BASE_URL}/ready`);
  check(readyResponse, {
    'readiness check status is 200': (r) => r.status === 200,
    'readiness check response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  errorRate.add(readyResponse.status !== 200);
  responseTime.add(readyResponse.timings.duration);

  // User registration
  let registerResponse = http.post(`${BASE_URL}/api/v1/auth/register`, JSON.stringify(testUser), {
    headers: { 'Content-Type': 'application/json' },
  });
  check(registerResponse, {
    'registration status is 201': (r) => r.status === 201,
    'registration response time < 2000ms': (r) => r.timings.duration < 2000,
  });
  errorRate.add(registerResponse.status !== 201);
  responseTime.add(registerResponse.timings.duration);

  // User login
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
    'login response time < 1500ms': (r) => r.timings.duration < 1500,
  });
  errorRate.add(loginResponse.status !== 200);
  responseTime.add(loginResponse.timings.duration);

  if (accessToken) {
    // Document upload (simulate with a simple text file)
    let uploadResponse = http.post(`${BASE_URL}/api/v1/documents/upload`, {
      file: http.file('Sample document content for testing', 'test.txt', 'text/plain')
    }, {
      headers: { 'Authorization': `Bearer ${accessToken}` },
    });
    
    check(uploadResponse, {
      'upload status is 200': (r) => r.status === 200,
      'upload response time < 5000ms': (r) => r.timings.duration < 5000,
    });
    errorRate.add(uploadResponse.status !== 200);
    responseTime.add(uploadResponse.timings.duration);

    // Chat message
    let chatResponse = http.post(`${BASE_URL}/api/v1/chat/message`, JSON.stringify({
      message: 'What is this document about?',
      session_id: `test-session-${Math.random().toString(36).substr(2, 9)}`
    }), {
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}` 
      },
    });
    
    check(chatResponse, {
      'chat status is 200': (r) => r.status === 200,
      'chat response time < 10000ms': (r) => r.timings.duration < 10000,
    });
    errorRate.add(chatResponse.status !== 200);
    responseTime.add(chatResponse.timings.duration);

    // Analytics overview
    let analyticsResponse = http.get(`${BASE_URL}/api/v1/analytics/overview`, {
      headers: { 'Authorization': `Bearer ${accessToken}` },
    });
    
    check(analyticsResponse, {
      'analytics status is 200': (r) => r.status === 200,
      'analytics response time < 3000ms': (r) => r.timings.duration < 3000,
    });
    errorRate.add(analyticsResponse.status !== 200);
    responseTime.add(analyticsResponse.timings.duration);
  }

  sleep(1); // Wait 1 second between iterations
}

export function handleSummary(data) {
  return {
    'k6-results.json': JSON.stringify(data, null, 2),
    'k6-results.html': htmlReport(data),
  };
}

function htmlReport(data) {
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <title>K6 Load Test Results</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .metric { margin: 10px 0; padding: 10px; border: 1px solid #ddd; }
        .pass { background-color: #d4edda; }
        .fail { background-color: #f8d7da; }
      </style>
    </head>
    <body>
      <h1>K6 Load Test Results</h1>
      <div class="metric">
        <h3>Test Summary</h3>
        <p>Duration: ${data.state.testRunDurationMs / 1000}s</p>
        <p>VUs: ${data.metrics.vus.values.max}</p>
        <p>Iterations: ${data.metrics.iterations.values.count}</p>
      </div>
      <div class="metric ${data.metrics.http_req_failed.values.rate < 0.01 ? 'pass' : 'fail'}">
        <h3>Error Rate</h3>
        <p>${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%</p>
      </div>
      <div class="metric ${data.metrics.http_req_duration.values.p95 < 2000 ? 'pass' : 'fail'}">
        <h3>Response Time (P95)</h3>
        <p>${data.metrics.http_req_duration.values.p95.toFixed(2)}ms</p>
      </div>
    </body>
    </html>
  `;
}
