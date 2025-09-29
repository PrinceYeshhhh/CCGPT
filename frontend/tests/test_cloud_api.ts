/**
 * Frontend Cloud API Tests
 * Tests the frontend against the deployed cloud backend
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import axios from 'axios';

// Cloud URLs (using your existing configuration)
const BACKEND_URL = import.meta.env.VITE_API_URL || 'https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1';
const WS_URL = import.meta.env.VITE_WS_URL || 'wss://customercaregpt-backend-xxxxx-uc.a.run.app/ws';

// Test configuration
const TEST_USER = {
  email: `test_${Date.now()}@example.com`,
  password: 'SecurePassword123!',
  full_name: 'Test User'
};

let authToken: string = '';
let userId: string = '';

describe('Cloud API Integration Tests', () => {
  beforeAll(async () => {
    console.log('🌐 Testing against cloud backend:', BACKEND_URL);
    console.log('🌐 WebSocket URL:', WS_URL);
  });

  afterAll(async () => {
    // Cleanup if needed
  });

  describe('Health Checks', () => {
    it('should check backend health', async () => {
      const response = await axios.get(`${BACKEND_URL.replace('/api/v1', '')}/health`);
      
      expect(response.status).toBe(200);
      expect(response.data.status).toBe('healthy');
      expect(response.data.timestamp).toBeDefined();
    });

    it('should check backend readiness', async () => {
      const response = await axios.get(`${BACKEND_URL.replace('/api/v1', '')}/ready`);
      
      expect(response.status).toBe(200);
      expect(response.data.status).toBe('ready');
    });

    it('should check detailed health', async () => {
      const response = await axios.get(`${BACKEND_URL.replace('/api/v1', '')}/health/detailed`);
      
      expect(response.status).toBe(200);
      expect(response.data.dependencies).toBeDefined();
      expect(response.data.dependencies.database).toBeDefined();
      expect(response.data.dependencies.redis).toBeDefined();
    });
  });

  describe('Authentication', () => {
    it('should register a new user', async () => {
      const response = await axios.post(`${BACKEND_URL}/auth/register`, TEST_USER);
      
      expect(response.status).toBe(201);
      expect(response.data.user).toBeDefined();
      expect(response.data.user.email).toBe(TEST_USER.email);
      expect(response.data.user.full_name).toBe(TEST_USER.full_name);
      
      userId = response.data.user.id;
    });

    it('should login with valid credentials', async () => {
      const loginData = {
        email: TEST_USER.email,
        password: TEST_USER.password
      };
      
      const response = await axios.post(`${BACKEND_URL}/auth/login`, loginData);
      
      expect(response.status).toBe(200);
      expect(response.data.access_token).toBeDefined();
      expect(response.data.token_type).toBe('bearer');
      
      authToken = response.data.access_token;
    });

    it('should reject invalid credentials', async () => {
      const invalidLoginData = {
        email: TEST_USER.email,
        password: 'wrongpassword'
      };
      
      try {
        await axios.post(`${BACKEND_URL}/auth/login`, invalidLoginData);
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
        expect(error.response.data.detail).toContain('Invalid credentials');
      }
    });

    it('should get current user with valid token', async () => {
      const response = await axios.get(`${BACKEND_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      expect(response.status).toBe(200);
      expect(response.data.id).toBe(userId);
      expect(response.data.email).toBe(TEST_USER.email);
    });

    it('should reject requests without token', async () => {
      try {
        await axios.get(`${BACKEND_URL}/auth/me`);
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
      }
    });
  });

  describe('Workspaces', () => {
    let workspaceId: string = '';

    it('should create a new workspace', async () => {
      const workspaceData = {
        name: 'Test Workspace',
        description: 'Test workspace for cloud integration'
      };
      
      const response = await axios.post(`${BACKEND_URL}/workspaces/`, workspaceData, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      expect(response.status).toBe(201);
      expect(response.data.id).toBeDefined();
      expect(response.data.name).toBe(workspaceData.name);
      expect(response.data.description).toBe(workspaceData.description);
      
      workspaceId = response.data.id;
    });

    it('should get user workspaces', async () => {
      const response = await axios.get(`${BACKEND_URL}/workspaces/`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      expect(response.status).toBe(200);
      expect(Array.isArray(response.data)).toBe(true);
      expect(response.data.length).toBeGreaterThan(0);
    });

    it('should update workspace', async () => {
      const updateData = {
        name: 'Updated Test Workspace',
        description: 'Updated description'
      };
      
      const response = await axios.put(`${BACKEND_URL}/workspaces/${workspaceId}`, updateData, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      expect(response.status).toBe(200);
      expect(response.data.name).toBe(updateData.name);
      expect(response.data.description).toBe(updateData.description);
    });

    it('should reject workspace access without auth', async () => {
      try {
        await axios.get(`${BACKEND_URL}/workspaces/`);
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
      }
    });
  });

  describe('Documents', () => {
    let workspaceId: string = '';

    beforeAll(async () => {
      // Create a workspace for document tests
      const workspaceData = {
        name: 'Document Test Workspace',
        description: 'Workspace for document testing'
      };
      
      const response = await axios.post(`${BACKEND_URL}/workspaces/`, workspaceData, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      workspaceId = response.data.id;
    });

    it('should upload a document', async () => {
      const formData = new FormData();
      const fileContent = 'This is a test document for cloud integration testing.';
      const blob = new Blob([fileContent], { type: 'text/plain' });
      formData.append('file', blob, 'test_document.txt');
      formData.append('workspace_id', workspaceId);
      
      const response = await axios.post(`${BACKEND_URL}/documents/upload`, formData, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      
      expect(response.status).toBe(201);
      expect(response.data.id).toBeDefined();
      expect(response.data.filename).toBe('test_document.txt');
    });

    it('should get documents for workspace', async () => {
      const response = await axios.get(`${BACKEND_URL}/documents/?workspace_id=${workspaceId}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      expect(response.status).toBe(200);
      expect(Array.isArray(response.data)).toBe(true);
    });

    it('should reject document upload without workspace', async () => {
      const formData = new FormData();
      const fileContent = 'Test content';
      const blob = new Blob([fileContent], { type: 'text/plain' });
      formData.append('file', blob, 'test.txt');
      
      try {
        await axios.post(`${BACKEND_URL}/documents/upload`, formData, {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'multipart/form-data'
          }
        });
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(400);
      }
    });
  });

  describe('Chat', () => {
    let workspaceId: string = '';

    beforeAll(async () => {
      // Create a workspace for chat tests
      const workspaceData = {
        name: 'Chat Test Workspace',
        description: 'Workspace for chat testing'
      };
      
      const response = await axios.post(`${BACKEND_URL}/workspaces/`, workspaceData, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      workspaceId = response.data.id;
    });

    it('should create a chat session', async () => {
      const sessionData = {
        workspace_id: workspaceId,
        title: 'Test Chat Session'
      };
      
      const response = await axios.post(`${BACKEND_URL}/chat/sessions/`, sessionData, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      expect(response.status).toBe(201);
      expect(response.data.id).toBeDefined();
      expect(response.data.title).toBe(sessionData.title);
    });

    it('should send a chat message', async () => {
      const messageData = {
        workspace_id: workspaceId,
        content: 'Hello, this is a test message for cloud integration testing.'
      };
      
      const response = await axios.post(`${BACKEND_URL}/chat/message`, messageData, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      expect(response.status).toBe(200);
      expect(response.data.response).toBeDefined();
      expect(response.data.message_id).toBeDefined();
    });
  });

  describe('Billing', () => {
    it('should get billing status', async () => {
      const response = await axios.get(`${BACKEND_URL}/billing/status`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      expect(response.status).toBe(200);
      expect(response.data.tier).toBeDefined();
    });

    it('should get quota information', async () => {
      const response = await axios.get(`${BACKEND_URL}/billing/quota`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      expect(response.status).toBe(200);
      expect(response.data.daily_usage).toBeDefined();
      expect(response.data.monthly_usage).toBeDefined();
    });
  });

  describe('Error Handling', () => {
    it('should handle 404 errors gracefully', async () => {
      try {
        await axios.get(`${BACKEND_URL}/nonexistent/endpoint`, {
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        });
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(404);
      }
    });

    it('should handle malformed JSON gracefully', async () => {
      try {
        await axios.post(`${BACKEND_URL}/auth/login`, 'invalid json', {
          headers: {
            'Content-Type': 'application/json'
          }
        });
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(422);
      }
    });
  });

  describe('CORS', () => {
    it('should handle CORS preflight requests', async () => {
      const response = await axios.options(`${BACKEND_URL}/auth/login`, {
        headers: {
          'Origin': 'https://customercaregpt-frontend.vercel.app',
          'Access-Control-Request-Method': 'POST',
          'Access-Control-Request-Headers': 'Content-Type'
        }
      });
      
      expect(response.status).toBe(200);
      expect(response.headers['access-control-allow-origin']).toBeDefined();
    });
  });
});

describe('Performance Tests', () => {
  it('should respond within acceptable time', async () => {
    const startTime = Date.now();
    const response = await axios.get(`${BACKEND_URL.replace('/api/v1', '')}/health`);
    const endTime = Date.now();
    
    const responseTime = endTime - startTime;
    
    expect(response.status).toBe(200);
    expect(responseTime).toBeLessThan(5000); // Should respond within 5 seconds
  });

  it('should handle concurrent requests', async () => {
    const requests = Array(5).fill(null).map(() => 
      axios.get(`${BACKEND_URL.replace('/api/v1', '')}/health`)
    );
    
    const responses = await Promise.all(requests);
    
    responses.forEach(response => {
      expect(response.status).toBe(200);
      expect(response.data.status).toBe('healthy');
    });
  });
});
