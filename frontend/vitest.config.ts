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
    sequence: { concurrent: false },
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/e2e/**',
      '**/*.e2e.spec.ts',
      '**/*.e2e.test.ts'
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'html']
    }
  },
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || 'https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1')
  }
})
