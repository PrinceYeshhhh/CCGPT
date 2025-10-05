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
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    // 20 minutes timeout to accommodate heavy tests in CI
    testTimeout: 1200000,
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/e2e/**',
      '**/__tests__/integration/**',
      '**/*.e2e.spec.ts',
      '**/*.e2e.test.ts'
    ]
  },
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || 'https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1')
  }
})
