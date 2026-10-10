import { useEffect, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import { apiRequest } from '../services/api'

export default function AdminAttendance() {
  const [batches, setBatches] = useState([])
  const [attendance, setAttendance] = useState([])
  const [summary, setSummary] = useState([])

  const [selectedBatch, setSelectedBatch] = useState('')
  const [selectedDate, setSelectedDate] = useState('')

  const [loading, setLoading] = useState(true)
  const [loadingSummary, setLoadingSummary] = useState(true)
  const [editingId, setEditingId] = useState(null)

  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState({
    page: 1,
    pages: 1,
    total: 0,
  })

  // =====================================================
  // INITIAL LOAD
  // =====================================================

  useEffect(() => {
    fetchBatches()
  }, [])

  useEffect(() => {
    fetchAttendance()
  }, [selectedBatch, selectedDate, page])

  useEffect(() => {
    fetchSummary()
  }, [selectedBatch])

  // =====================================================
  // FETCH BATCHES
  // =====================================================

  async function fetchBatches() {
    try {
      const data = await apiRequest(
        '/api/admin/batches?limit=100',
        {
          method: 'GET',
        }
      )

      setBatches(data.batches || [])
    } catch (err) {
      setError(
        err.message ||
        'Failed to load batches.'
      )
    }
  }

  // =====================================================
  // FETCH ATTENDANCE RECORDS
  // =====================================================

  async function fetchAttendance() {
    setLoading(true)
    setError('')

    try {
      const params = new URLSearchParams()

      params.set('page', String(page))
      params.set('limit', '20')

      if (selectedBatch) {
        params.set(
          'batch_id',
          selectedBatch
        )
      }

      if (selectedDate) {
        params.set(
          'date',
          selectedDate
        )
      }

      const data = await apiRequest(
        `/api/admin/attendance?${params.toString()}`,
        {
          method: 'GET',
        }
      )

      setAttendance(
        data.attendance || []
      )

      setPagination(
        data.pagination || {
          page: 1,
          pages: 1,
          total: 0,
        }
      )
    } catch (err) {
      setAttendance([])

      setError(
        err.message ||
        'Failed to load attendance.'
      )
    } finally {
      setLoading(false)
    }
  }

  // =====================================================
  // FETCH ATTENDANCE SUMMARY
  // =====================================================

  async function fetchSummary() {
    setLoadingSummary(true)

    try {
      const endpoint =
        selectedBatch
          ? `/api/admin/attendance/summary?batch_id=${encodeURIComponent(
              selectedBatch
            )}`
          : '/api/admin/attendance/summary'

      const data = await apiRequest(
        endpoint,
        {
          method: 'GET',
        }
      )

      setSummary(
        data.learners || []
      )
    } catch (err) {
      setSummary([])

      setError(
        err.message ||
        'Failed to load attendance summary.'
      )
    } finally {
      setLoadingSummary(false)
    }
  }

  // =====================================================
  // FILTER HANDLERS
  // =====================================================

  function handleBatchChange(event) {
    setSelectedBatch(
      event.target.value
    )
    setPage(1)
    setMessage('')
  }

  function handleDateChange(event) {
    setSelectedDate(
      event.target.value
    )
    setPage(1)
    setMessage('')
  }

  function clearFilters() {
    setSelectedBatch('')
    setSelectedDate('')
    setPage(1)
    setMessage('')
  }

  // =====================================================
  // UPDATE ATTENDANCE
  // =====================================================

  async function updateAttendance(
    attendanceId,
    status
  ) {
    setEditingId(attendanceId)
    setError('')
    setMessage('')

    try {
      await apiRequest(
        `/api/admin/attendance/${attendanceId}`,
        {
          method: 'PUT',

          body: JSON.stringify({
            status,
          }),
        }
      )

      setMessage(
        'Attendance updated successfully.'
      )

      await Promise.all([
        fetchAttendance(),
        fetchSummary(),
      ])
    } catch (err) {
      setError(
        err.message ||
        'Failed to update attendance.'
      )
    } finally {
      setEditingId(null)
    }
  }

  // =====================================================
  // SUMMARY TOTALS
  // =====================================================

  const summaryTotals =
    summary.reduce(
      (totals, learner) => ({
        total:
          totals.total +
          Number(learner.total || 0),

        present:
          totals.present +
          Number(learner.present || 0),

        late:
          totals.late +
          Number(learner.late || 0),

        absent:
          totals.absent +
          Number(learner.absent || 0),
      }),
      {
        total: 0,
        present: 0,
        late: 0,
        absent: 0,
      }
    )

  const attended =
    summaryTotals.present +
    summaryTotals.late

  const overallPercentage =
    summaryTotals.total > 0
      ? (
          (attended /
            summaryTotals.total) *
          100
        ).toFixed(2)
      : '0.00'

  // =====================================================
  // PAGE
  // =====================================================

  return (
    <DashboardLayout role="admin">

      <div className="admin-attendance-page">

        {/* =================================================
            HEADER
        ================================================= */}

        <div className="page-header">

          <div>
            <h1>
              Attendance Management
            </h1>

            <p>
              View, monitor, and manage
              learner attendance.
            </p>
          </div>

        </div>

        {/* =================================================
            ALERTS
        ================================================= */}

        {error && (
          <div className="alert error">
            {error}
          </div>
        )}

        {message && (
          <div className="alert success">
            {message}
          </div>
        )}

        {/* =================================================
            SUMMARY CARDS
        ================================================= */}

        <div className="summary-grid">

          <div className="summary-card">
            <span className="summary-label">
              Total Records
            </span>

            <strong>
              {summaryTotals.total}
            </strong>
          </div>

          <div className="summary-card present-card">
            <span className="summary-label">
              Present
            </span>

            <strong>
              {summaryTotals.present}
            </strong>
          </div>

          <div className="summary-card late-card">
            <span className="summary-label">
              Late
            </span>

            <strong>
              {summaryTotals.late}
            </strong>
          </div>

          <div className="summary-card absent-card">
            <span className="summary-label">
              Absent
            </span>

            <strong>
              {summaryTotals.absent}
            </strong>
          </div>

          <div className="summary-card percentage-card">
            <span className="summary-label">
              Attendance %
            </span>

            <strong>
              {overallPercentage}%
            </strong>
          </div>

        </div>

        {/* =================================================
            FILTERS
        ================================================= */}

        <div className="filters-card">

          <div className="field">

            <label htmlFor="batch-filter">
              Batch
            </label>

            <select
              id="batch-filter"
              value={selectedBatch}
              onChange={
                handleBatchChange
              }
            >

              <option value="">
                All Batches
              </option>

              {batches.map(
                (batch) => (
                  <option
                    key={batch.id}
                    value={batch.id}
                  >
                    {batch.name}

                    {batch.course_title
                      ? ` — ${batch.course_title}`
                      : ''}
                  </option>
                )
              )}

            </select>

          </div>

          <div className="field">

            <label htmlFor="date-filter">
              Date
            </label>

            <input
              id="date-filter"
              type="date"
              value={selectedDate}
              onChange={
                handleDateChange
              }
            />

          </div>

          <div className="filter-actions">

            <button
              type="button"
              className="clear-button"
              onClick={clearFilters}
            >
              Clear Filters
            </button>

          </div>

        </div>

        {/* =================================================
            LEARNER SUMMARY
        ================================================= */}

        <div className="section-card">

          <div className="section-header">

            <div>
              <h2>
                Learner Attendance Summary
              </h2>

              <p>
                Attendance percentage is calculated
                from present and late records.
              </p>
            </div>

          </div>

          {loadingSummary ? (

            <div className="state-card">
              Loading summary...
            </div>

          ) : summary.length === 0 ? (

            <div className="state-card">
              No attendance summary available.
            </div>

          ) : (

            <div className="table-wrapper">

              <table className="attendance-table">

                <thead>
                  <tr>
                    <th>
                      Learner
                    </th>

                    <th>
                      Batch
                    </th>

                    <th>
                      Total
                    </th>

                    <th>
                      Present
                    </th>

                    <th>
                      Late
                    </th>

                    <th>
                      Absent
                    </th>

                    <th>
                      Attendance %
                    </th>
                  </tr>
                </thead>

                <tbody>

                  {summary.map(
                    (learner) => (
                      <tr
                        key={
                          `${learner.learner_id}-${learner.batch_id}`
                        }
                      >

                        <td>
                          <strong>
                            {learner.learner_name ||
                              'Unnamed learner'}
                          </strong>
                        </td>

                        <td>
                          {batches.find(
                            (batch) =>
                              String(
                                batch.id
                              ) ===
                              String(
                                learner.batch_id
                              )
                          )?.name || '—'}
                        </td>

                        <td>
                          {learner.total}
                        </td>

                        <td className="text-present">
                          {learner.present}
                        </td>

                        <td className="text-late">
                          {learner.late}
                        </td>

                        <td className="text-absent">
                          {learner.absent}
                        </td>

                        <td>
                          <span
                            className={
                              learner.attendance_percentage >= 75
                                ? 'percentage good'
                                : 'percentage warning'
                            }
                          >
                            {
                              learner.attendance_percentage
                            }%
                          </span>
                        </td>

                      </tr>
                    )
                  )}

                </tbody>

              </table>

            </div>

          )}

        </div>

        {/* =================================================
            ATTENDANCE RECORDS
        ================================================= */}

        <div className="section-card">

          <div className="section-header">

            <div>
              <h2>
                Attendance Records
              </h2>

              <p>
                Individual attendance records
                across all batches.
              </p>
            </div>

            <span className="record-count">
              {pagination.total || 0} records
            </span>

          </div>

          {loading ? (

            <div className="state-card">
              Loading attendance...
            </div>

          ) : attendance.length === 0 ? (

            <div className="state-card">
              No attendance records found.
            </div>

          ) : (

            <div className="table-wrapper">

              <table className="attendance-table">

                <thead>
                  <tr>
                    <th>
                      Learner
                    </th>

                    <th>
                      Batch
                    </th>

                    <th>
                      Trainer
                    </th>

                    <th>
                      Date
                    </th>

                    <th>
                      Status
                    </th>

                    <th>
                      Action
                    </th>
                  </tr>
                </thead>

                <tbody>

                  {attendance.map(
                    (record) => (

                      <tr
                        key={record.id}
                      >

                        <td>

                          <div className="learner-cell">

                            <strong>
                              {
                                record.learner_name ||
                                'Unnamed learner'
                              }
                            </strong>

                            <span>
                              {
                                record.learner_email ||
                                '—'
                              }
                            </span>

                          </div>

                        </td>

                        <td>
                          {record.batch_name ||
                            '—'}
                        </td>

                        <td>
                          {record.trainer_name ||
                            '—'}
                        </td>

                        <td>
                          {record.date ||
                            '—'}
                        </td>

                        <td>

                          <span
                            className={`status-badge ${record.status}`}
                          >
                            {record.status}
                          </span>

                        </td>

                        <td>

                          <div className="status-actions">

                            <button
                              type="button"
                              className={
                                record.status ===
                                'present'
                                  ? 'status-btn active present'
                                  : 'status-btn present'
                              }
                              disabled={
                                editingId ===
                                record.id
                              }
                              onClick={() =>
                                updateAttendance(
                                  record.id,
                                  'present'
                                )
                              }
                            >
                              Present
                            </button>

                            <button
                              type="button"
                              className={
                                record.status ===
                                'late'
                                  ? 'status-btn active late'
                                  : 'status-btn late'
                              }
                              disabled={
                                editingId ===
                                record.id
                              }
                              onClick={() =>
                                updateAttendance(
                                  record.id,
                                  'late'
                                )
                              }
                            >
                              Late
                            </button>

                            <button
                              type="button"
                              className={
                                record.status ===
                                'absent'
                                  ? 'status-btn active absent'
                                  : 'status-btn absent'
                              }
                              disabled={
                                editingId ===
                                record.id
                              }
                              onClick={() =>
                                updateAttendance(
                                  record.id,
                                  'absent'
                                )
                              }
                            >
                              Absent
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

          {/* =================================================
              PAGINATION
          ================================================= */}

          {pagination.pages > 1 && (

            <div className="pagination">

              <button
                type="button"
                disabled={
                  !pagination.has_previous
                }
                onClick={() =>
                  setPage(
                    (current) =>
                      Math.max(
                        current - 1,
                        1
                      )
                  )
                }
              >
                ← Previous
              </button>

              <span>
                Page {pagination.page} of{' '}
                {pagination.pages}
              </span>

              <button
                type="button"
                disabled={
                  !pagination.has_next
                }
                onClick={() =>
                  setPage(
                    (current) =>
                      Math.min(
                        current + 1,
                        pagination.pages
                      )
                  )
                }
              >
                Next →
              </button>

            </div>

          )}

        </div>

      </div>

      {/* =====================================================
          STYLES
      ===================================================== */}

      <style>{`

        .admin-attendance-page {
          padding: 24px;
          max-width: 1500px;
          margin: 0 auto;
        }

        .page-header {
          margin-bottom: 24px;
        }

        .page-header h1 {
          margin: 0 0 6px;
          font-size: 30px;
        }

        .page-header p {
          margin: 0;
          color: #6b7280;
        }

        .alert {
          padding: 12px 16px;
          border-radius: 10px;
          margin-bottom: 16px;
          font-weight: 600;
        }

        .alert.error {
          background: #fee2e2;
          color: #991b1b;
        }

        .alert.success {
          background: #dcfce7;
          color: #166534;
        }

        .summary-grid {
          display: grid;
          grid-template-columns:
            repeat(5, minmax(0, 1fr));
          gap: 14px;
          margin-bottom: 20px;
        }

        .summary-card {
          background: white;
          border-radius: 14px;
          padding: 20px;
          box-shadow:
            0 4px 18px
            rgba(0, 0, 0, 0.06);
          border-left: 4px solid #111827;
        }

        .summary-card strong {
          display: block;
          margin-top: 8px;
          font-size: 28px;
          color: #111827;
        }

        .summary-label {
          color: #6b7280;
          font-size: 13px;
          font-weight: 700;
          text-transform: uppercase;
        }

        .present-card {
          border-left-color: #22c55e;
        }

        .late-card {
          border-left-color: #f59e0b;
        }

        .absent-card {
          border-left-color: #ef4444;
        }

        .percentage-card {
          border-left-color: #6366f1;
        }

        .filters-card {
          display: grid;
          grid-template-columns:
            minmax(240px, 1fr)
            220px
            auto;
          align-items: end;
          gap: 18px;
          background: white;
          padding: 20px;
          border-radius: 14px;
          margin-bottom: 20px;
          box-shadow:
            0 4px 18px
            rgba(0, 0, 0, 0.06);
        }

        .field {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .field label {
          font-weight: 700;
          color: #374151;
        }

        .field select,
        .field input {
          width: 100%;
          box-sizing: border-box;
          padding: 11px 12px;
          border: 1px solid #d1d5db;
          border-radius: 9px;
          background: white;
          font-size: 14px;
        }

        .filter-actions {
          display: flex;
          justify-content: flex-end;
        }

        .clear-button {
          border: 1px solid #d1d5db;
          background: white;
          color: #374151;
          padding: 11px 18px;
          border-radius: 9px;
          font-weight: 700;
          cursor: pointer;
        }

        .clear-button:hover {
          background: #f9fafb;
        }

        .section-card {
          background: white;
          border-radius: 14px;
          margin-bottom: 20px;
          box-shadow:
            0 4px 18px
            rgba(0, 0, 0, 0.06);
          overflow: hidden;
        }

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 20px;
          padding: 20px;
          border-bottom: 1px solid #e5e7eb;
        }

        .section-header h2 {
          margin: 0 0 5px;
          font-size: 20px;
        }

        .section-header p {
          margin: 0;
          color: #6b7280;
          font-size: 14px;
        }

        .record-count {
          color: #6b7280;
          font-size: 14px;
          font-weight: 600;
        }

        .table-wrapper {
          overflow-x: auto;
        }

        .attendance-table {
          width: 100%;
          border-collapse: collapse;
        }

        .attendance-table th,
        .attendance-table td {
          padding: 14px 16px;
          text-align: left;
          border-bottom: 1px solid #e5e7eb;
        }

        .attendance-table th {
          background: #f9fafb;
          color: #6b7280;
          font-size: 12px;
          text-transform: uppercase;
          white-space: nowrap;
        }

        .attendance-table td {
          color: #374151;
          font-size: 14px;
        }

        .learner-cell {
          display: flex;
          flex-direction: column;
          gap: 3px;
        }

        .learner-cell span {
          color: #6b7280;
          font-size: 12px;
        }

        .text-present {
          color: #166534 !important;
          font-weight: 700;
        }

        .text-late {
          color: #92400e !important;
          font-weight: 700;
        }

        .text-absent {
          color: #991b1b !important;
          font-weight: 700;
        }

        .percentage {
          display: inline-block;
          padding: 5px 9px;
          border-radius: 999px;
          font-weight: 700;
          font-size: 12px;
        }

        .percentage.good {
          background: #dcfce7;
          color: #166534;
        }

        .percentage.warning {
          background: #fef3c7;
          color: #92400e;
        }

        .status-badge {
          display: inline-block;
          padding: 5px 10px;
          border-radius: 999px;
          font-size: 12px;
          font-weight: 700;
          text-transform: capitalize;
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

        .status-actions {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
        }

        .status-btn {
          border: 1px solid #d1d5db;
          background: white;
          border-radius: 7px;
          padding: 6px 9px;
          cursor: pointer;
          font-weight: 600;
          font-size: 11px;
        }

        .status-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .status-btn.present.active {
          background: #dcfce7;
          border-color: #22c55e;
          color: #166534;
        }

        .status-btn.late.active {
          background: #fef3c7;
          border-color: #f59e0b;
          color: #92400e;
        }

        .status-btn.absent.active {
          background: #fee2e2;
          border-color: #ef4444;
          color: #991b1b;
        }

        .state-card {
          padding: 50px 20px;
          text-align: center;
          color: #6b7280;
        }

        .pagination {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 18px;
          padding: 18px;
        }

        .pagination button {
          border: 1px solid #d1d5db;
          background: white;
          border-radius: 8px;
          padding: 8px 14px;
          cursor: pointer;
          font-weight: 600;
        }

        .pagination button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .pagination span {
          color: #6b7280;
          font-size: 14px;
        }

        @media (max-width: 1100px) {

          .summary-grid {
            grid-template-columns:
              repeat(3, minmax(0, 1fr));
          }

          .filters-card {
            grid-template-columns: 1fr 1fr;
          }

          .filter-actions {
            justify-content: flex-start;
          }

        }

        @media (max-width: 700px) {

          .admin-attendance-page {
            padding: 16px;
          }

          .summary-grid {
            grid-template-columns: 1fr 1fr;
          }

          .filters-card {
            grid-template-columns: 1fr;
          }

          .section-header {
            align-items: flex-start;
            flex-direction: column;
          }

        }

      `}</style>

    </DashboardLayout>
  )
}