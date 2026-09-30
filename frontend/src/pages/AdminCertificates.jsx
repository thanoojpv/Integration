import React, { useEffect, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'

const API_BASE =
  `${import.meta.env.VITE_API_BASE_URL}/api`

export default function AdminCertificates() {
  const [certificates, setCertificates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedCertificate, setSelectedCertificate] = useState(null)

  const fetchCertificates = async () => {
    try {
      setLoading(true)
      setError('')

      const token = localStorage.getItem('access_token')

      if (!token) {
        throw new Error('Login session not found. Please login again.')
      }

      const response = await fetch(
        `${API_BASE}/admin/certificates`,
        {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.error || 'Unable to load certificates.'
        )
      }

      setCertificates(data.certificates || [])
    } catch (error) {
      console.error('ADMIN CERTIFICATES ERROR:', error)

      setError(
        error.message || 'Something went wrong.'
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCertificates()
  }, [])

  const formatDate = (date) => {
    if (!date) return '—'

    return new Date(date).toLocaleDateString(
      'en-IN',
      {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      }
    )
  }

  const getLearnerName = (certificate) => {
    return (
      certificate.learner_name ||
      certificate.learner ||
      certificate.name ||
      'Learner'
    )
  }

  const getLearnerEmail = (certificate) => {
    return (
      certificate.learner_email ||
      certificate.email ||
      '—'
    )
  }

  const getCourseName = (certificate) => {
    return (
      certificate.course_name ||
      certificate.course ||
      certificate.title ||
      'Course'
    )
  }

  return (
    <DashboardLayout role="admin">

      <div className="admin-certificates-page">

        {/* HEADER */}

        <div className="page-header">

          <div>
            <div className="title-row">

              <div className="title-icon">
                🏆
              </div>

              <div>
                <h1>Certificates</h1>

                <p>
                  View learners who have completed courses and received certificates.
                </p>
              </div>

            </div>
          </div>

          <button
            className="refresh-button"
            onClick={fetchCertificates}
            disabled={loading}
          >
            {loading ? 'Loading...' : '↻ Refresh'}
          </button>

        </div>


        {/* SUMMARY */}

        {!loading && !error && (
          <div className="summary-card">

            <div className="summary-icon">
              🎓
            </div>

            <div>
              <div className="summary-label">
                Certificates Issued
              </div>

              <div className="summary-value">
                {certificates.length}
              </div>
            </div>

          </div>
        )}


        {/* LOADING */}

        {loading && (
          <div className="state-card">

            <div className="state-icon">
              ⏳
            </div>

            <h2>
              Loading certificates...
            </h2>

            <p>
              Please wait while certificates are fetched.
            </p>

          </div>
        )}


        {/* ERROR */}

        {!loading && error && (
          <div className="error-card">

            <strong>
              Unable to load certificates
            </strong>

            <p>
              {error}
            </p>

            <button
              className="retry-button"
              onClick={fetchCertificates}
            >
              Try Again
            </button>

          </div>
        )}


        {/* EMPTY */}

        {!loading &&
          !error &&
          certificates.length === 0 && (

            <div className="state-card">

              <div className="state-icon">
                🎓
              </div>

              <h2>
                No certificates issued yet
              </h2>

              <p>
                Certificates will appear here automatically when learners complete courses.
              </p>

            </div>
          )}


        {/* TABLE */}

        {!loading &&
          !error &&
          certificates.length > 0 && (

            <div className="certificates-card">

              <div className="table-wrapper">

                <table>

                  <thead>
                    <tr>
                      <th>Learner</th>
                      <th>Course</th>
                      <th>Certificate ID</th>
                      <th>Started</th>
                      <th>Completed</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>

                  <tbody>

                    {certificates.map((certificate) => (

                      <tr
                        key={
                          certificate.id ||
                          certificate.certificate_id
                        }
                      >

                        {/* LEARNER */}

                        <td>

                          <div className="learner-cell">

                            <div className="learner-avatar">
                              {getLearnerName(certificate)
                                .charAt(0)
                                .toUpperCase()}
                            </div>

                            <div>

                              <div className="learner-name">
                                {getLearnerName(certificate)}
                              </div>

                              <div className="learner-email">
                                {getLearnerEmail(certificate)}
                              </div>

                            </div>

                          </div>

                        </td>


                        {/* COURSE */}

                        <td>

                          <div className="course-name">
                            {getCourseName(certificate)}
                          </div>

                          <div className="course-id">
                            {certificate.course_id || '—'}
                          </div>

                        </td>


                        {/* CERTIFICATE ID */}

                        <td>

                          <span className="certificate-id">
                            {certificate.certificate_id || '—'}
                          </span>

                        </td>


                        {/* STARTED */}

                        <td>
                          {formatDate(
                            certificate.start_date
                          )}
                        </td>


                        {/* COMPLETED */}

                        <td>
                          {formatDate(
                            certificate.end_date ||
                            certificate.completed_at ||
                            certificate.created_at
                          )}
                        </td>


                        {/* STATUS */}

                        <td>

                          <span
                            className={
                              certificate.status === 'valid'
                                ? 'status-badge valid'
                                : 'status-badge'
                            }
                          >
                            {certificate.status === 'valid'
                              ? '✓ Valid'
                              : certificate.status || '—'}
                          </span>

                        </td>


                        {/* ACTION */}

                        <td>

                          <button
                            className="view-button"
                            onClick={() =>
                              setSelectedCertificate(
                                certificate
                              )
                            }
                          >
                             View
                          </button>

                        </td>

                      </tr>

                    ))}

                  </tbody>

                </table>

              </div>

            </div>
          )}

      </div>


      {/* CERTIFICATE MODAL */}

      {selectedCertificate && (

        <div
          className="modal-overlay"
          onClick={() =>
            setSelectedCertificate(null)
          }
        >

          <div
            className="certificate-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            <div className="modal-header">

              <div>
                <h2>
                  Certificate
                </h2>

                <p>
                  {getCourseName(selectedCertificate)}
                </p>
              </div>

              <button
                className="close-button"
                onClick={() =>
                  setSelectedCertificate(null)
                }
              >
                ✕
              </button>

            </div>


            {/* CERTIFICATE */}

            <div className="modal-certificate">

              <div className="certificate-trophy">
                🏆
              </div>

              <div className="certificate-title">
                CERTIFICATE
              </div>

              <div className="certificate-subtitle">
                OF COURSE COMPLETION
              </div>

              <div className="certificate-line" />

              <div className="presented-text">
                This certificate is proudly presented to
              </div>

              <div className="certificate-learner">
                {getLearnerName(selectedCertificate)}
              </div>

              <div className="completion-text">
                for successfully completing the course
              </div>

              <div className="certificate-course">
                {getCourseName(selectedCertificate)}
              </div>


              <div className="certificate-bottom">

                <div>
                  <span>
                    Completion Date
                  </span>

                  <strong>
                    {formatDate(
                      selectedCertificate.end_date ||
                      selectedCertificate.completed_at ||
                      selectedCertificate.created_at
                    )}
                  </strong>
                </div>


                <div>
                  <span>
                    Certificate ID
                  </span>

                  <strong>
                    {selectedCertificate.certificate_id || '—'}
                  </strong>
                </div>

              </div>

            </div>


            {/* COURSE DETAILS */}

            <div className="course-details">

              <div className="details-title">
                📚 Course Details
              </div>

              <div className="details-grid">

                <div>
                  <span>Course Name</span>
                  <strong>
                    {getCourseName(selectedCertificate)}
                  </strong>
                </div>

                <div>
                  <span>Course ID</span>
                  <strong>
                    {selectedCertificate.course_id || '—'}
                  </strong>
                </div>

                <div>
                  <span>Learner</span>
                  <strong>
                    {getLearnerName(selectedCertificate)}
                  </strong>
                </div>

                <div>
                  <span>Learner Email</span>
                  <strong>
                    {getLearnerEmail(selectedCertificate)}
                  </strong>
                </div>

                <div>
                  <span>Started</span>
                  <strong>
                    {formatDate(
                      selectedCertificate.start_date
                    )}
                  </strong>
                </div>

                <div>
                  <span>Completed</span>
                  <strong>
                    {formatDate(
                      selectedCertificate.end_date ||
                      selectedCertificate.completed_at
                    )}
                  </strong>
                </div>

              </div>

            </div>


            {/* FOOTER */}

            <div className="modal-footer">

              <button
                className="close-modal-button"
                onClick={() =>
                  setSelectedCertificate(null)
                }
              >
                Close
              </button>

            </div>

          </div>

        </div>
      )}


      <style>{`

        .admin-certificates-page {
          width: 100%;
          max-width: 1400px;
          margin: 0 auto;
          padding: 32px;
          box-sizing: border-box;
        }

        .page-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 20px;
          margin-bottom: 24px;
        }

        .title-row {
          display: flex;
          align-items: center;
          gap: 14px;
        }

        .title-icon {
          width: 48px;
          height: 48px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 12px;
          background: #eef4ff;
          border: 1px solid #dbe7ff;
          font-size: 23px;
        }

        .page-header h1 {
          margin: 0 0 5px;
          color: #172033;
          font-size: 30px;
        }

        .page-header p {
          margin: 0;
          color: #667085;
          font-size: 15px;
        }

        .refresh-button {
          border: none;
          border-radius: 8px;
          padding: 11px 18px;
          background: #3764e8;
          color: white;
          font-weight: 600;
          cursor: pointer;
        }

        .refresh-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .summary-card {
          display: flex;
          align-items: center;
          gap: 14px;
          width: fit-content;
          min-width: 210px;
          margin-bottom: 22px;
          padding: 18px 22px;
          background: white;
          border: 1px solid #e4e7ec;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(16, 24, 40, 0.04);
        }

        .summary-icon {
          width: 42px;
          height: 42px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 10px;
          background: #eef4ff;
          font-size: 21px;
        }

        .summary-label {
          color: #667085;
          font-size: 12px;
        }

        .summary-value {
          margin-top: 3px;
          color: #172033;
          font-size: 22px;
          font-weight: 700;
        }

        .state-card {
          padding: 55px 30px;
          text-align: center;
          background: white;
          border: 1px solid #e4e7ec;
          border-radius: 14px;
        }

        .state-icon {
          font-size: 38px;
          margin-bottom: 12px;
        }

        .state-card h2 {
          margin: 0 0 8px;
          color: #172033;
        }

        .state-card p {
          margin: 0;
          color: #667085;
        }

        .error-card {
          padding: 20px;
          background: #fef3f2;
          border: 1px solid #fecdca;
          border-radius: 12px;
          color: #b42318;
        }

        .error-card p {
          margin: 7px 0 14px;
        }

        .retry-button {
          border: none;
          border-radius: 7px;
          padding: 9px 15px;
          background: #b42318;
          color: white;
          font-weight: 600;
          cursor: pointer;
        }

        .certificates-card {
          background: white;
          border: 1px solid #e4e7ec;
          border-radius: 14px;
          overflow: hidden;
          box-shadow: 0 3px 12px rgba(16, 24, 40, 0.05);
        }

        .table-wrapper {
          width: 100%;
          overflow-x: auto;
        }

        table {
          width: 100%;
          min-width: 1050px;
          border-collapse: collapse;
        }

        th {
          padding: 15px 18px;
          background: #f8faff;
          border-bottom: 1px solid #e4e7ec;
          color: #667085;
          font-size: 12px;
          font-weight: 700;
          text-align: left;
          white-space: nowrap;
        }

        td {
          padding: 17px 18px;
          border-bottom: 1px solid #eaecf0;
          color: #344054;
          font-size: 13px;
          vertical-align: middle;
        }

        tr:last-child td {
          border-bottom: none;
        }

        tbody tr:hover {
          background: #f8faff;
        }

        .learner-cell {
          display: flex;
          align-items: center;
          gap: 11px;
          min-width: 210px;
        }

        .learner-avatar {
          width: 38px;
          height: 38px;
          min-width: 38px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          background: #eef4ff;
          border: 1px solid #dbe7ff;
          color: #3764e8;
          font-weight: 700;
        }

        .learner-name {
          color: #172033;
          font-weight: 600;
          margin-bottom: 3px;
        }

        .learner-email {
          color: #667085;
          font-size: 11px;
        }

        .course-name {
          color: #172033;
          font-weight: 600;
          margin-bottom: 3px;
        }

        .course-id {
          color: #667085;
          font-size: 11px;
        }

        .certificate-id {
          padding: 5px 8px;
          border-radius: 6px;
          background: #f2f4f7;
          color: #344054;
          font-size: 11px;
          white-space: nowrap;
        }

        .status-badge {
          display: inline-flex;
          padding: 5px 9px;
          border-radius: 999px;
          background: #f2f4f7;
          color: #667085;
          font-size: 11px;
          font-weight: 600;
        }

        .status-badge.valid {
          background: #ecfdf3;
          border: 1px solid #abefc6;
          color: #067647;
        }

        .view-button {
          border: 1px solid #3764e8;
          border-radius: 7px;
          padding: 8px 12px;
          background: #3764e8;
          color: white;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
        }

        .view-button:hover {
          background: #2f56cc;
        }

        .modal-overlay {
          position: fixed;
          inset: 0;
          z-index: 9999;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
          background: rgba(15, 23, 42, 0.58);
        }

        .certificate-modal {
          width: 100%;
          max-width: 950px;
          max-height: 92vh;
          overflow-y: auto;
          background: white;
          border-radius: 16px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
        }

        .modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 18px 22px;
          border-bottom: 1px solid #eaecf0;
        }

        .modal-header h2 {
          margin: 0 0 4px;
          color: #172033;
          font-size: 19px;
        }

        .modal-header p {
          margin: 0;
          color: #667085;
          font-size: 12px;
        }

        .close-button {
          width: 34px;
          height: 34px;
          border: none;
          border-radius: 8px;
          background: #f2f4f7;
          cursor: pointer;
        }

        .modal-certificate {
          margin: 22px;
          padding: 45px 30px;
          text-align: center;
          border: 7px solid #d4b45d;
          background: linear-gradient(
            135deg,
            #fffdf5,
            #ffffff 50%,
            #f5f8ff
          );
        }

        .certificate-trophy {
          font-size: 32px;
          margin-bottom: 8px;
        }

        .certificate-title {
          color: #172033;
          font-size: 40px;
          font-weight: 800;
          letter-spacing: 6px;
        }

        .certificate-subtitle {
          margin-top: 4px;
          color: #8b6b24;
          font-size: 12px;
          font-weight: 700;
          letter-spacing: 3px;
        }

        .certificate-line {
          width: 140px;
          height: 2px;
          margin: 18px auto;
          background: #c9a84e;
        }

        .presented-text {
          color: #667085;
          font-size: 13px;
        }

        .certificate-learner {
          margin: 14px 0;
          color: #172033;
          font-size: 36px;
          font-family: Georgia, serif;
          font-style: italic;
        }

        .completion-text {
          color: #475467;
          font-size: 14px;
        }

        .certificate-course {
          margin-top: 8px;
          color: #8b6b24;
          font-size: 22px;
          font-weight: 700;
        }

        .certificate-bottom {
          display: flex;
          justify-content: space-around;
          gap: 30px;
          margin-top: 38px;
          padding-top: 18px;
          border-top: 1px solid #d0d5dd;
        }

        .certificate-bottom div {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }

        .certificate-bottom span {
          color: #667085;
          font-size: 11px;
        }

        .certificate-bottom strong {
          color: #344054;
          font-size: 12px;
        }

        .course-details {
          margin: 0 22px 22px;
          padding: 18px;
          border: 1px solid #e4e7ec;
          border-radius: 10px;
          background: #f8faff;
        }

        .details-title {
          margin-bottom: 15px;
          color: #172033;
          font-size: 16px;
          font-weight: 700;
        }

        .details-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 13px;
        }

        .details-grid div {
          display: flex;
          flex-direction: column;
          gap: 4px;
          padding: 12px;
          background: white;
          border: 1px solid #e4e7ec;
          border-radius: 8px;
        }

        .details-grid span {
          color: #667085;
          font-size: 11px;
        }

        .details-grid strong {
          color: #344054;
          font-size: 13px;
        }

        .modal-footer {
          display: flex;
          justify-content: flex-end;
          padding: 0 22px 22px;
        }

        .close-modal-button {
          padding: 10px 18px;
          border: 1px solid #d0d5dd;
          border-radius: 8px;
          background: white;
          color: #344054;
          font-weight: 600;
          cursor: pointer;
        }

        @media (max-width: 700px) {

          .admin-certificates-page {
            padding: 20px;
          }

          .page-header {
            align-items: flex-start;
            flex-direction: column;
          }

          .certificate-title {
            font-size: 27px;
            letter-spacing: 4px;
          }

          .certificate-learner {
            font-size: 28px;
          }

          .details-grid {
            grid-template-columns: 1fr;
          }

          .certificate-bottom {
            flex-direction: column;
          }

        }

      `}</style>

    </DashboardLayout>
  )
}