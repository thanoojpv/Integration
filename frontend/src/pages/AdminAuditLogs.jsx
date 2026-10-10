import { useEffect, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import { apiRequest } from '../services/api'

export default function AdminAuditLogs() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState(null)

  const fetchAuditLogs = async (selectedPage = 1) => {
    try {
      setLoading(true)
      setError('')

      const data = await apiRequest(
        `/api/admin/audit-logs?page=${selectedPage}&per_page=20`
      )

      setLogs(data.audit_logs || [])
      setPagination(data.pagination || null)
      setPage(selectedPage)
    } catch (err) {
      setError(err.message || 'Failed to load audit logs')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAuditLogs(1)
  }, [])

  return (
    <DashboardLayout role="admin">
      <div className="audit-page">
        <div className="audit-header">
          <div>
            <h1>Audit Logs</h1>
            <p>
              Track important actions performed in DevSprint LMS.
            </p>
          </div>

          <button
            className="refresh-button"
            onClick={() => fetchAuditLogs(page)}
            disabled={loading}
          >
            ↻ Refresh
          </button>
        </div>

        {loading && (
          <div className="state-card">
            Loading audit logs...
          </div>
        )}

        {error && !loading && (
          <div className="state-card error-card">
            {error}
          </div>
        )}

        {!loading && !error && logs.length === 0 && (
          <div className="state-card">
            No audit logs found.
          </div>
        )}

        {!loading && !error && logs.length > 0 && (
          <>
            <div className="audit-card">
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>User</th>
                      <th>Action</th>
                      <th>Entity</th>
                      <th>Description</th>
                      <th>IP Address</th>
                    </tr>
                  </thead>

                  <tbody>
                    {logs.map((log) => (
                      <tr key={log.id}>
                        <td>
                          {log.created_at
                            ? new Date(
                                log.created_at
                              ).toLocaleString()
                            : '-'}
                        </td>

                        <td>
                          <strong>
                            {log.user_name || 'System'}
                          </strong>
                        </td>

                        <td>
                          <span className="action-badge">
                            {log.action}
                          </span>
                        </td>

                        <td>
                          <div>
                            {log.entity_type}
                          </div>

                          {log.entity_id && (
                            <small>
                              ID: {log.entity_id}
                            </small>
                          )}
                        </td>

                        <td>
                          {log.description}
                        </td>

                        <td>
                          {log.ip_address || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {pagination && pagination.pages > 1 && (
              <div className="pagination">
                <button
                  onClick={() =>
                    fetchAuditLogs(page - 1)
                  }
                  disabled={!pagination.has_prev || loading}
                >
                  ← Previous
                </button>

                <span>
                  Page {pagination.page} of{' '}
                  {pagination.pages}
                </span>

                <button
                  onClick={() =>
                    fetchAuditLogs(page + 1)
                  }
                  disabled={!pagination.has_next || loading}
                >
                  Next →
                </button>
              </div>
            )}
          </>
        )}

        <style>{`
          .audit-page {
            padding: 28px;
          }

          .audit-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 20px;
            margin-bottom: 24px;
          }

          .audit-header h1 {
            margin: 0 0 8px;
            font-size: 30px;
          }

          .audit-header p {
            margin: 0;
            color: #64748b;
          }

          .refresh-button {
            border: none;
            border-radius: 10px;
            padding: 11px 18px;
            cursor: pointer;
            font-weight: 600;
            background: #2563eb;
            color: white;
          }

          .refresh-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
          }

          .state-card {
            background: white;
            border-radius: 14px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06);
          }

          .error-card {
            color: #b91c1c;
            background: #fef2f2;
          }

          .audit-card {
            background: white;
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06);
          }

          .table-wrapper {
            width: 100%;
            overflow-x: auto;
          }

          table {
            width: 100%;
            border-collapse: collapse;
            min-width: 1000px;
          }

          th {
            text-align: left;
            padding: 15px 16px;
            background: #f8fafc;
            color: #475569;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
          }

          td {
            padding: 16px;
            border-top: 1px solid #e2e8f0;
            color: #334155;
            font-size: 14px;
            vertical-align: top;
          }

          tr:hover td {
            background: #f8fafc;
          }

          td small {
            color: #94a3b8;
          }

          .action-badge {
            display: inline-block;
            padding: 5px 9px;
            border-radius: 999px;
            background: #dbeafe;
            color: #1d4ed8;
            font-size: 12px;
            font-weight: 700;
          }

          .pagination {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
            margin-top: 20px;
          }

          .pagination button {
            border: 1px solid #cbd5e1;
            background: white;
            padding: 9px 14px;
            border-radius: 8px;
            cursor: pointer;
          }

          .pagination button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
        `}</style>
      </div>
    </DashboardLayout>
  )
}