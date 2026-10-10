import { useEffect, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import { apiRequest } from '../services/api'

export default function TrainerAttendance() {
  const [batches, setBatches] = useState([])
  const [selectedBatch, setSelectedBatch] = useState('')
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split('T')[0]
  )
  const [learners, setLearners] = useState([])

  const [loadingBatches, setLoadingBatches] = useState(true)
  const [loadingAttendance, setLoadingAttendance] = useState(false)
  const [saving, setSaving] = useState(false)

  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  // =====================================================
  // LOAD TRAINER BATCHES
  // =====================================================

  useEffect(() => {
    fetchBatches()
  }, [])

  // =====================================================
  // LOAD ATTENDANCE WHEN BATCH OR DATE CHANGES
  // =====================================================

  useEffect(() => {
    if (selectedBatch && selectedDate) {
      fetchAttendance()
    } else {
      setLearners([])
    }
  }, [selectedBatch, selectedDate])

  // =====================================================
  // FETCH BATCHES
  // =====================================================

  async function fetchBatches() {
    setLoadingBatches(true)
    setError('')

    try {
      const data = await apiRequest(
        '/api/trainer/batches',
        {
          method: 'GET',
        }
      )

      setBatches(data.batches || [])

      if (data.batches?.length > 0) {
        setSelectedBatch(
          String(data.batches[0].id)
        )
      }
    } catch (err) {
      setError(
        err.message ||
        'Failed to load your batches.'
      )
    } finally {
      setLoadingBatches(false)
    }
  }

  // =====================================================
  // FETCH ATTENDANCE
  // =====================================================

  async function fetchAttendance() {
    setLoadingAttendance(true)
    setError('')
    setMessage('')

    try {
      const data = await apiRequest(
        `/api/trainer/batches/${selectedBatch}/attendance?date=${encodeURIComponent(
          selectedDate
        )}`,
        {
          method: 'GET',
        }
      )

      setLearners(data.learners || [])
    } catch (err) {
      setLearners([])

      setError(
        err.message ||
        'Failed to load attendance.'
      )
    } finally {
      setLoadingAttendance(false)
    }
  }

  // =====================================================
  // UPDATE LOCAL ATTENDANCE STATUS
  // =====================================================

  function updateStatus(learnerId, status) {
    setLearners((current) =>
      current.map((learner) =>
        learner.learner_id === learnerId
          ? {
              ...learner,
              status,
            }
          : learner
      )
    )

    setError('')
    setMessage('')
  }

  // =====================================================
  // SAVE ATTENDANCE
  // =====================================================

  async function saveAttendance() {
    if (!selectedBatch) {
      setError('Please select a batch.')
      return
    }

    if (!selectedDate) {
      setError('Please select a date.')
      return
    }

    if (!learners.length) {
      setError(
        'There are no learners in this batch.'
      )
      return
    }

    const incomplete = learners.some(
      (learner) => !learner.status
    )

    if (incomplete) {
      setError(
        'Please mark attendance for every learner.'
      )
      return
    }

    setSaving(true)
    setError('')
    setMessage('')

    try {
      await apiRequest(
        `/api/trainer/batches/${selectedBatch}/attendance`,
        {
          method: 'POST',

          body: JSON.stringify({
            date: selectedDate,

            attendance: learners.map(
              (learner) => ({
                learner_id:
                  learner.learner_id,

                status:
                  learner.status,
              })
            ),
          }),
        }
      )

      setMessage(
        'Attendance saved successfully.'
      )

      await fetchAttendance()
    } catch (err) {
      setError(
        err.message ||
        'Failed to save attendance.'
      )
    } finally {
      setSaving(false)
    }
  }

  // =====================================================
  // SELECTED BATCH
  // =====================================================

  const selectedBatchData =
    batches.find(
      (batch) =>
        String(batch.id) ===
        String(selectedBatch)
    )

  // =====================================================
  // ATTENDANCE COUNTS
  // =====================================================

  const presentCount =
    learners.filter(
      (learner) =>
        learner.status === 'present'
    ).length

  const absentCount =
    learners.filter(
      (learner) =>
        learner.status === 'absent'
    ).length

  const lateCount =
    learners.filter(
      (learner) =>
        learner.status === 'late'
    ).length

  // =====================================================
  // PAGE
  // =====================================================

  return (
    <DashboardLayout role="trainer">

      <div className="attendance-page">

        {/* =================================================
            PAGE HEADER
        ================================================= */}

        <div className="page-header">

          <div>
            <h1>Attendance</h1>

            <p>
              Mark and manage attendance
              for your batches.
            </p>
          </div>

        </div>

        {/* =================================================
            ERROR MESSAGE
        ================================================= */}

        {error && (
          <div className="alert error">
            {error}
          </div>
        )}

        {/* =================================================
            SUCCESS MESSAGE
        ================================================= */}

        {message && (
          <div className="alert success">
            {message}
          </div>
        )}

        {/* =================================================
            FILTERS
        ================================================= */}

        <div className="filters-card">

          <div className="field">

            <label htmlFor="batch">
              Batch
            </label>

            <select
              id="batch"
              value={selectedBatch}
              onChange={(event) =>
                setSelectedBatch(
                  event.target.value
                )
              }
              disabled={loadingBatches}
            >

              {loadingBatches ? (
                <option value="">
                  Loading batches...
                </option>
              ) : batches.length === 0 ? (
                <option value="">
                  No batches available
                </option>
              ) : (
                batches.map((batch) => (
                  <option
                    key={batch.id}
                    value={batch.id}
                  >
                    {batch.name}

                    {batch.course_title
                      ? ` — ${batch.course_title}`
                      : ''}
                  </option>
                ))
              )}

            </select>

          </div>

          <div className="field">

            <label htmlFor="attendance-date">
              Date
            </label>

            <input
              id="attendance-date"
              type="date"
              value={selectedDate}
              onChange={(event) =>
                setSelectedDate(
                  event.target.value
                )
              }
            />

          </div>

        </div>

        {/* =================================================
            BATCH INFORMATION
        ================================================= */}

        {selectedBatchData && (

          <div className="batch-info">

            <div>

              <strong>
                {selectedBatchData.name}
              </strong>

              {selectedBatchData.course_title && (
                <span>
                  {selectedBatchData.course_title}
                </span>
              )}

            </div>

            <div className="summary">

              <span>
                Total:{' '}
                <strong>
                  {learners.length}
                </strong>
              </span>

              <span className="present">
                Present:{' '}
                <strong>
                  {presentCount}
                </strong>
              </span>

              <span className="late">
                Late:{' '}
                <strong>
                  {lateCount}
                </strong>
              </span>

              <span className="absent">
                Absent:{' '}
                <strong>
                  {absentCount}
                </strong>
              </span>

            </div>

          </div>

        )}

        {/* =================================================
            LOADING
        ================================================= */}

        {loadingAttendance ? (

          <div className="state-card">
            Loading attendance...
          </div>

        ) : learners.length === 0 ? (

          <div className="state-card">

            {selectedBatch
              ? 'No learners are assigned to this batch.'
              : 'Select a batch to view attendance.'}

          </div>

        ) : (

          /* =================================================
             ATTENDANCE TABLE
          ================================================= */

          <div className="attendance-card">

            <div className="table-header">

              <div>

                <h2>
                  Learner Attendance
                </h2>

                <p>
                  {selectedDate}
                </p>

              </div>

              <button
                className="save-button"
                onClick={saveAttendance}
                disabled={saving}
              >

                {saving
                  ? 'Saving...'
                  : 'Save Attendance'}

              </button>

            </div>

            <div className="attendance-table-wrapper">

              <table className="attendance-table">

                <thead>

                  <tr>

                    <th>
                      #
                    </th>

                    <th>
                      Learner
                    </th>

                    <th>
                      Email
                    </th>

                    <th>
                      Status
                    </th>

                  </tr>

                </thead>

                <tbody>

                  {learners.map(
                    (learner, index) => (

                      <tr
                        key={
                          learner.learner_id
                        }
                      >

                        <td>
                          {index + 1}
                        </td>

                        <td>

                          <strong>
                            {learner.name ||
                              'Unnamed learner'}
                          </strong>

                        </td>

                        <td>
                          {learner.email ||
                            '—'}
                        </td>

                        <td>

                          <div className="status-buttons">

                            {/* PRESENT */}

                            <button
                              type="button"
                              className={
                                learner.status ===
                                'present'
                                  ? 'status-btn active present'
                                  : 'status-btn present'
                              }
                              onClick={() =>
                                updateStatus(
                                  learner.learner_id,
                                  'present'
                                )
                              }
                            >
                              Present
                            </button>

                            {/* LATE */}

                            <button
                              type="button"
                              className={
                                learner.status ===
                                'late'
                                  ? 'status-btn active late'
                                  : 'status-btn late'
                              }
                              onClick={() =>
                                updateStatus(
                                  learner.learner_id,
                                  'late'
                                )
                              }
                            >
                              Late
                            </button>

                            {/* ABSENT */}

                            <button
                              type="button"
                              className={
                                learner.status ===
                                'absent'
                                  ? 'status-btn active absent'
                                  : 'status-btn absent'
                              }
                              onClick={() =>
                                updateStatus(
                                  learner.learner_id,
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

          </div>

        )}

      </div>

      {/* =====================================================
          PAGE STYLES
      ===================================================== */}

      <style>{`

        .attendance-page {
          padding: 24px;
          max-width: 1400px;
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

        .filters-card {
          display: grid;
          grid-template-columns: 1fr 220px;
          gap: 20px;
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

        .batch-info {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 20px;
          padding: 18px 20px;
          margin-bottom: 20px;
          border-radius: 14px;
          background: #f8fafc;
          border: 1px solid #e5e7eb;
        }

        .batch-info > div:first-child {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .batch-info span {
          color: #6b7280;
          font-size: 14px;
        }

        .summary {
          display: flex;
          gap: 18px;
          flex-wrap: wrap;
        }

        .summary span {
          color: #374151;
        }

        .summary .present {
          color: #166534;
        }

        .summary .late {
          color: #92400e;
        }

        .summary .absent {
          color: #991b1b;
        }

        .attendance-card {
          background: white;
          border-radius: 14px;
          box-shadow:
            0 4px 18px
            rgba(0, 0, 0, 0.06);
          overflow: hidden;
        }

        .table-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 20px;
          padding: 20px;
          border-bottom: 1px solid #e5e7eb;
        }

        .table-header h2 {
          margin: 0 0 5px;
          font-size: 20px;
        }

        .table-header p {
          margin: 0;
          color: #6b7280;
        }

        .save-button {
          border: none;
          border-radius: 9px;
          padding: 11px 18px;
          background: #111827;
          color: white;
          font-weight: 700;
          cursor: pointer;
        }

        .save-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .attendance-table-wrapper {
          overflow-x: auto;
        }

        .attendance-table {
          width: 100%;
          border-collapse: collapse;
        }

        .attendance-table th,
        .attendance-table td {
          padding: 15px 18px;
          text-align: left;
          border-bottom: 1px solid #e5e7eb;
        }

        .attendance-table th {
          background: #f9fafb;
          font-size: 13px;
          text-transform: uppercase;
          color: #6b7280;
        }

        .attendance-table td {
          color: #374151;
        }

        .status-buttons {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .status-btn {
          border: 1px solid #d1d5db;
          background: white;
          border-radius: 8px;
          padding: 7px 12px;
          cursor: pointer;
          font-weight: 600;
          font-size: 13px;
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
          background: white;
          border-radius: 14px;
          color: #6b7280;
          box-shadow:
            0 4px 18px
            rgba(0, 0, 0, 0.06);
        }

        @media (max-width: 800px) {

          .filters-card {
            grid-template-columns: 1fr;
          }

          .batch-info,
          .table-header {
            align-items: flex-start;
            flex-direction: column;
          }

        }

      `}</style>

    </DashboardLayout>
  )
}