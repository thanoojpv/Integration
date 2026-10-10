import React, { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { enrolledCourses } from '../data/mockData'
import { useAuth } from '../context/AuthContext'
import { useNotification } from '../context/NotificationContext'

export default function Topbar() {
  const [open, setOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const [query, setQuery] = useState('')

  const { user, logout } = useAuth()

  const {
    notifications,
    unreadCount,
    notificationsLoading,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    deleteAllNotifications,
    refreshNotifications,
  } = useNotification()

  const navigate = useNavigate()

  const initials = (user?.name || 'U')
    .split(' ')
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  const results = useMemo(() => {
    const q = query.trim().toLowerCase()

    if (!q) return []

    return enrolledCourses
      .filter((course) =>
        `${course.title} ${course.instructor} ${course.level}`
          .toLowerCase()
          .includes(q)
      )
      .slice(0, 5)
  }, [query])

  /* =========================================================
     SEARCH
  ========================================================= */

  const handleSearch = (event) => {
    event.preventDefault()

    const first = results[0]

    if (first) {
      navigate(`/learner/course/${first.id}`)
      setQuery('')
    }
  }

  /* =========================================================
     LOGOUT
  ========================================================= */

  const handleLogout = () => {
    setProfileOpen(false)
    setOpen(false)

    logout()

    navigate('/login', {
      replace: true,
    })
  }

  /* =========================================================
     PROFILE
  ========================================================= */

  const handleProfile = () => {
    setProfileOpen(false)

    navigate(
      `/${user?.role || 'learner'}/settings`
    )
  }

  /* =========================================================
     NOTIFICATION TOGGLE
  ========================================================= */

  const handleNotificationToggle = async () => {
    const nextOpen = !open

    setOpen(nextOpen)
    setProfileOpen(false)

    if (nextOpen) {
      await refreshNotifications()
    }
  }

  /* =========================================================
     OPEN NOTIFICATION
  ========================================================= */

  const handleNotificationClick = async (notification) => {
    try {
      if (!notification.is_read) {
        await markAsRead(notification.id)
      }

      if (notification.link) {
        setOpen(false)
        navigate(notification.link)
      }
    } catch (error) {
      console.error(
        'Unable to open notification:',
        error
      )
    }
  }

  /* =========================================================
     MARK ALL AS READ
  ========================================================= */

  const handleMarkAllAsRead = async () => {
    try {
      await markAllAsRead()
    } catch (error) {
      console.error(
        'Unable to mark all notifications as read:',
        error
      )
    }
  }

  /* =========================================================
     DELETE ONE NOTIFICATION
  ========================================================= */

  const handleDeleteNotification = async (
    event,
    notificationId
  ) => {
    event.stopPropagation()

    try {
      await deleteNotification(notificationId)
    } catch (error) {
      console.error(
        'Unable to delete notification:',
        error
      )
    }
  }

  /* =========================================================
     DELETE ALL NOTIFICATIONS
  ========================================================= */

  const handleDeleteAllNotifications = async () => {
    try {
      await deleteAllNotifications()
    } catch (error) {
      console.error('Unable to delete all notifications:', error)
    }
  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (
    <>
      <header
        className="topbar"
        style={{
          position: 'relative',
          zIndex: 1000,
          overflow: 'visible',
        }}
      >

        {/* =================================================
            SEARCH
        ================================================= */}

        <div className="search-area">

          <form
            className="search-box"
            onSubmit={handleSearch}
          >

            <span>🔍</span>

            <input
              value={query}
              onChange={(e) =>
                setQuery(e.target.value)
              }
              placeholder="Search courses, lessons, assignments, trainers..."
              aria-label="Search"
            />

          </form>

          {query.trim() && (

            <div className="search-results">

              {results.length ? (

                results.map((course) => (

                  <button
                    type="button"
                    key={course.id}
                    className="search-result"
                    onClick={() => {
                      navigate(
                        `/learner/course/${course.id}`
                      )

                      setQuery('')
                    }}
                  >

                    <strong>
                      {course.title}
                    </strong>

                    <span>
                      {course.instructor}
                    </span>

                  </button>

                ))

              ) : (

                <div className="search-empty">
                  No matching courses found
                </div>

              )}

            </div>

          )}

        </div>


        {/* =================================================
            RIGHT SIDE
        ================================================= */}

        <div className="topbar-right">

          {/* =================================================
              NOTIFICATION BELL
          ================================================= */}

          <div
            className="bell"
            onClick={handleNotificationToggle}
            style={{
              cursor: 'pointer',
              position: 'relative',
            }}
            role="button"
            tabIndex={0}
            aria-label="Notifications"
            aria-expanded={open}
            onKeyDown={(event) => {
              if (
                event.key === 'Enter' ||
                event.key === ' '
              ) {
                event.preventDefault()
                handleNotificationToggle()
              }
            }}
          >

            <span>
              🔔
            </span>

            {unreadCount > 0 && (

              <span
                style={{
                  position: 'absolute',
                  top: '-7px',
                  right: '-9px',
                  minWidth: '18px',
                  height: '18px',
                  padding: '0 5px',
                  borderRadius: '999px',
                  background: '#d92d20',
                  color: '#fff',
                  fontSize: '10px',
                  fontWeight: '700',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '2px solid #fff',
                  boxSizing: 'border-box',
                }}
              >
                {unreadCount > 99
                  ? '99+'
                  : unreadCount}
              </span>

            )}

          </div>


          {/* =================================================
              PROFILE
          ================================================= */}

          <div
            className="profile-wrap"
            style={{
              position: 'relative',
            }}
          >

            <button
              type="button"
              className="user-chip profile-button"
              onClick={() => {
                setProfileOpen((o) => !o)
                setOpen(false)
              }}
              aria-label="Open profile menu"
              aria-expanded={profileOpen}
            >

              <div className="avatar">
                {initials}
              </div>

              <div>

                <div className="name">
                  {user?.name || 'Guest'}
                </div>

                <div
                  className="role"
                  style={{
                    textTransform: 'capitalize',
                  }}
                >
                  {user?.role || ''}
                </div>

              </div>

              <span className="profile-arrow">
                {profileOpen ? '⌃' : '⌄'}
              </span>

            </button>


            {/* =================================================
                PROFILE DROPDOWN
            ================================================= */}

            {profileOpen && (

              <div
                className="profile-menu"
                style={{
                  position: 'absolute',
                  top: 'calc(100% + 10px)',
                  right: 0,
                  width: '260px',
                  background: '#ffffff',
                  border: '1px solid #e4e7ec',
                  borderRadius: '12px',
                  boxShadow:
                    '0 12px 30px rgba(16, 24, 40, 0.15)',
                  padding: '8px',
                  zIndex: 9999,
                }}
              >

                {/* PROFILE SUMMARY */}

                <div
                  className="profile-summary"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '12px',
                    marginBottom: '6px',
                    borderBottom:
                      '1px solid #eef0f3',
                  }}
                >

                  <div className="avatar">
                    {initials}
                  </div>

                  <div
                    style={{
                      minWidth: 0,
                    }}
                  >

                    <strong
                      style={{
                        display: 'block',
                        color: '#172033',
                        fontSize: '14px',
                        marginBottom: '3px',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {user?.name || 'Guest'}
                    </strong>

                    <span
                      style={{
                        display: 'block',
                        color: '#667085',
                        fontSize: '12px',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {user?.email || ''}
                    </span>

                  </div>

                </div>


                {/* MY PROFILE */}

                <button
                  type="button"
                  onClick={handleProfile}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    border: 'none',
                    background: 'transparent',
                    borderRadius: '8px',
                    padding: '11px 12px',
                    color: '#344054',
                    fontSize: '14px',
                    textAlign: 'left',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background =
                      '#f5f7ff'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background =
                      'transparent'
                  }}
                >

                  <span>👤</span>

                  <span>
                    My Profile
                  </span>

                </button>


                {/* ACCOUNT SETTINGS */}

                <button
                  type="button"
                  onClick={handleProfile}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    border: 'none',
                    background: 'transparent',
                    borderRadius: '8px',
                    padding: '11px 12px',
                    color: '#344054',
                    fontSize: '14px',
                    textAlign: 'left',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background =
                      '#f5f7ff'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background =
                      'transparent'
                  }}
                >

                  <span>⚙️</span>

                  <span>
                    Account Settings
                  </span>

                </button>


                {/* LOGOUT */}

                <button
                  type="button"
                  onClick={handleLogout}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    border: 'none',
                    borderTop:
                      '1px solid #eef0f3',
                    marginTop: '6px',
                    padding: '12px',
                    background: 'transparent',
                    borderRadius: '8px',
                    color: '#d92d20',
                    fontSize: '14px',
                    fontWeight: '600',
                    textAlign: 'left',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background =
                      '#fff5f4'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background =
                      'transparent'
                  }}
                >

                  <span>🚪</span>

                  <span>
                    Logout
                  </span>

                </button>

              </div>

            )}

          </div>

        </div>


        {/* =================================================
            NOTIFICATION PANEL
        ================================================= */}

        {open && (

          <div
            className="notif-panel"
            style={{
              position: 'absolute',
              top: 'calc(100% + 10px)',
              right: '20px',
              width: '390px',
              maxWidth: 'calc(100vw - 30px)',
              background: '#ffffff',
              border: '1px solid #e4e7ec',
              borderRadius: '14px',
              boxShadow:
                '0 16px 40px rgba(16, 24, 40, 0.18)',
              overflow: 'hidden',
              zIndex: 99999,
            }}
          >

            {/* =================================================
                PANEL HEADER
            ================================================= */}

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '15px 16px',
                borderBottom:
                  '1px solid #eef0f3',
              }}
            >

              <div>

                <div
                  style={{
                    fontSize: '16px',
                    fontWeight: '700',
                    color: '#172033',
                  }}
                >
                  Notifications
                </div>

                <div
                  style={{
                    marginTop: '3px',
                    fontSize: '12px',
                    color: '#667085',
                  }}
                >
                  {notifications.length === 0
                    ? 'No notifications'
                    : unreadCount === 0
                      ? `${notifications.length} notification${notifications.length === 1 ? '' : 's'}`
                      : `${unreadCount} unread`}
                </div>

              </div>


              {/* HEADER ACTIONS */}

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                }}
              >

                <button
                  type="button"
                  onClick={handleMarkAllAsRead}
                  disabled={unreadCount === 0}
                  style={{
                    border: 'none',
                    background: 'transparent',
                    color:
                      unreadCount === 0
                        ? '#98a2b3'
                        : '#4f46e5',
                    fontSize: '12px',
                    fontWeight: '600',
                    cursor:
                      unreadCount === 0
                        ? 'default'
                        : 'pointer',
                    padding: '5px',
                  }}
                >
                  Mark all read
                </button>

                <button
                  type="button"
                  onClick={handleDeleteAllNotifications}
                  disabled={notifications.length === 0}
                  style={{
                    border: 'none',
                    background:
                      notifications.length === 0
                        ? 'transparent'
                        : '#fff1f0',
                    color:
                      notifications.length === 0
                        ? '#98a2b3'
                        : '#d92d20',
                    fontSize: '12px',
                    fontWeight: '600',
                    cursor:
                      notifications.length === 0
                        ? 'default'
                        : 'pointer',
                    padding: '6px 9px',
                    borderRadius: '7px',
                  }}
                >
                  Clear all
                </button>

              </div>

            </div>


            {/* =================================================
                PANEL CONTENT
            ================================================= */}

            <div
              style={{
                maxHeight: '440px',
                overflowY: 'auto',
              }}
            >

              {notificationsLoading ? (

                <div
                  style={{
                    padding: '35px 20px',
                    textAlign: 'center',
                    color: '#667085',
                    fontSize: '14px',
                  }}
                >
                  Loading notifications...
                </div>

              ) : notifications.length === 0 ? (

                <div
                  style={{
                    padding: '42px 20px',
                    textAlign: 'center',
                  }}
                >

                  <div
                    style={{
                      fontSize: '34px',
                      marginBottom: '10px',
                    }}
                  >
                    🔔
                  </div>

                  <div
                    style={{
                      fontWeight: '600',
                      color: '#344054',
                      marginBottom: '5px',
                    }}
                  >
                    No notifications
                  </div>

                  <div
                    style={{
                      fontSize: '12px',
                      color: '#98a2b3',
                    }}
                  >
                    New updates will appear here.
                  </div>

                </div>

              ) : (

                notifications.map((item) => (

                  <div
                    key={item.id}
                    role="button"
                    tabIndex={0}
                    onClick={() =>
                      handleNotificationClick(item)
                    }
                    onKeyDown={(event) => {
                      if (
                        event.key === 'Enter' ||
                        event.key === ' '
                      ) {
                        event.preventDefault()
                        handleNotificationClick(item)
                      }
                    }}
                    style={{
                      width: '100%',
                      borderBottom:
                        '1px solid #f0f2f5',
                      background:
                        item.is_read
                          ? '#ffffff'
                          : '#f5f7ff',
                      padding: '14px 16px',
                      textAlign: 'left',
                      cursor: 'pointer',
                      boxSizing: 'border-box',
                    }}
                    onMouseEnter={(event) => {
                      event.currentTarget.style.background =
                        item.is_read
                          ? '#f9fafb'
                          : '#eef2ff'
                    }}
                    onMouseLeave={(event) => {
                      event.currentTarget.style.background =
                        item.is_read
                          ? '#ffffff'
                          : '#f5f7ff'
                    }}
                  >

                    <div
                      style={{
                        display: 'flex',
                        gap: '10px',
                        alignItems: 'flex-start',
                      }}
                    >

                      {/* UNREAD DOT */}

                      <div
                        style={{
                          width: '8px',
                          height: '8px',
                          minWidth: '8px',
                          borderRadius: '50%',
                          background:
                            item.is_read
                              ? '#d0d5dd'
                              : '#4f46e5',
                          marginTop: '6px',
                        }}
                      />


                      {/* CONTENT */}

                      <div
                        style={{
                          flex: 1,
                          minWidth: 0,
                        }}
                      >

                        <div
                          style={{
                            fontSize: '14px',
                            fontWeight:
                              item.is_read
                                ? '600'
                                : '700',
                            color: '#172033',
                          }}
                        >
                          {item.title}
                        </div>

                        <div
                          style={{
                            marginTop: '4px',
                            fontSize: '13px',
                            lineHeight: '1.4',
                            color: '#475467',
                          }}
                        >
                          {item.message}
                        </div>

                        <div
                          style={{
                            marginTop: '7px',
                            fontSize: '11px',
                            color: '#98a2b3',
                          }}
                        >
                          {formatNotificationDate(
                            item.created_at
                          )}
                        </div>

                      </div>


                      {/* REMOVE BUTTON */}

                      <button
                        type="button"
                        onClick={(event) =>
                          handleDeleteNotification(
                            event,
                            item.id
                          )
                        }
                        aria-label={`Remove ${item.title}`}
                        title="Remove notification"
                        style={{
                          border: 'none',
                          background: 'transparent',
                          color: '#98a2b3',
                          fontSize: '16px',
                          cursor: 'pointer',
                          padding: '5px',
                          borderRadius: '6px',
                          flexShrink: 0,
                          lineHeight: 1,
                        }}
                        onMouseEnter={(event) => {
                          event.currentTarget.style.background =
                            '#fff1f0'
                          event.currentTarget.style.color =
                            '#d92d20'
                        }}
                        onMouseLeave={(event) => {
                          event.currentTarget.style.background =
                            'transparent'
                          event.currentTarget.style.color =
                            '#98a2b3'
                        }}
                      >
                        🗑️
                      </button>

                    </div>

                  </div>

                ))

              )}

            </div>

          </div>

        )}

      </header>
    </>
  )
}


/* =========================================================
   NOTIFICATION DATE FORMAT
========================================================= */

function formatNotificationDate(value) {
  if (!value) {
    return ''
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return ''
  }

  return date.toLocaleString()
}