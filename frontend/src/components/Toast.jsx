import React, { useEffect } from 'react'

export default function Toast({
  message,
  type = 'error',
  onClose
}) {
  useEffect(() => {
    if (!message) {
      return
    }

    const timer = setTimeout(() => {
      onClose?.()
    }, 4000)

    return () => clearTimeout(timer)
  }, [message, onClose])

  if (!message) {
    return null
  }

  return (
    <div
      role="alert"
      style={{
        position: 'fixed',
        top: '24px',
        right: '24px',
        zIndex: 9999,
        maxWidth: '420px',
        padding: '14px 18px',
        borderRadius: '10px',
        background:
          type === 'success'
            ? '#166534'
            : '#b91c1c',
        color: '#ffffff',
        boxShadow:
          '0 8px 24px rgba(0, 0, 0, 0.18)',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        fontSize: '14px',
        lineHeight: 1.4
      }}
    >
      <span style={{ flex: 1 }}>
        {message}
      </span>

      <button
        type="button"
        onClick={onClose}
        aria-label="Close message"
        style={{
          border: 'none',
          background: 'transparent',
          color: '#ffffff',
          fontSize: '20px',
          cursor: 'pointer',
          lineHeight: 1
        }}
      >
        ×
      </button>
    </div>
  )
}