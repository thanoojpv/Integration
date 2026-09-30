import React, {
  createContext,
  useContext,
  useEffect,
  useState
} from 'react'

import {
  loginUser,
  getCurrentUser
} from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)

  useEffect(() => {
  const validateSession = async () => {
    const token = localStorage.getItem('access_token')

    if (!token) {
      setAuthLoading(false)
      return
    }

    try {
      const data = await getCurrentUser(token)

      const currentUser =
        data?.user ||
        data

      if (!currentUser) {
        throw new Error('Invalid session')
      }

      localStorage.setItem(
        'devsprint_user',
        JSON.stringify(currentUser)
      )

      setUser(currentUser)
    } catch (error) {
      console.warn(
        'Session validation failed:',
        error
      )

      localStorage.removeItem(
        'devsprint_user'
      )

      localStorage.removeItem(
        'access_token'
      )

      setUser(null)
    } finally {
      setAuthLoading(false)
    }
  }

  validateSession()
}, [])

  const login = async (email, password) => {
    try {
      const data = await loginUser(email, password)

      if (data && data.user && data.token)  {
        const nextUser = data.user

        localStorage.setItem(
          'devsprint_user',
          JSON.stringify(nextUser)
        )

        localStorage.setItem(
          'access_token',
          data.token
        )

        setUser(nextUser)

        return {
          success: true,
          user: nextUser
        }
      }

      return {
        success: false,
        message: data.error || data.message || 'Login failed'
      }
    } catch (error) {
      console.error('Login error:', error)

      return {
        success: false,
        message: error.message || 'Unable to connect to server'
      }
    }
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('devsprint_user')
    localStorage.removeItem('access_token')
  }
  if (authLoading) {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}
    >
      Checking your session...
    </div>
  )
}
  return (
<AuthContext.Provider
    value={{
      user,
      login,
      logout,
      authLoading
    }}
  >      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}