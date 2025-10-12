import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  test: {
    environment: 'jsdom',
    environmentOptions: {
      jsdom: { 
        url: 'http://localhost',
        resources: 'usable'
      }
    },
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    sequence: { concurrent: false },
    // Keep workers small for CI stability, avoid OOM
    maxThreads: 1,
    minThreads: 1,
    // Limit in-flight tasks to keep jsdom stable
    isolate: true,
    poolOptions: {
      forks: { singleFork: true },
      threads: { singleThread: true }
    },
    testTimeout: 15000,
    hookTimeout: 15000,
    include: [
      'src/**/*.{test,spec}.{ts,tsx}'
    ],
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/e2e/**',
      '**/*.e2e.spec.ts',
      '**/*.e2e.test.ts',
      '**/__tests__/integration/**'
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'html'],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      },
      include: [
        'src/**/*.{ts,tsx}'
      ],
      exclude: [
        'src/**/*.d.ts',
        'src/**/*.stories.{ts,tsx}',
        'src/**/*.test.{ts,tsx}',
        'src/**/*.spec.{ts,tsx}',
        'src/test/**',
        'src/main.tsx',
        'src/vite-env.d.ts'
      ]
    }
  },
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || 'https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1')
  }
})
