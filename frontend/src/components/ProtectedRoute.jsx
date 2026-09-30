import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({
  allowedRole,
  children
}) {
  const {
    user,
    authLoading
  } = useAuth()

  const location = useLocation()

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

  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: location.pathname
        }}
      />
    )
  }

  if (
    allowedRole &&
    user.role !== allowedRole
  ) {
    return (
      <Navigate
        to={`/${user.role}`}
        replace
      />
    )
  }

  return children
}