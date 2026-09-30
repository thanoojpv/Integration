import React, {
  createContext,
  useCallback,
  useContext,
  useState,
} from 'react'

const NotificationContext = createContext(null)

export function NotificationProvider({ children }) {
  const [notification, setNotification] = useState(null)

  const showNotification = useCallback(
    (message, type = 'error') => {
      setNotification({
        message,
        type,
      })
    },
    []
  )

  const hideNotification = useCallback(() => {
    setNotification(null)
  }, [])

  return (
    <NotificationContext.Provider
      value={{
        showNotification,
        hideNotification,
      }}
    >
      {children}

      <Toast
        notification={notification}
        onClose={hideNotification}
      />
    </NotificationContext.Provider>
  )
}

function Toast({ notification, onClose }) {
  if (!notification) {
    return null
  }

  return (
    <div
      role="alert"
      style={{
        position: 'fixed',
        top: '24px',
        right: '24px',
        zIndex: 99999,
        maxWidth: '420px',
        padding: '14px 18px',
        borderRadius: '10px',
        background:
          notification.type === 'success'
            ? '#166534'
            : '#b91c1c',
        color: '#fff',
        boxShadow:
          '0 8px 24px rgba(0, 0, 0, 0.18)',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        fontSize: '14px',
        lineHeight: 1.4,
      }}
    >
      <span style={{ flex: 1 }}>
        {notification.message}
      </span>

      <button
        type="button"
        onClick={onClose}
        aria-label="Close notification"
        style={{
          border: 'none',
          background: 'transparent',
          color: '#fff',
          fontSize: '20px',
          cursor: 'pointer',
          lineHeight: 1,
        }}
      >
        ×
      </button>
    </div>
  )
}

export function useNotification() {
  const context = useContext(NotificationContext)

  if (!context) {
    throw new Error(
      'useNotification must be used inside NotificationProvider'
    )
  }

  return context
}