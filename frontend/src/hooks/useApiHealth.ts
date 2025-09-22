import { useEffect } from 'react'
import toast from 'react-hot-toast'
import api from '@/lib/api'

/**
 * Pings the backend health endpoint once on mount.
 * Shows a clear toast if the API base URL is misconfigured or unreachable.
 */
export function useApiHealth(): void {
  useEffect(() => {
    let isMounted = true

    const checkHealth = async () => {
      try {
        // Prefer a standard health endpoint; falls back to a trivial GET
        const response = await api.get('/api/v1/health').catch(async () => {
          return api.get('/')
        })

        if (!isMounted) return

        if (response.status >= 200 && response.status < 500) {
          // Consider reachable; no toast needed
          return
        }

        toast.error('API unreachable or returned an error. Please try again later.')
      } catch (error: any) {
        if (!isMounted) return

        const baseUrl = (api.defaults && api.defaults.baseURL) || 'Unknown API URL'
        const message = error?.message || 'Network error'
        toast.error(`Cannot reach API at ${baseUrl}. ${message}`)
      }
    }

    // Delay slightly to avoid racing initial renders
    const timer = setTimeout(checkHealth, 200)
    return () => {
      isMounted = false
      clearTimeout(timer)
    }
  }, [])
}

export default useApiHealth


