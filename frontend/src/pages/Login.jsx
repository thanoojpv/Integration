import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useNotification } from '../context/NotificationContext'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const navigate = useNavigate()
  const { login } = useAuth()
  const { showNotification } = useNotification()

  const handleSubmit = async (e) => {
    e.preventDefault()

    try {
      const result = await login(email, password)

      if (!result || !result.user) {
        showNotification(
          result?.error ||
          result?.message ||
          'Login failed'
        )       
         return
      }

      console.log('Login successful:', result)

      // Get the user's actual role from the backend
      const userRole = result.user.role

      // Navigate to the correct portal automatically
      if (userRole === 'learner') {
        navigate('/learner')
      } else if (userRole === 'trainer') {
        navigate('/trainer')
      } else if (userRole === 'admin') {
        navigate('/admin')
      } else {
        showNotification('Invalid user role')
      }

    } catch (error) {
      console.error('Login error:', error)
      showNotification('Unable to connect to the backend'
)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">

        <div className="auth-left">
          <div className="brand-badge">
            <span className="brand-mark">DS</span> DevSprint LMS
          </div>

          <div>
            <h1>Learn. Build. Grow.</h1>
            <p>
              Professional corporate learning and skill management portal
              for DevSprint Services Pvt. Ltd.
            </p>
          </div>

          <div className="footnote">
            © 2026 DevSprint Services. All rights reserved.
          </div>
        </div>

        <div className="auth-right">
          <h2>Welcome back 👋</h2>

          <p className="subtitle">
            Please enter your credentials to log in. Your portal opens
            automatically based on your account.
          </p>

          <form onSubmit={handleSubmit}>

            {/* Email */}
            <div className="field">
              <label>Email Address</label>

              <div className="input-wrap">
                <span className="field-icon">✉</span>

                <input
                  className="with-icon"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email address"
                  required
                />
              </div>
            </div>

            {/* Password */}
            <div className="field">
              <label>Password</label>

              <div className="input-wrap password-wrap">
                <span className="field-icon">🔒</span>

                <input
                  className="with-icon"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                />

                <button
                  type="button"
                  className="show-password-btn"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>

            {/* Remember me + Forgot password */}
            <div className="checkbox-row">
              <label>
                <input type="checkbox" defaultChecked /> Remember me
              </label>

              <Link className="link" to="/forgot-password">
                Forget password?
              </Link>
            </div>

            {/* Login */}
            <button
              className="btn btn-primary btn-full"
              type="submit"
            >
              Login Now →
            </button>

          </form>

          <div className="auth-foot">
            Don't have an account?{' '}
            <Link
              className="link"
              to="/create-account"
              style={{
                color: 'var(--blue-600)',
                fontWeight: 600
              }}
            >
              Create account
            </Link>
          </div>

        </div>
      </div>
    </div>
  )
}