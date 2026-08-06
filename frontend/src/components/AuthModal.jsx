import { useState, useEffect } from 'react'
import axios from 'axios'

export function AuthModal({ isOpen, onClose, onAuthSuccess, initialMode = 'login' }) {
  const [mode, setMode] = useState(initialMode) // 'login' | 'register'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setMode(initialMode)
      setError('')
    }
  }, [isOpen, initialMode])

  if (!isOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const endpoint = mode === 'login' ? '/api/v1/auth/login' : '/api/v1/auth/register'
      const payload = mode === 'login' ? { username, password } : { username, password, email }

      const response = await axios.post(endpoint, payload)
      const { access_token, user } = response.data

      // Save token to localStorage & set default axios header
      localStorage.setItem('auth_token', access_token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

      onAuthSuccess(user, access_token)
      onClose()
    } catch (err) {
      console.error('Auth error:', err)
      const msg = err.response?.data?.detail || 'خطا در برقراری ارتباط با سرور'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.65)',
        backdropFilter: 'blur(8px)',
        zIndex: 3000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
      }}>
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '380px',
          padding: '28px',
          borderRadius: '20px',
          position: 'relative',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.5)',
        }}>
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '16px',
            left: '16px',
            background: 'none',
            border: 'none',
            color: 'var(--text-sub)',
            fontSize: '18px',
            cursor: 'pointer',
          }}>
          ✕
        </button>

        {/* Header Tabs */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--panel-border)', paddingBottom: '12px', gap: '16px' }}>
          <button
            onClick={() => { setMode('login'); setError(''); }}
            style={{
              background: 'none',
              border: 'none',
              color: mode === 'login' ? '#38bdf8' : 'var(--text-sub)',
              fontWeight: 800,
              fontSize: '16px',
              cursor: 'pointer',
              borderBottom: mode === 'login' ? '2px solid #38bdf8' : 'none',
              paddingBottom: '4px',
            }}>
            ورود به حساب
          </button>
          <button
            onClick={() => { setMode('register'); setError(''); }}
            style={{
              background: 'none',
              border: 'none',
              color: mode === 'register' ? '#38bdf8' : 'var(--text-sub)',
              fontWeight: 800,
              fontSize: '16px',
              cursor: 'pointer',
              borderBottom: mode === 'register' ? '2px solid #38bdf8' : 'none',
              paddingBottom: '4px',
            }}>
            ثبت‌نام کاربر جدید
          </button>
        </div>

        {/* Auth Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {error && (
            <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#f87171', padding: '8px 12px', borderRadius: '8px', fontSize: '12px' }}>
              ⚠️ {error}
            </div>
          )}

          <div>
            <label style={{ fontSize: '11px', color: 'var(--text-sub)', display: 'block', marginBottom: '4px' }}>نام کاربری</label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="مثال: explorer_tehran"
              style={{
                width: '100%',
                background: 'rgba(125, 125, 125, 0.12)',
                border: '1px solid var(--panel-border)',
                color: 'var(--text-main)',
                padding: '10px 12px',
                borderRadius: '10px',
                fontSize: '13px',
                outline: 'none',
                fontFamily: 'Vazirmatn',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {mode === 'register' && (
            <div>
              <label style={{ fontSize: '11px', color: 'var(--text-sub)', display: 'block', marginBottom: '4px' }}>ایمیل (اختیاری)</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="email@example.com"
                style={{
                  width: '100%',
                  background: 'rgba(125, 125, 125, 0.12)',
                  border: '1px solid var(--panel-border)',
                  color: 'var(--text-main)',
                  padding: '10px 12px',
                  borderRadius: '10px',
                  fontSize: '13px',
                  outline: 'none',
                  fontFamily: 'Vazirmatn',
                  boxSizing: 'border-box',
                }}
              />
            </div>
          )}

          <div>
            <label style={{ fontSize: '11px', color: 'var(--text-sub)', display: 'block', marginBottom: '4px' }}>رمز عبور</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={{
                width: '100%',
                background: 'rgba(125, 125, 125, 0.12)',
                border: '1px solid var(--panel-border)',
                color: 'var(--text-main)',
                padding: '10px 12px',
                borderRadius: '10px',
                fontSize: '13px',
                outline: 'none',
                fontFamily: 'Vazirmatn',
                boxSizing: 'border-box',
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              marginTop: '8px',
              background: 'linear-gradient(135deg, #38bdf8, #3b82f6)',
              color: '#fff',
              border: 'none',
              padding: '12px',
              borderRadius: '10px',
              fontWeight: 800,
              fontSize: '14px',
              cursor: 'pointer',
              opacity: loading ? 0.7 : 1,
            }}>
            {loading ? 'در حال ارتباط...' : mode === 'login' ? 'ورود به سامانه 🔑' : 'تأیید و ثبت‌نام ✨'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default AuthModal
