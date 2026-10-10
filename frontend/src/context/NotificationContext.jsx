import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'

import { apiRequest } from '../services/api'

const NotificationContext = createContext(null)

export function NotificationProvider({ children }) {
  // =====================================================
  // TOAST NOTIFICATION
  // =====================================================

  const [notification, setNotification] = useState(null)

  // =====================================================
  // DATABASE NOTIFICATIONS
  // =====================================================

  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [notificationsLoading, setNotificationsLoading] =
    useState(false)

  // =====================================================
  // TOAST
  // =====================================================

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

  // =====================================================
  // FETCH NOTIFICATIONS
  // =====================================================

  const fetchNotifications = useCallback(async () => {
    const token =
      localStorage.getItem('access_token')

    if (!token) {
      setNotifications([])
      setUnreadCount(0)
      return
    }

    try {
      setNotificationsLoading(true)

      const data =
        await apiRequest('/notifications')

      setNotifications(
        Array.isArray(data?.notifications)
          ? data.notifications
          : []
      )
    } catch (error) {
      console.error(
        'Failed to fetch notifications:',
        error
      )
    } finally {
      setNotificationsLoading(false)
    }
  }, [])

  // =====================================================
  // FETCH UNREAD COUNT
  // =====================================================

  const fetchUnreadCount = useCallback(async () => {
    const token =
      localStorage.getItem('access_token')

    if (!token) {
      setUnreadCount(0)
      return
    }

    try {
      const data =
        await apiRequest(
          '/notifications/unread-count'
        )

      setUnreadCount(
        Number(data?.unread_count || 0)
      )
    } catch (error) {
      console.error(
        'Failed to fetch unread notification count:',
        error
      )
    }
  }, [])

  // =====================================================
  // FETCH ALL NOTIFICATION DATA
  // =====================================================

  const refreshNotifications =
    useCallback(async () => {
      await Promise.all([
        fetchNotifications(),
        fetchUnreadCount(),
      ])
    }, [
      fetchNotifications,
      fetchUnreadCount,
    ])

  // =====================================================
  // MARK ONE NOTIFICATION AS READ
  // =====================================================

  const markAsRead = useCallback(
    async (notificationId) => {
      try {
        await apiRequest(
          `/notifications/${notificationId}/read`,
          {
            method: 'PUT',
          }
        )

        setNotifications((current) =>
          current.map((item) =>
            item.id === notificationId
              ? {
                  ...item,
                  is_read: true,
                  read_at:
                    new Date().toISOString(),
                }
              : item
          )
        )

        setUnreadCount((current) =>
          Math.max(0, current - 1)
        )
      } catch (error) {
        console.error(
          'Failed to mark notification as read:',
          error
        )

        throw error
      }
    },
    []
  )

  // =====================================================
  // MARK ALL NOTIFICATIONS AS READ
  // =====================================================

  const markAllAsRead =
    useCallback(async () => {
      try {
        await apiRequest(
          '/notifications/read-all',
          {
            method: 'PUT',
          }
        )

        const readTime =
          new Date().toISOString()

        setNotifications((current) =>
          current.map((item) => ({
            ...item,
            is_read: true,
            read_at:
              item.read_at || readTime,
          }))
        )

        setUnreadCount(0)
      } catch (error) {
        console.error(
          'Failed to mark all notifications as read:',
          error
        )

        throw error
      }
    }, [])


  // =====================================================
  // DELETE ONE NOTIFICATION
  // =====================================================

  const deleteNotification = useCallback(
    async (notificationId) => {
      try {
        await apiRequest(
          `/notifications/${notificationId}`,
          {
            method: 'DELETE',
          }
        )

        setNotifications((current) =>
          current.filter(
            (item) => item.id !== notificationId
          )
        )

        await fetchUnreadCount()
      } catch (error) {
        console.error(
          'Failed to delete notification:',
          error
        )

        throw error
      }
    },
    [fetchUnreadCount]
  )

  // =====================================================
  // DELETE ALL NOTIFICATIONS
  // =====================================================

  const deleteAllNotifications =
    useCallback(async () => {
      try {
        await apiRequest(
          '/notifications',
          {
            method: 'DELETE',
          }
        )

        setNotifications([])
        setUnreadCount(0)
      } catch (error) {
        console.error(
          'Failed to delete all notifications:',
          error
        )

        throw error
      }
    }, [])

  // =====================================================
  // INITIAL LOAD
  // =====================================================

  useEffect(() => {
    refreshNotifications()
  }, [refreshNotifications])

  // =====================================================
  // CONTEXT
  // =====================================================

  return (
    <NotificationContext.Provider
      value={{
        // Existing toast API
        showNotification,
        hideNotification,

        // Backend notification API
        notifications,
        unreadCount,
        notificationsLoading,
        fetchNotifications,
        fetchUnreadCount,
        refreshNotifications,
        markAsRead,
        markAllAsRead,
        deleteNotification,
        deleteAllNotifications,
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

// =====================================================
// TOAST COMPONENT
// =====================================================

function Toast({
  notification,
  onClose,
}) {
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

// =====================================================
// HOOK
// =====================================================

export function useNotification() {
  const context =
    useContext(NotificationContext)

  if (!context) {
    throw new Error(
      'useNotification must be used inside NotificationProvider'
    )
  }

  return context
}