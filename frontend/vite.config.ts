import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { analyzer } from 'vite-bundle-analyzer'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.VITE_API_URL || 'http://localhost:8000'
  return ({
  plugins: [
    react(),
    // Add bundle analyzer in development
    mode === 'analyze' && analyzer({
      analyzerMode: 'server',
      analyzerPort: 8888,
      openAnalyzer: true,
    })
  ].filter(Boolean),
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target,
        changeOrigin: true,
        secure: false,
        ws: true,
      },
      '/ws': {
        target,
        changeOrigin: true,
        ws: true,
        secure: false,
      },
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: mode === 'analyze', // Enable sourcemaps for analysis
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          charts: ['recharts'],
          ui: ['@radix-ui/react-accordion', '@radix-ui/react-dialog', '@radix-ui/react-label', '@radix-ui/react-progress', '@radix-ui/react-select', '@radix-ui/react-tabs'],
          forms: ['react-hook-form', '@hookform/resolvers', 'zod'],
          utils: ['axios', 'date-fns', 'clsx', 'tailwind-merge', 'class-variance-authority'],
        }
      }
    }
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'axios']
  }
  })
})
