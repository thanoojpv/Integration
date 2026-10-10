import React, {
  useEffect,
  useState,
} from 'react'

import DashboardLayout from '../components/DashboardLayout'
import { apiRequest } from '../services/api'

export default function AdminBatches() {
  const [batches, setBatches] = useState([])
  const [courses, setCourses] = useState([])
  const [trainers, setTrainers] = useState([])
  const [learners, setLearners] = useState([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const [showCreate, setShowCreate] = useState(false)
  const [showRoster, setShowRoster] = useState(false)

  const [selectedBatch, setSelectedBatch] = useState(null)
  const [roster, setRoster] = useState([])

  const [form, setForm] = useState({
    name: '',
    course_id: '',
    trainer_id: '',
    start_date: '',
    end_date: '',
    status: 'active',
  })

  const [selectedLearner, setSelectedLearner] = useState('')

  async function loadData() {
    try {
      setLoading(true)
      setError('')

      const [
        batchData,
        courseData,
        trainerData,
        learnerData,
      ] = await Promise.all([
        apiRequest('/api/admin/batches'),
        apiRequest('/api/admin/courses'),
        apiRequest('/api/admin/trainers'),
        apiRequest('/api/admin/learners?limit=100'),
      ])

      setBatches(batchData.batches || [])
      setCourses(courseData.courses || [])
      setTrainers(trainerData.trainers || [])
      setLearners(learnerData.learners || [])
    } catch (err) {
      console.error('Admin batches error:', err)

      setError(
        err.message ||
        'Unable to load batch management data'
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  function handleChange(event) {
    const {
      name,
      value,
    } = event.target

    setForm((current) => ({
      ...current,
      [name]: value,
    }))
  }

  async function createBatch(event) {
    event.preventDefault()

    try {
      setError('')
      setMessage('')

      await apiRequest(
        '/api/admin/batches',
        {
          method: 'POST',
          body: JSON.stringify(form),
        }
      )

      setMessage(
        'Batch created successfully.'
      )

      setForm({
        name: '',
        course_id: '',
        trainer_id: '',
        start_date: '',
        end_date: '',
        status: 'active',
      })

      setShowCreate(false)

      await loadData()
    } catch (err) {
      console.error(
        'Create batch error:',
        err
      )

      setError(
        err.message ||
        'Unable to create batch'
      )
    }
  }

  async function openRoster(batch) {
    try {
      setError('')
      setMessage('')

      const data = await apiRequest(
        `/api/admin/batches/${batch.id}/learners`
      )

      setSelectedBatch(batch)
      setRoster(data.learners || [])
      setSelectedLearner('')
      setShowRoster(true)
    } catch (err) {
      console.error(
        'Batch roster error:',
        err
      )

      setError(
        err.message ||
        'Unable to load batch roster'
      )
    }
  }

  async function addLearner() {
    if (!selectedBatch || !selectedLearner) {
      setError(
        'Please select a learner.'
      )
      return
    }

    try {
      setError('')
      setMessage('')

      await apiRequest(
        `/api/admin/batches/${selectedBatch.id}/learners`,
        {
          method: 'POST',
          body: JSON.stringify({
            learner_id: Number(selectedLearner),
          }),
        }
      )

      setMessage(
        'Learner added to batch successfully.'
      )

      setSelectedLearner('')

      await openRoster(selectedBatch)
      await loadData()
    } catch (err) {
      console.error(
        'Add learner error:',
        err
      )

      setError(
        err.message ||
        'Unable to add learner to batch'
      )
    }
  }

  return (
    <DashboardLayout role="admin">
      <div style={styles.page}>

        <div style={styles.header}>
          <div>
            <h1 style={styles.title}>
              Batch Management
            </h1>

            <p style={styles.subtitle}>
              Create training cohorts, assign trainers,
              and manage learner rosters.
            </p>
          </div>

          <button
            type="button"
            style={styles.primaryButton}
            onClick={() => {
              setError('')
              setMessage('')
              setShowCreate(true)
            }}
          >
            + Create Batch
          </button>
        </div>

        {message && (
          <div style={styles.success}>
            {message}
          </div>
        )}

        {error && (
          <div style={styles.error}>
            {error}
          </div>
        )}

        {showCreate && (
          <div style={styles.card}>
            <div style={styles.cardHeader}>
              <h2 style={styles.cardTitle}>
                Create Batch
              </h2>

              <button
                type="button"
                style={styles.closeButton}
                onClick={() => setShowCreate(false)}
              >
                ×
              </button>
            </div>

            <form onSubmit={createBatch}>
              <div style={styles.formGrid}>

                <div style={styles.field}>
                  <label style={styles.label}>
                    Batch Name
                  </label>

                  <input
                    name="name"
                    value={form.name}
                    onChange={handleChange}
                    placeholder="Example: Python Batch 01"
                    required
                    style={styles.input}
                  />
                </div>

                <div style={styles.field}>
                  <label style={styles.label}>
                    Course
                  </label>

                  <select
                    name="course_id"
                    value={form.course_id}
                    onChange={handleChange}
                    required
                    style={styles.input}
                  >
                    <option value="">
                      Select course
                    </option>

                    {courses.map((course) => (
                      <option
                        key={course.id}
                        value={course.id}
                      >
                        {course.title}
                      </option>
                    ))}
                  </select>
                </div>

                <div style={styles.field}>
                  <label style={styles.label}>
                    Trainer
                  </label>

                  <select
                    name="trainer_id"
                    value={form.trainer_id}
                    onChange={handleChange}
                    required
                    style={styles.input}
                  >
                    <option value="">
                      Select trainer
                    </option>

                    {trainers.map((trainer) => (
                      <option
                        key={trainer.id}
                        value={trainer.id}
                      >
                        {trainer.name ||
                          trainer.user?.name ||
                          `Trainer ${trainer.id}`}
                      </option>
                    ))}
                  </select>
                </div>

                <div style={styles.field}>
                  <label style={styles.label}>
                    Start Date
                  </label>

                  <input
                    type="date"
                    name="start_date"
                    value={form.start_date}
                    onChange={handleChange}
                    required
                    style={styles.input}
                  />
                </div>

                <div style={styles.field}>
                  <label style={styles.label}>
                    End Date
                  </label>

                  <input
                    type="date"
                    name="end_date"
                    value={form.end_date}
                    onChange={handleChange}
                    required
                    style={styles.input}
                  />
                </div>

                <div style={styles.field}>
                  <label style={styles.label}>
                    Status
                  </label>

                  <select
                    name="status"
                    value={form.status}
                    onChange={handleChange}
                    style={styles.input}
                  >
                    <option value="active">
                      Active
                    </option>

                    <option value="inactive">
                      Inactive
                    </option>
                  </select>
                </div>

              </div>

              <div style={styles.formActions}>
                <button
                  type="button"
                  style={styles.secondaryButton}
                  onClick={() => setShowCreate(false)}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  style={styles.primaryButton}
                >
                  Create Batch
                </button>
              </div>
            </form>
          </div>
        )}

        {loading ? (
          <div style={styles.stateCard}>
            Loading batches...
          </div>
        ) : batches.length === 0 ? (
          <div style={styles.stateCard}>
            <h3>No batches yet</h3>

            <p>
              Create your first batch to organize
              learners into a training cohort.
            </p>
          </div>
        ) : (
          <div style={styles.card}>
            <div style={styles.cardHeader}>
              <div>
                <h2 style={styles.cardTitle}>
                  Batches
                </h2>

                <p style={styles.muted}>
                  {batches.length} batch
                  {batches.length === 1 ? '' : 'es'}
                </p>
              </div>
            </div>

            <div style={styles.tableWrapper}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>
                      Batch
                    </th>

                    <th style={styles.th}>
                      Course
                    </th>

                    <th style={styles.th}>
                      Trainer
                    </th>

                    <th style={styles.th}>
                      Dates
                    </th>

                    <th style={styles.th}>
                      Learners
                    </th>

                    <th style={styles.th}>
                      Status
                    </th>

                    <th style={styles.th}>
                      Action
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {batches.map((batch) => (
                    <tr key={batch.id}>
                      <td style={styles.td}>
                        <strong>
                          {batch.name}
                        </strong>
                      </td>

                      <td style={styles.td}>
                        {batch.course_title || '—'}
                      </td>

                      <td style={styles.td}>
                        {batch.trainer_name || '—'}
                      </td>

                      <td style={styles.td}>
                        {batch.start_date || '—'}
                        {' → '}
                        {batch.end_date || '—'}
                      </td>

                      <td style={styles.td}>
                        {batch.learner_count ?? 0}
                      </td>

                      <td style={styles.td}>
                        <span
                          style={{
                            ...styles.status,
                            ...(batch.status === 'active'
                              ? styles.activeStatus
                              : styles.inactiveStatus),
                          }}
                        >
                          {batch.status}
                        </span>
                      </td>

                      <td style={styles.td}>
                        <button
                          type="button"
                          style={styles.smallButton}
                          onClick={() =>
                            openRoster(batch)
                          }
                        >
                          View Roster
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {showRoster && selectedBatch && (
          <div style={styles.overlay}>
            <div style={styles.modal}>

              <div style={styles.cardHeader}>
                <div>
                  <h2 style={styles.cardTitle}>
                    {selectedBatch.name}
                  </h2>

                  <p style={styles.muted}>
                    {selectedBatch.course_title ||
                      'Batch roster'}
                  </p>
                </div>

                <button
                  type="button"
                  style={styles.closeButton}
                  onClick={() => setShowRoster(false)}
                >
                  ×
                </button>
              </div>

              <div style={styles.addLearner}>
                <select
                  value={selectedLearner}
                  onChange={(event) =>
                    setSelectedLearner(
                      event.target.value
                    )
                  }
                  style={styles.input}
                >
                  <option value="">
                    Select learner to add
                  </option>

                  {learners
                    .filter(
                      (learner) =>
                        !learner.batch_id
                    )
                    .map((learner) => (
                      <option
                        key={learner.id}
                        value={learner.id}
                      >
                        {learner.name ||
                          learner.email ||
                          `Learner ${learner.id}`}
                      </option>
                    ))}
                </select>

                <button
                  type="button"
                  style={styles.primaryButton}
                  onClick={addLearner}
                >
                  Add Learner
                </button>
              </div>

              {roster.length === 0 ? (
                <div style={styles.emptyRoster}>
                  No learners are assigned to this batch.
                </div>
              ) : (
                <div style={styles.roster}>
                  {roster.map((learner) => (
                    <div
                      key={learner.id}
                      style={styles.rosterRow}
                    >
                      <div>
                        <strong>
                          {learner.name ||
                            'Unnamed learner'}
                        </strong>

                        <div style={styles.muted}>
                          {learner.email || '—'}
                        </div>
                      </div>

                      <span
                        style={styles.status}
                      >
                        {learner.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}

            </div>
          </div>
        )}

      </div>
    </DashboardLayout>
  )
}

const styles = {
  page: {
    padding: '28px',
    maxWidth: '1400px',
    margin: '0 auto',
  },

  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: '20px',
    marginBottom: '24px',
  },

  title: {
    margin: 0,
    fontSize: '30px',
  },

  subtitle: {
    margin: '8px 0 0',
    color: '#667085',
  },

  card: {
    background: '#fff',
    border: '1px solid #e4e7ec',
    borderRadius: '14px',
    padding: '22px',
    marginBottom: '20px',
  },

  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '16px',
    marginBottom: '18px',
  },

  cardTitle: {
    margin: 0,
    fontSize: '20px',
  },

  muted: {
    color: '#667085',
    fontSize: '14px',
  },

  primaryButton: {
    border: 'none',
    borderRadius: '9px',
    padding: '11px 16px',
    cursor: 'pointer',
    fontWeight: 600,
    background: '#111827',
    color: '#fff',
  },

  secondaryButton: {
    border: '1px solid #d0d5dd',
    borderRadius: '9px',
    padding: '11px 16px',
    cursor: 'pointer',
    background: '#fff',
    color: '#344054',
    fontWeight: 600,
  },

  smallButton: {
    border: '1px solid #d0d5dd',
    borderRadius: '8px',
    padding: '8px 12px',
    cursor: 'pointer',
    background: '#fff',
    fontWeight: 600,
  },

  closeButton: {
    border: 'none',
    background: 'transparent',
    fontSize: '28px',
    cursor: 'pointer',
    lineHeight: 1,
  },

  success: {
    padding: '12px 14px',
    borderRadius: '9px',
    background: '#ecfdf3',
    border: '1px solid #abefc6',
    color: '#067647',
    marginBottom: '18px',
  },

  error: {
    padding: '12px 14px',
    borderRadius: '9px',
    background: '#fef3f2',
    border: '1px solid #fecdca',
    color: '#b42318',
    marginBottom: '18px',
  },

  stateCard: {
    background: '#fff',
    border: '1px solid #e4e7ec',
    borderRadius: '14px',
    padding: '50px',
    textAlign: 'center',
    color: '#667085',
  },

  formGrid: {
    display: 'grid',
    gridTemplateColumns:
      'repeat(auto-fit, minmax(220px, 1fr))',
    gap: '18px',
  },

  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '7px',
  },

  label: {
    fontWeight: 600,
    fontSize: '14px',
  },

  input: {
    width: '100%',
    boxSizing: 'border-box',
    padding: '11px 12px',
    border: '1px solid #d0d5dd',
    borderRadius: '9px',
    background: '#fff',
    fontSize: '14px',
  },

  formActions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '10px',
    marginTop: '22px',
  },

  tableWrapper: {
    overflowX: 'auto',
  },

  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },

  th: {
    textAlign: 'left',
    padding: '12px',
    borderBottom: '1px solid #e4e7ec',
    color: '#667085',
    fontSize: '13px',
  },

  td: {
    padding: '14px 12px',
    borderBottom: '1px solid #f2f4f7',
    fontSize: '14px',
    verticalAlign: 'middle',
  },

  status: {
    display: 'inline-block',
    padding: '5px 9px',
    borderRadius: '999px',
    fontSize: '12px',
    fontWeight: 600,
    background: '#f2f4f7',
    color: '#344054',
  },

  activeStatus: {
    background: '#ecfdf3',
    color: '#067647',
  },

  inactiveStatus: {
    background: '#f2f4f7',
    color: '#667085',
  },

  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(16, 24, 40, 0.45)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '20px',
    zIndex: 1000,
  },

  modal: {
    width: 'min(760px, 100%)',
    maxHeight: '85vh',
    overflowY: 'auto',
    background: '#fff',
    borderRadius: '16px',
    padding: '24px',
    boxSizing: 'border-box',
  },

  addLearner: {
    display: 'grid',
    gridTemplateColumns: '1fr auto',
    gap: '10px',
    marginBottom: '20px',
  },

  emptyRoster: {
    padding: '30px',
    textAlign: 'center',
    color: '#667085',
    border: '1px dashed #d0d5dd',
    borderRadius: '10px',
  },

  roster: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },

  rosterRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '13px 14px',
    border: '1px solid #eaecf0',
    borderRadius: '10px',
  },
}