import { useEffect, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import { apiRequest } from '../services/api'

function LearnerAttendance() {
  const [attendance, setAttendance] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchAttendance = async () => {
    try {
      setLoading(true)
      setError('')

      const data = await apiRequest('/api/learner/attendance')

      console.log('ATTENDANCE API RESPONSE:', data)

      // Support different possible response names
      const records =
        data?.attendance ||
        data?.records ||
        data?.attendance_records ||
        data?.attendanceHistory ||
        []

      setAttendance(
        Array.isArray(records) ? records : []
      )

      const apiSummary = data?.summary || {}

      // Get counts from API
      const total = Number(
        apiSummary.total ??
        apiSummary.total_classes ??
        records.length ??
        0
      )

      const present = Number(
        apiSummary.present ??
        apiSummary.present_count ??
        0
      )

      const late = Number(
        apiSummary.late ??
        apiSummary.late_count ??
        0
      )

      const absent = Number(
        apiSummary.absent ??
        apiSummary.absent_count ??
        0
      )

      // Present + Late are considered attended
      const calculatedPercentage =
        total > 0
          ? Number(
              (
                ((present + late) / total) *
                100
              ).toFixed(2)
            )
          : 0

      setSummary({
        total,
        present,
        late,
        absent,
        percentage: calculatedPercentage
      })

    } catch (err) {
      console.error(
        'Attendance loading error:',
        err
      )

      setError(
        err?.message ||
        'Failed to load attendance'
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAttendance()
  }, [])

  const getStatusClass = (status) => {
    const value = String(
      status || ''
    ).toLowerCase()

    if (value === 'present') {
      return 'present'
    }

    if (value === 'late') {
      return 'late'
    }

    return 'absent'
  }

  const formatStatus = (status) => {
    if (!status) {
      return '-'
    }

    const value = String(status)

    return (
      value.charAt(0).toUpperCase() +
      value.slice(1).toLowerCase()
    )
  }

  const formatDate = (date) => {
    if (!date) {
      return '-'
    }

    const parsedDate = new Date(date)

    if (
      Number.isNaN(
        parsedDate.getTime()
      )
    ) {
      return date
    }

    return parsedDate.toLocaleDateString()
  }

  return (
    <DashboardLayout role="learner">

      <div className="attendance-page">

        {/* HEADER */}

        <div className="page-header">

          <div>
            <h1>My Attendance</h1>

            <p>
              View your attendance history and
              attendance percentage.
            </p>
          </div>

          <button
            type="button"
            className="refresh-button"
            onClick={fetchAttendance}
            disabled={loading}
          >
            {loading
              ? 'Loading...'
              : '↻ Refresh'}
          </button>

        </div>

        {/* LOADING */}

        {loading && (
          <div className="state-card">

            <div className="loading-icon">
              ⏳
            </div>

            <h3>
              Loading attendance...
            </h3>

            <p>
              Please wait while we load
              your attendance.
            </p>

          </div>
        )}

        {/* ERROR */}

        {!loading && error && (
          <div className="state-card error-card">

            <div className="error-icon">
              ⚠️
            </div>

            <h3>
              Unable to load attendance
            </h3>

            <p>
              {error}
            </p>

            <button
              type="button"
              className="retry-button"
              onClick={fetchAttendance}
            >
              Try Again
            </button>

          </div>
        )}

        {/* SUMMARY */}

        {!loading &&
          !error &&
          summary && (

            <div className="summary-grid">

              <div className="summary-card">

                <div className="summary-icon">
                  📚
                </div>

                <div>
                  <span>
                    Total Classes
                  </span>

                  <strong>
                    {summary.total}
                  </strong>
                </div>

              </div>

              <div className="summary-card">

                <div className="summary-icon present-icon">
                  ✅
                </div>

                <div>
                  <span>
                    Present
                  </span>

                  <strong>
                    {summary.present}
                  </strong>
                </div>

              </div>

              <div className="summary-card">

                <div className="summary-icon late-icon">
                  ⏰
                </div>

                <div>
                  <span>
                    Late
                  </span>

                  <strong>
                    {summary.late}
                  </strong>
                </div>

              </div>

              <div className="summary-card">

                <div className="summary-icon absent-icon">
                  ❌
                </div>

                <div>
                  <span>
                    Absent
                  </span>

                  <strong>
                    {summary.absent}
                  </strong>
                </div>

              </div>

              <div className="summary-card percentage-card">

                <div className="summary-icon percentage-icon">
                  📊
                </div>

                <div>
                  <span>
                    Attendance
                  </span>

                  <strong>
                    {summary.percentage}%
                  </strong>
                </div>

              </div>

            </div>
          )}

        {/* ATTENDANCE HISTORY */}

        {!loading &&
          !error &&
          attendance.length > 0 && (

            <div className="attendance-card">

              <div className="card-header">

                <div>
                  <h2>
                    Attendance History
                  </h2>

                  <p>
                    Your attendance records
                  </p>
                </div>

                <span className="record-count">
                  {attendance.length}{' '}
                  {attendance.length === 1
                    ? 'record'
                    : 'records'}
                </span>

              </div>

              <div className="table-wrapper">

                <table>

                  <thead>

                    <tr>

                      <th>
                        #
                      </th>

                      <th>
                        Date
                      </th>

                      <th>
                        Batch
                      </th>

                      <th>
                        Status
                      </th>

                    </tr>

                  </thead>

                  <tbody>

                    {attendance.map(
                      (record, index) => (

                        <tr
                          key={
                            record.id ??
                            `${record.date}-${index}`
                          }
                        >

                          <td className="number-cell">
                            {index + 1}
                          </td>

                          <td>
                            {formatDate(
                              record.date
                            )}
                          </td>

                          <td>
                            {record.batch_name ||
                              record.batchName ||
                              record.batch ||
                              '-'}
                          </td>

                          <td>

                            <span
                              className={`status-badge ${getStatusClass(
                                record.status
                              )}`}
                            >
                              {formatStatus(
                                record.status
                              )}
                            </span>

                          </td>

                        </tr>

                      )
                    )}

                  </tbody>

                </table>

              </div>

            </div>
          )}

        {/* NO RECORDS */}

        {!loading &&
          !error &&
          attendance.length === 0 &&
          summary?.total === 0 && (

            <div className="state-card">

              <div className="empty-icon">
                📋
              </div>

              <h3>
                No attendance records
              </h3>

              <p>
                Your attendance will appear
                here once your trainer marks
                attendance.
              </p>

            </div>
          )}

        {/* CSS */}

        <style>{`

          .attendance-page {
            padding: 28px;
            max-width: 1400px;
            margin: 0 auto;
          }

          .page-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 20px;
            margin-bottom: 24px;
          }

          .page-header h1 {
            margin: 0 0 8px;
            font-size: 30px;
            font-weight: 700;
            color: #0f172a;
          }

          .page-header p {
            margin: 0;
            color: #64748b;
            font-size: 15px;
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

          .refresh-button:hover:not(:disabled) {
            background: #1d4ed8;
          }

          .refresh-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
          }

          .summary-grid {
            display: grid;
            grid-template-columns:
              repeat(5, minmax(130px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
          }

          .summary-card {
            display: flex;
            align-items: center;
            gap: 14px;
            background: white;
            border-radius: 14px;
            padding: 20px;
            box-shadow:
              0 2px 12px
              rgba(15, 23, 42, 0.06);
          }

          .summary-icon {
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 12px;
            background: #eff6ff;
            font-size: 20px;
          }

          .present-icon {
            background: #dcfce7;
          }

          .late-icon {
            background: #fef3c7;
          }

          .absent-icon {
            background: #fee2e2;
          }

          .percentage-icon {
            background: #dbeafe;
          }

          .summary-card span {
            display: block;
            color: #64748b;
            font-size: 13px;
            margin-bottom: 6px;
          }

          .summary-card strong {
            display: block;
            font-size: 26px;
            color: #0f172a;
          }

          .percentage-card strong {
            color: #2563eb;
          }

          .state-card {
            background: white;
            border-radius: 14px;
            padding: 40px 25px;
            text-align: center;
            box-shadow:
              0 2px 12px
              rgba(15, 23, 42, 0.06);
          }

          .state-card h3 {
            margin: 10px 0 8px;
            color: #0f172a;
          }

          .state-card p {
            color: #64748b;
          }

          .loading-icon,
          .empty-icon,
          .error-icon {
            font-size: 40px;
          }

          .error-card {
            background: #fef2f2;
            border: 1px solid #fecaca;
          }

          .retry-button {
            border: none;
            border-radius: 9px;
            padding: 10px 18px;
            background: #dc2626;
            color: white;
            cursor: pointer;
            font-weight: 600;
          }

          .attendance-card {
            background: white;
            border-radius: 14px;
            overflow: hidden;
            box-shadow:
              0 2px 12px
              rgba(15, 23, 42, 0.06);
          }

          .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            border-bottom: 1px solid #e2e8f0;
          }

          .card-header h2 {
            margin: 0 0 4px;
            font-size: 19px;
            color: #0f172a;
          }

          .card-header p {
            margin: 0;
            color: #64748b;
            font-size: 13px;
          }

          .record-count {
            color: #64748b;
            background: #f8fafc;
            padding: 7px 12px;
            border-radius: 8px;
            font-size: 14px;
          }

          .table-wrapper {
            overflow-x: auto;
          }

          table {
            width: 100%;
            border-collapse: collapse;
          }

          th {
            text-align: left;
            padding: 14px 20px;
            background: #f8fafc;
            color: #475569;
            font-size: 13px;
          }

          td {
            padding: 16px 20px;
            border-top: 1px solid #e2e8f0;
            color: #334155;
          }

          tbody tr:hover {
            background: #f8fafc;
          }

          .number-cell {
            color: #94a3b8;
            width: 50px;
          }

          .status-badge {
            display: inline-block;
            padding: 5px 11px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
          }

          .status-badge.present {
            background: #dcfce7;
            color: #166534;
          }

          .status-badge.late {
            background: #fef3c7;
            color: #92400e;
          }

          .status-badge.absent {
            background: #fee2e2;
            color: #991b1b;
          }

          @media (max-width: 1100px) {

            .summary-grid {
              grid-template-columns:
                repeat(3, 1fr);
            }

          }

          @media (max-width: 800px) {

            .summary-grid {
              grid-template-columns:
                repeat(2, 1fr);
            }

          }

          @media (max-width: 600px) {

            .attendance-page {
              padding: 16px;
            }

            .page-header {
              flex-direction: column;
            }

            .refresh-button {
              width: 100%;
            }

            .summary-grid {
              grid-template-columns: 1fr;
            }

            .card-header {
              flex-direction: column;
              align-items: flex-start;
              gap: 12px;
            }

            th,
            td {
              padding: 12px;
            }

          }

        `}</style>

      </div>

    </DashboardLayout>
  )
}

export default LearnerAttendance