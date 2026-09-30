import React, { useEffect, useMemo, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import { apiRequest } from '../services/api'
import { useNotification } from '../context/NotificationContext'

export default function AdminUsers() {

  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [busyId, setBusyId] = useState(null)
  const { showNotification } = useNotification()

  async function loadUsers() {

    try {

      setLoading(true)
      setError('')

      const data = await apiRequest(
        '/api/admin/users'
      )

      setUsers(data.users || [])

    } catch (err) {

      console.error(
        'Admin users error:',
        err
      )

      setError(
        err.message ||
        'Unable to load users'
      )

    } finally {

      setLoading(false)

    }
  }

  useEffect(() => {

    loadUsers()

  }, [])

  async function changeStatus(user) {

    const status =
      user.status === 'active'
        ? 'inactive'
        : 'active'

    try {

      setBusyId(user.id)

      await apiRequest(
        `/api/admin/users/${user.id}/status`,
        {
          method: 'PUT',

          body: JSON.stringify({
            status
          })
        }
      )

      await loadUsers()

    } catch (err) {

      console.error(
        'Status update error:',
        err
      )

      showNotification(
        err.message ||
        'Unable to update status'
      )

    } finally {

      setBusyId(null)

    }
  }

  async function deleteUser(user) {

    const confirmed =
      window.confirm(
        `Delete ${user.name}?\n\nThis cannot be undone.`
      )

    if (!confirmed) {
      return
    }

    try {

      setBusyId(user.id)

      await apiRequest(
        `/api/admin/users/${user.id}`,
        {
          method: 'DELETE'
        }
      )

      await loadUsers()

    } catch (err) {

      console.error(
        'Delete user error:',
        err
      )

      showNotification(
        err.message ||
        'Unable to update status'
      )

    } finally {

      setBusyId(null)

    }
  }

  const filteredUsers =
    useMemo(() => {

      const term =
        search
          .trim()
          .toLowerCase()

      return users.filter(
        (user) => {

          const matchesSearch =
            !term ||
            user.name
              ?.toLowerCase()
              .includes(term) ||
            user.email
              ?.toLowerCase()
              .includes(term) ||
            user.mobile
              ?.toLowerCase()
              .includes(term)

          const matchesRole =
            roleFilter === 'all' ||
            user.role === roleFilter

          const matchesStatus =
            statusFilter === 'all' ||
            user.status === statusFilter

          return (
            matchesSearch &&
            matchesRole &&
            matchesStatus
          )
        }
      )

    }, [
      users,
      search,
      roleFilter,
      statusFilter
    ])

  return (

    <DashboardLayout role="admin">

      <div
        className="page-heading-row"
      >

        <div>

          <h1>
            User Management
          </h1>

          <p>
            View and manage all LMS
            user accounts.
          </p>

        </div>

        <button
          type="button"
          className="btn btn-outline"
          onClick={loadUsers}
          disabled={loading}
        >
          {loading
            ? 'Loading...'
            : '↻ Refresh'}
        </button>

      </div>

      <div
        className="card"
        style={{
          padding: 18,
          marginBottom: 20,
          display: 'flex',
          gap: 10,
          flexWrap: 'wrap'
        }}
      >

        <input
          type="text"
          value={search}
          onChange={(e) =>
            setSearch(e.target.value)
          }
          placeholder="Search name, email or mobile..."
          style={{
            flex: 1,
            minWidth: 240,
            padding: '10px 12px',
            border:
              '1px solid var(--border)',
            borderRadius: 8
          }}
        />

        <select
          value={roleFilter}
          onChange={(e) =>
            setRoleFilter(e.target.value)
          }
          style={{
            padding: '10px 12px',
            border:
              '1px solid var(--border)',
            borderRadius: 8
          }}
        >

          <option value="all">
            All Roles
          </option>

          <option value="learner">
            Learner
          </option>

          <option value="trainer">
            Trainer
          </option>

          <option value="admin">
            Admin
          </option>

        </select>

        <select
          value={statusFilter}
          onChange={(e) =>
            setStatusFilter(e.target.value)
          }
          style={{
            padding: '10px 12px',
            border:
              '1px solid var(--border)',
            borderRadius: 8
          }}
        >

          <option value="all">
            All Status
          </option>

          <option value="active">
            Active
          </option>

          <option value="inactive">
            Inactive
          </option>

        </select>

      </div>

      {error ? (

        <div
          className="card"
          style={{
            padding: 24
          }}
        >

          <h2>
            Unable to load users
          </h2>

          <p>
            {error}
          </p>

          <button
            className="btn btn-primary"
            onClick={loadUsers}
          >
            Try Again
          </button>

        </div>

      ) : loading ? (

        <div
          className="card"
          style={{
            padding: 30,
            textAlign: 'center'
          }}
        >
          Loading users...
        </div>

      ) : filteredUsers.length === 0 ? (

        <div
          className="card"
          style={{
            padding: 30,
            textAlign: 'center'
          }}
        >
          No users found.
        </div>

      ) : (

        <div
          className="card"
          style={{
            padding: 0,
            overflowX: 'auto'
          }}
        >

          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              minWidth: 850
            }}
          >

            <thead>

              <tr>

                {[
                  'Name',
                  'Email',
                  'Mobile',
                  'Role',
                  'Status',
                  'Created',
                  'Actions'
                ].map(
                  (heading) => (

                    <th
                      key={heading}
                      style={{
                        textAlign: 'left',
                        padding:
                          '14px 16px',
                        borderBottom:
                          '1px solid var(--border)',
                        whiteSpace:
                          'nowrap'
                      }}
                    >
                      {heading}
                    </th>

                  )
                )}

              </tr>

            </thead>

            <tbody>

              {filteredUsers.map(
                (user) => (

                  <tr key={user.id}>

                    <td
                      style={{
                        padding:
                          '14px 16px'
                      }}
                    >
                      <strong>
                        {user.name}
                      </strong>
                    </td>

                    <td
                      style={{
                        padding:
                          '14px 16px'
                      }}
                    >
                      {user.email}
                    </td>

                    <td
                      style={{
                        padding:
                          '14px 16px'
                      }}
                    >
                      {user.mobile || '—'}
                    </td>

                    <td
                      style={{
                        padding:
                          '14px 16px',
                        textTransform:
                          'capitalize'
                      }}
                    >
                      {user.role}
                    </td>

                    <td
                      style={{
                        padding:
                          '14px 16px',
                        textTransform:
                          'capitalize'
                      }}
                    >
                      {user.status}
                    </td>

                    <td
                      style={{
                        padding:
                          '14px 16px'
                      }}
                    >
                      {user.created_at
                        ? new Date(
                            user.created_at
                          ).toLocaleDateString()
                        : '—'}
                    </td>

                    <td
                      style={{
                        padding:
                          '14px 16px'
                      }}
                    >

                      <div
                        style={{
                          display: 'flex',
                          gap: 6,
                          flexWrap: 'wrap'
                        }}
                      >

                        <button
                          className="btn btn-outline"
                          disabled={
                            busyId === user.id
                          }
                          onClick={() =>
                            changeStatus(user)
                          }
                        >
                          {user.status ===
                          'active'
                            ? 'Deactivate'
                            : 'Activate'}
                        </button>

                        <button
                          className="btn btn-outline"
                          disabled={
                            busyId === user.id ||
                            user.role === 'admin'
                          }
                          onClick={() =>
                            deleteUser(user)
                          }
                          style={{
                            color:
                              user.role ===
                              'admin'
                                ? 'var(--text-500)'
                                : '#c62828'
                          }}
                        >
                          Delete
                        </button>

                      </div>

                    </td>

                  </tr>

                )
              )}

            </tbody>

          </table>

        </div>

      )}

    </DashboardLayout>

  )
}