import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { User } from '../types'
import api from '../lib/api'

export function useAuth() {
  const [accessToken, setAccessToken] = useState<string | null>(
    localStorage.getItem('access_token')
  )
  const [refreshToken, setRefreshToken] = useState<string | null>(
    localStorage.getItem('refresh_token')
  )

  const { data: user, isLoading, error } = useQuery(
    ['user', accessToken],
    async () => {
      if (!accessToken) return null
      const response = await api.get('/api/v1/auth/me')
      return response.data as User
    },
    {
      enabled: !!accessToken,
      retry: false,
    }
  )

  const refreshAccessToken = async () => {
    if (!refreshToken) return false
    
    try {
      const response = await api.post('/api/v1/auth/refresh', {
        refresh_token: refreshToken
      })
      
      const { access_token, refresh_token: new_refresh_token } = response.data
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', new_refresh_token)
      setAccessToken(access_token)
      setRefreshToken(new_refresh_token)
      
      return true
    } catch (error) {
      // Refresh failed, clear tokens
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      setAccessToken(null)
      setRefreshToken(null)
      return false
    }
  }

  const login = async (email: string, password: string) => {
    try {
      const response = await api.post('/api/v1/auth/login', {
        email,
        password,
      })
      
      const { access_token, refresh_token } = response.data
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      setAccessToken(access_token)
      setRefreshToken(refresh_token)
      
      return { success: true }
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed'
      }
    }
  }

  const register = async (userData: {
    email: string
    password: string
    full_name?: string
    business_name?: string
    business_domain?: string
  }) => {
    try {
      const response = await api.post('/api/v1/auth/register', userData)
      return { success: true, data: response.data }
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed'
      }
    }
  }

  const logout = async () => {
    try {
      await api.post('/api/v1/auth/logout')
    } catch (error) {
      // Ignore logout errors
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      setAccessToken(null)
      setRefreshToken(null)
    }
  }

  // Auto-refresh token when it's about to expire
  useEffect(() => {
    if (!accessToken || !refreshToken) return

    const refreshInterval = setInterval(async () => {
      const success = await refreshAccessToken()
      if (!success) {
        clearInterval(refreshInterval)
      }
    }, 50 * 60 * 1000) // Refresh every 50 minutes

    return () => clearInterval(refreshInterval)
  }, [accessToken, refreshToken])

  return {
    user: user || null,
    isLoading,
    error,
    login,
    register,
    logout,
    refreshAccessToken,
    isAuthenticated: !!user,
  }
}
