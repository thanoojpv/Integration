import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { apiRequest } from '../services/api'
import './TrainerCodingExamResults.css'


// =========================================================
// TRAINER CODING EXAM RESULTS
// =========================================================

export default function TrainerCodingExamResults() {

  const navigate = useNavigate()
  const { examId } = useParams()

  // -------------------------------------------------------
  // DATA
  // -------------------------------------------------------

  const [exam, setExam] = useState(null)

  const [summary, setSummary] = useState({
    total_submissions: 0,
    accepted: 0,
    partial: 0,
    failed: 0,
  })

  const [submissions, setSubmissions] = useState([])


  // -------------------------------------------------------
  // MONITORING DATA
  // -------------------------------------------------------

  const [monitoringSessions, setMonitoringSessions] =
    useState([])

  const [monitoringLoading, setMonitoringLoading] =
    useState(false)

  const [monitoringError, setMonitoringError] =
    useState('')


  // -------------------------------------------------------
  // UI STATE
  // -------------------------------------------------------

  const [loading, setLoading] =
    useState(true)

  const [error, setError] =
    useState('')


  // =======================================================
  // LOAD RESULTS
  // =======================================================

  async function loadResults() {

    try {

      setLoading(true)
      setError('')

      const data = await apiRequest(
        `/api/trainer/coding-exams/${examId}/submissions`
      )

      setExam(
        data?.exam || null
      )

      setSummary(
        data?.summary || {
          total_submissions: 0,
          accepted: 0,
          partial: 0,
          failed: 0,
        }
      )

      setSubmissions(
        Array.isArray(data?.submissions)
          ? data.submissions
          : []
      )

    } catch (err) {

      console.error(
        'Failed to load coding exam results:',
        err
      )

      setError(
        err.message ||
        'Failed to load coding exam results.'
      )

    } finally {

      setLoading(false)
    }
  }


  // =======================================================
  // LOAD MONITORING
  // =======================================================

  async function loadMonitoring() {

    if (!examId) {
      return
    }

    try {

      setMonitoringLoading(true)
      setMonitoringError('')

      const data = await apiRequest(
        `/api/trainer/coding-exams/${examId}/monitoring`
      )

      setMonitoringSessions(
        Array.isArray(data?.sessions)
          ? data.sessions
          : []
      )

    } catch (err) {

      console.error(
        'Failed to load coding exam monitoring:',
        err
      )

      setMonitoringError(
        err.message ||
        'Failed to load monitoring information.'
      )

    } finally {

      setMonitoringLoading(false)
    }
  }


  // =======================================================
  // INITIAL LOAD
  // =======================================================

  useEffect(() => {

    if (examId) {

      loadResults()
      loadMonitoring()

    }

  }, [examId])


  // =======================================================
  // FORMAT DATE
  // =======================================================

  function formatDate(value) {

    if (!value) {
      return '—'
    }

    const date =
      new Date(value)

    if (
      Number.isNaN(
        date.getTime()
      )
    ) {
      return value
    }

    return date.toLocaleString()
  }


  // =======================================================
  // STATUS CLASS
  // =======================================================

  function getStatusClass(status) {

    if (status === 'accepted') {
      return 'accepted'
    }

    if (status === 'partial') {
      return 'partial'
    }

    return 'failed'
  }


  // =======================================================
  // MONITORING STATUS CLASS
  // =======================================================

  function getMonitoringStatusClass(
    status
  ) {

    if (status === 'flagged') {
      return 'monitoring-flagged'
    }

    if (status === 'active') {
      return 'monitoring-active'
    }

    return 'monitoring-ended'
  }


  // =======================================================
  // MONITORING WARNING CLASS
  // =======================================================

  function getWarningClass(
    warningCount
  ) {

    const count =
      Number(warningCount || 0)

    if (count >= 3) {
      return 'monitoring-warning-danger'
    }

    if (count > 0) {
      return 'monitoring-warning'
    }

    return 'monitoring-warning-safe'
  }


  // =======================================================
  // LOADING
  // =======================================================

  if (loading) {

    return (
      <div className="trainer-coding-results-page">

        <div className="trainer-coding-results-loading">
          Loading coding exam results...
        </div>

      </div>
    )
  }


  // =======================================================
  // PAGE
  // =======================================================

  return (

    <div className="trainer-coding-results-page">


      {/* =================================================
          HEADER
      ================================================= */}

      <div className="trainer-coding-results-header">

        <div>

          <button
            className="trainer-coding-results-back"
            onClick={() =>
              navigate(
                '/trainer/coding-exams'
              )
            }
          >
            ← Back to Coding Exams
          </button>


          <h1>
            {exam?.title ||
              'Coding Exam Results'}
          </h1>


          <p>
            View learner submissions,
            coding performance, and
            exam monitoring information.
          </p>

        </div>


        <button
          className="trainer-coding-results-refresh"
          onClick={() => {

            loadResults()
            loadMonitoring()

          }}
        >
          ↻ Refresh
        </button>

      </div>


      {/* =================================================
          ERROR
      ================================================= */}

      {error && (

        <div className="trainer-coding-results-error">

          {error}

        </div>

      )}


      {/* =================================================
          SUMMARY
      ================================================= */}

      <div className="trainer-coding-results-summary">


        <div className="trainer-coding-results-summary-card">

          <span>
            Total Submissions
          </span>

          <strong>
            {summary.total_submissions}
          </strong>

        </div>


        <div className="trainer-coding-results-summary-card">

          <span>
            Accepted
          </span>

          <strong>
            {summary.accepted}
          </strong>

        </div>


        <div className="trainer-coding-results-summary-card">

          <span>
            Partial
          </span>

          <strong>
            {summary.partial}
          </strong>

        </div>


        <div className="trainer-coding-results-summary-card">

          <span>
            Failed
          </span>

          <strong>
            {summary.failed}
          </strong>

        </div>

      </div>


      {/* =================================================
          SUBMISSIONS
      ================================================= */}

      <section className="trainer-coding-results-section">


        <div className="trainer-coding-results-section-header">

          <div>

            <h2>
              Learner Submissions
            </h2>

            <p>
              Every code submission made
              for this exam.
            </p>

          </div>

        </div>


        {submissions.length === 0 ? (

          <div className="trainer-coding-results-empty">

            <div className="trainer-coding-results-empty-icon">
              📝
            </div>

            <h3>
              No submissions yet
            </h3>

            <p>
              Learner submissions will
              appear here after they
              submit code.
            </p>

          </div>

        ) : (

          <div className="trainer-coding-results-table-wrapper">

            <table className="trainer-coding-results-table">

              <thead>

                <tr>

                  <th>
                    Learner
                  </th>

                  <th>
                    Question
                  </th>

                  <th>
                    Language
                  </th>

                  <th>
                    Status
                  </th>

                  <th>
                    Score
                  </th>

                  <th>
                    Tests
                  </th>

                  <th>
                    Time
                  </th>

                  <th>
                    Submitted
                  </th>

                </tr>

              </thead>


              <tbody>

                {submissions.map(
                  submission => (

                    <tr
                      key={
                        submission.id
                      }
                    >

                      <td>

                        <div className="trainer-coding-results-learner">

                          <strong>
                            {submission.learner_name ||
                              'Unknown Learner'}
                          </strong>


                          {submission.learner_email && (

                            <span>
                              {submission.learner_email}
                            </span>

                          )}

                        </div>

                      </td>


                      <td>
                        {submission.question_title ||
                          'Unknown Question'}
                      </td>


                      <td>
                        {submission.language ||
                          '—'}
                      </td>


                      <td>

                        <span
                          className={
                            `trainer-coding-results-status ${getStatusClass(
                              submission.status
                            )}`
                          }
                        >
                          {submission.status ||
                            'failed'}
                        </span>

                      </td>


                      <td>

                        <strong>
                          {submission.score ??
                            0}
                        </strong>

                      </td>


                      <td>

                        {submission.passed_tests ??
                          0}

                        {' / '}

                        {submission.total_tests ??
                          0}

                      </td>


                      <td>
                        {submission.execution_time ??
                          0}s
                      </td>


                      <td>
                        {formatDate(
                          submission.submitted_at
                        )}
                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        )}

      </section>


      {/* =================================================
          MONITORING & PROCTORING
      ================================================= */}

      <section className="trainer-coding-results-section">


        {/* -------------------------------------------------
            MONITORING HEADER
        ------------------------------------------------- */}

        <div className="trainer-coding-results-section-header">

          <div>

            <h2>
              Monitoring & Proctoring
            </h2>

            <p>
              Camera monitoring sessions,
              warnings, monitoring events,
              and random screenshots.
            </p>

          </div>


          <button
            className="trainer-coding-results-refresh"
            onClick={loadMonitoring}
            disabled={monitoringLoading}
          >
            {monitoringLoading
              ? 'Loading...'
              : '↻ Refresh Monitoring'}
          </button>

        </div>


        {/* -------------------------------------------------
            MONITORING ERROR
        ------------------------------------------------- */}

        {monitoringError && (

          <div className="trainer-coding-results-error">

            {monitoringError}

          </div>

        )}


        {/* -------------------------------------------------
            MONITORING LOADING
        ------------------------------------------------- */}

        {monitoringLoading ? (

          <div className="trainer-coding-results-empty">

            <div className="trainer-coding-results-empty-icon">
              🎥
            </div>

            <h3>
              Loading monitoring information...
            </h3>

            <p>
              Please wait while the
              monitoring records are loaded.
            </p>

          </div>


        ) : monitoringSessions.length === 0 ? (


          /* -------------------------------------------------
             NO MONITORING SESSIONS
          ------------------------------------------------- */

          <div className="trainer-coding-results-empty">

            <div className="trainer-coding-results-empty-icon">
              🎥
            </div>

            <h3>
              No monitoring sessions yet
            </h3>

            <p>
              Monitoring information will
              appear here after a learner
              starts the exam.
            </p>

          </div>


        ) : (


          /* -------------------------------------------------
             MONITORING SESSION LIST
          ------------------------------------------------- */

          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '20px',
            }}
          >

            {monitoringSessions.map(
              item => {

                const session =
                  item.session || {}

                const learner =
                  item.learner || {}

                const events =
                  Array.isArray(
                    item.events
                  )
                    ? item.events
                    : []

                const screenshots =
                  Array.isArray(
                    item.screenshots
                  )
                    ? item.screenshots
                    : []


                return (

                  <div
                    key={
                      session.id
                    }

                    style={{
                      border:
                        '1px solid rgba(148,163,184,0.20)',

                      borderRadius:
                        '14px',

                      padding:
                        '20px',

                      background:
                        'rgba(15,23,42,0.45)',
                    }}
                  >


                    {/* =================================
                        LEARNER + STATUS
                    ================================= */}

                    <div
                      style={{
                        display:
                          'flex',

                        justifyContent:
                          'space-between',

                        alignItems:
                          'flex-start',

                        gap:
                          '15px',

                        flexWrap:
                          'wrap',
                      }}
                    >

                      <div>

                        <h3
                          style={{
                            margin:
                              '0 0 6px',
                          }}
                        >
                          {learner.name ||
                            'Unknown Learner'}
                        </h3>


                        <div
                          style={{
                            color:
                              '#94a3b8',

                            fontSize:
                              '13px',
                          }}
                        >
                          {learner.email ||
                            'No email available'}
                        </div>

                      </div>


                      {/* SESSION STATUS */}

                      <span
                        className={
                          `trainer-coding-results-status ${
                            getMonitoringStatusClass(
                              session.status
                            )
                          }`
                        }
                      >
                        {session.status ||
                          'unknown'}
                      </span>

                    </div>


                    {/* =================================
                        SESSION DETAILS
                    ================================= */}

                    <div
                      style={{
                        display:
                          'grid',

                        gridTemplateColumns:
                          'repeat(auto-fit, minmax(160px, 1fr))',

                        gap:
                          '12px',

                        marginTop:
                          '18px',
                      }}
                    >


                      {/* STARTED */}

                      <div
                        style={{
                          padding:
                            '12px',

                          borderRadius:
                            '10px',

                          background:
                            'rgba(255,255,255,0.04)',
                        }}
                      >

                        <small>
                          Started
                        </small>

                        <div>
                          {formatDate(
                            session.started_at
                          )}
                        </div>

                      </div>


                      {/* ENDED */}

                      <div
                        style={{
                          padding:
                            '12px',

                          borderRadius:
                            '10px',

                          background:
                            'rgba(255,255,255,0.04)',
                        }}
                      >

                        <small>
                          Ended
                        </small>

                        <div>
                          {formatDate(
                            session.ended_at
                          )}
                        </div>

                      </div>


                      {/* CAMERA */}

                      <div
                        style={{
                          padding:
                            '12px',

                          borderRadius:
                            '10px',

                          background:
                            'rgba(255,255,255,0.04)',
                        }}
                      >

                        <small>
                          Camera
                        </small>

                        <div>
                          {session.camera_enabled
                            ? '✓ Enabled'
                            : '✕ Disabled'}
                        </div>

                      </div>


                      {/* MICROPHONE */}

                      <div
                        style={{
                          padding:
                            '12px',

                          borderRadius:
                            '10px',

                          background:
                            'rgba(255,255,255,0.04)',
                        }}
                      >

                        <small>
                          Microphone
                        </small>

                        <div>
                          {session.microphone_enabled
                            ? '✓ Enabled'
                            : '✕ Disabled'}
                        </div>

                      </div>


                      {/* WARNINGS */}

                      <div
                        style={{
                          padding:
                            '12px',

                          borderRadius:
                            '10px',

                          background:
                            'rgba(255,255,255,0.04)',
                        }}
                      >

                        <small>
                          Warnings
                        </small>

                        <div
                          className={
                            getWarningClass(
                              session.warning_count
                            )
                          }

                          style={{
                            fontWeight:
                              '700',

                            fontSize:
                              '18px',

                            marginTop:
                              '4px',
                          }}
                        >
                          {session.warning_count ??
                            0}

                          {' / 3'}
                        </div>

                      </div>

                    </div>


                    {/* =================================
                        MONITORING EVENTS
                    ================================= */}

                    <div
                      style={{
                        marginTop:
                          '22px',
                      }}
                    >

                      <h4>
                        Monitoring Events
                      </h4>


                      {events.length === 0 ? (

                        <p
                          style={{
                            color:
                              '#94a3b8',
                          }}
                        >
                          No monitoring events
                          recorded.
                        </p>

                      ) : (

                        <div
                          style={{
                            display:
                              'flex',

                            flexDirection:
                              'column',

                            gap:
                              '8px',
                          }}
                        >

                          {events.map(
                            event => (

                              <div
                                key={
                                  event.id
                                }

                                style={{
                                  padding:
                                    '10px 12px',

                                  borderRadius:
                                    '8px',

                                  background:
                                    'rgba(255,255,255,0.04)',
                                }}
                              >

                                <strong>
                                  {event.event_type}
                                </strong>


                                <div
                                  style={{
                                    fontSize:
                                      '13px',

                                    marginTop:
                                      '3px',
                                  }}
                                >
                                  {event.message ||
                                    'Monitoring event'}
                                </div>


                                <small
                                  style={{
                                    color:
                                      '#94a3b8',
                                  }}
                                >
                                  {formatDate(
                                    event.event_time
                                  )}
                                </small>

                              </div>

                            )
                          )}

                        </div>

                      )}

                    </div>


                    {/* =================================
                        RANDOM SCREENSHOTS
                    ================================= */}

                    <div
                      style={{
                        marginTop:
                          '22px',
                      }}
                    >

                      <h4>
                        Random Monitoring Screenshots
                      </h4>


                      {screenshots.length === 0 ? (

                        <p
                          style={{
                            color:
                              '#94a3b8',
                          }}
                        >
                          No screenshots captured yet.
                        </p>

                      ) : (

                        <div
                          style={{
                            display:
                              'grid',

                            gridTemplateColumns:
                              'repeat(auto-fill, minmax(220px, 1fr))',

                            gap:
                              '14px',
                          }}
                        >

                          {screenshots.map(
                            screenshot => {

                              /*
                               * Backend screenshot endpoint:
                               *
                               * /api/trainer/coding-exams/
                               * {examId}/monitoring/
                               * screenshots/{screenshotId}
                               */

                              const imageUrl =
                                `${import.meta.env.VITE_API_BASE_URL}${screenshot.url}`


                              return (

                                <div
                                  key={
                                    screenshot.id
                                  }

                                  style={{
                                    border:
                                      '1px solid rgba(148,163,184,0.20)',

                                    borderRadius:
                                      '10px',

                                    overflow:
                                      'hidden',

                                    background:
                                      '#020617',
                                  }}
                                >

                                  <img
                                    src={
                                      imageUrl
                                    }

                                    alt="Monitoring snapshot"

                                    style={{
                                      width:
                                        '100%',

                                      display:
                                        'block',

                                      aspectRatio:
                                        '4 / 3',

                                      objectFit:
                                        'cover',
                                    }}

                                    onError={
                                      (event) => {

                                        console.error(
                                          'Failed to load monitoring screenshot:',
                                          imageUrl
                                        )

                                        event.currentTarget.style.display =
                                          'none'
                                      }
                                    }
                                  />


                                  <div
                                    style={{
                                      padding:
                                        '8px 10px',

                                      fontSize:
                                        '12px',

                                      color:
                                        '#94a3b8',
                                    }}
                                  >

                                    Captured:{' '}

                                    {formatDate(
                                      screenshot.captured_at
                                    )}

                                  </div>

                                </div>

                              )

                            }
                          )}

                        </div>

                      )}

                    </div>

                  </div>

                )

              }
            )}

          </div>

        )}

      </section>

    </div>
  )
}