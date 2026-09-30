import React, { useEffect, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'

const API_BASE =
  `${import.meta.env.VITE_API_BASE_URL}/api`

export default function LearnerCertificates() {
  const [certificates, setCertificates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [selectedCertificate, setSelectedCertificate] = useState(null)
  const [selectedCourse, setSelectedCourse] = useState(null)
  const [courseLoading, setCourseLoading] = useState(false)

  /* =========================================================
     FETCH CERTIFICATES
  ========================================================= */

  const fetchCertificates = async () => {
    try {
      setLoading(true)
      setError('')

      const token = localStorage.getItem('access_token')

      if (!token) {
        throw new Error(
          'Login session not found. Please login again.'
        )
      }

      const response = await fetch(
        `${API_BASE}/learner/certificates`,
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
      console.error('CERTIFICATES ERROR:', error)

      setError(
        error.message || 'Something went wrong.'
      )
    } finally {
      setLoading(false)
    }
  }

  /* =========================================================
     INITIAL LOAD
  ========================================================= */

  useEffect(() => {
    fetchCertificates()
  }, [])

  /* =========================================================
     FORMAT DATE
  ========================================================= */

  const formatDate = (date) => {
    if (!date) return '—'

    const parsedDate = new Date(date)

    if (Number.isNaN(parsedDate.getTime())) {
      return '—'
    }

    return parsedDate.toLocaleDateString(
      'en-IN',
      {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      }
    )
  }

  /* =========================================================
     GET COURSE NAME
  ========================================================= */

  const getCourseName = (certificate) => {
    return (
      certificate?.course_name ||
      certificate?.course ||
      certificate?.course_title ||
      selectedCourse?.title ||
      selectedCourse?.name ||
      selectedCourse?.course?.title ||
      selectedCourse?.course?.name ||
      'Course'
    )
  }

  /* =========================================================
     OPEN CERTIFICATE
  ========================================================= */

  const openCertificate = async (certificate) => {
    setSelectedCertificate(certificate)
    setSelectedCourse(null)

    const courseId =
      certificate?.course_id ||
      certificate?.course?.id

    if (!courseId) {
      return
    }

    try {
      setCourseLoading(true)

      const token = localStorage.getItem('access_token')

      const response = await fetch(
        `${API_BASE}/courses/${courseId}`,
        {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      )

      const data = await response.json()

      if (response.ok) {
        setSelectedCourse(
          data.course || data
        )
      }
    } catch (error) {
      console.error(
        'COURSE DETAILS ERROR:',
        error
      )
    } finally {
      setCourseLoading(false)
    }
  }

  /* =========================================================
     CLOSE CERTIFICATE
  ========================================================= */

  const closeCertificate = () => {
    setSelectedCertificate(null)
    setSelectedCourse(null)
  }

  /* =========================================================
     DOWNLOAD CERTIFICATE
     
     Browser print dialog allows:
     Print → Save as PDF
  ========================================================= */

  const downloadCertificate = () => {
    window.print()
  }

  return (
    <DashboardLayout role="learner">

      <div className="certificates-page">

        {/* =====================================================
            HEADER
        ===================================================== */}

        <div className="certificates-header">

          <div className="title-row">

            <div className="title-icon">
              🏆
            </div>

            <div>
              <h1>
                My Certificates
              </h1>

              <p>
                Certificates earned by completing your courses.
              </p>
            </div>

          </div>

          <button
            className="refresh-button"
            onClick={fetchCertificates}
            disabled={loading}
          >
            {loading
              ? 'Loading...'
              : '↻ Refresh'}
          </button>

        </div>


        {/* =====================================================
            LOADING
        ===================================================== */}

        {loading && (
          <div className="state-card">

            <div className="loading-icon">
              ⏳
            </div>

            <h3>
              Loading certificates...
            </h3>

            <p>
              Please wait while we fetch your certificates.
            </p>

          </div>
        )}


        {/* =====================================================
            ERROR
        ===================================================== */}

        {!loading && error && (
          <div className="error-card">

            <strong>
              Unable to load certificates
            </strong>

            <p>
              {error}
            </p>

            <button
              onClick={fetchCertificates}
              className="retry-button"
            >
              Try Again
            </button>

          </div>
        )}


        {/* =====================================================
            EMPTY
        ===================================================== */}

        {!loading &&
          !error &&
          certificates.length === 0 && (

            <div className="empty-card">

              <div className="empty-icon">
                🎓
              </div>

              <h2>
                No certificates yet
              </h2>

              <p>
                Complete a course to earn your certificate.
                Your certificate will appear here automatically.
              </p>

            </div>
          )}


        {/* =====================================================
            CERTIFICATE CARDS
        ===================================================== */}

        {!loading &&
          !error &&
          certificates.length > 0 && (

            <div className="certificate-grid">

              {certificates.map((certificate) => (

                <div
                  className="certificate-card"
                  key={
                    certificate.id ||
                    certificate.certificate_id
                  }
                >

                  {/* =================================================
                      CERTIFICATE PREVIEW
                  ================================================= */}

                  <div className="certificate-preview">

                    <div className="preview-decoration">
                      🏆
                    </div>

                    <div className="preview-title">
                      CERTIFICATE
                    </div>

                    <div className="preview-subtitle">
                      OF COURSE COMPLETION
                    </div>

                    <div className="preview-line" />

                    <div className="preview-presented">
                      This certificate is proudly presented to
                    </div>

                    <div className="preview-name">
                      {certificate.learner_name ||
                        certificate.learner ||
                        'Learner'}
                    </div>

                    <div className="preview-description">
                      For successfully completing
                    </div>

                    <div className="preview-course">
                      {getCourseName(certificate)}
                    </div>

                    <div className="preview-date">
                      {formatDate(
                        certificate.end_date ||
                        certificate.completed_at ||
                        certificate.created_at
                      )}
                    </div>

                    <div className="preview-id">
                      Certificate ID:{' '}
                      {certificate.certificate_id ||
                        '—'}
                    </div>

                  </div>


                  {/* =================================================
                      CERTIFICATE DETAILS
                  ================================================= */}

                  <div className="certificate-details">

                    <div className="certificate-heading">

                      <div>

                        <h2>
                          {getCourseName(certificate)}
                        </h2>

                        <span className="valid-badge">
                          ✓ Valid Certificate
                        </span>

                      </div>

                    </div>


                    <div className="details-grid">

                      <div className="detail-item">

                        <span>
                          Learner
                        </span>

                        <strong>
                          {certificate.learner_name ||
                            certificate.learner ||
                            'Learner'}
                        </strong>

                      </div>


                      <div className="detail-item">

                        <span>
                          Course
                        </span>

                        <strong>
                          {getCourseName(certificate)}
                        </strong>

                      </div>


                      <div className="detail-item">

                        <span>
                          Started
                        </span>

                        <strong>
                          {formatDate(
                            certificate.start_date
                          )}
                        </strong>

                      </div>


                      <div className="detail-item">

                        <span>
                          Completed
                        </span>

                        <strong>
                          {formatDate(
                            certificate.end_date ||
                            certificate.completed_at
                          )}
                        </strong>

                      </div>


                      <div className="detail-item full-width">

                        <span>
                          Certificate ID
                        </span>

                        <strong>
                          {certificate.certificate_id ||
                            '—'}
                        </strong>

                      </div>

                    </div>


                    {/* =================================================
                        VIEW BUTTON
                    ================================================= */}

                    <div className="certificate-actions">

                      <button
                        className="view-button"
                        onClick={() =>
                          openCertificate(
                            certificate
                          )
                        }
                      >
                         View Certificate
                      </button>

                    </div>

                  </div>

                </div>

              ))}

            </div>
          )}

      </div>


      {/* =========================================================
          CERTIFICATE MODAL
      ========================================================= */}

      {selectedCertificate && (

        <div
          className="modal-overlay"
          onClick={closeCertificate}
        >

          <div
            className="certificate-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            {/* =====================================================
                MODAL HEADER
            ===================================================== */}

            <div className="modal-header">

              <div>

                <div className="modal-title-row">

                  <div className="modal-title-icon">
                    🏆
                  </div>

                  <div>

                    <h2>
                      Certificate
                    </h2>

                    <p>
                      {getCourseName(
                        selectedCertificate
                      )}
                    </p>

                  </div>

                </div>

              </div>

              <button
                className="close-button"
                onClick={closeCertificate}
              >
                ✕
              </button>

            </div>


            {/* =====================================================
                CERTIFICATE
            ===================================================== */}

            <div
              className="modal-certificate"
              id="print-certificate"
            >

              <div className="certificate-inner">

                <div className="modal-decoration">
                  🏆
                </div>

                <div className="modal-certificate-title">
                  CERTIFICATE
                </div>

                <div className="modal-certificate-subtitle">
                  OF COURSE COMPLETION
                </div>

                <div className="modal-divider" />

                <div className="modal-presented">
                  This certificate is proudly presented to
                </div>

                <div className="modal-name">
                  {selectedCertificate.learner_name ||
                    selectedCertificate.learner ||
                    'Learner'}
                </div>

                <div className="modal-description">
                  for successfully completing the course
                </div>

                <div className="modal-course">
                  {getCourseName(
                    selectedCertificate
                  )}
                </div>


                {/* =================================================
                    CERTIFICATE BOTTOM DETAILS
                ================================================= */}

                <div className="modal-bottom">

                  <div>

                    <span>
                      Completion Date
                    </span>

                    <strong>
                      {formatDate(
                        selectedCertificate.end_date ||
                        selectedCertificate.completed_at
                      )}
                    </strong>

                  </div>


                  <div>

                    <span>
                      Certificate ID
                    </span>

                    <strong>
                      {selectedCertificate.certificate_id ||
                        '—'}
                    </strong>

                  </div>

                </div>

              </div>

            </div>


            {/* =====================================================
                COURSE DETAILS
            ===================================================== */}

            <div className="course-details-section">

              <div className="course-details-heading">

                <div className="course-details-icon">
                  📚
                </div>

                <div>

                  <h3>
                    Course Details
                  </h3>

                  <p>
                    Information about the course completed
                    by the learner.
                  </p>

                </div>

              </div>


              {courseLoading ? (

                <div className="course-loading">
                  Loading course details...
                </div>

              ) : (

                <div className="course-details-grid">

                  {/* COURSE NAME */}

                  <div className="course-detail-item">

                    <span>
                      Course Name
                    </span>

                    <strong>
                      {getCourseName(
                        selectedCertificate
                      )}
                    </strong>

                  </div>


                  {/* COURSE ID */}

                  <div className="course-detail-item">

                    <span>
                      Course ID
                    </span>

                    <strong>
                      {selectedCertificate.course_id ||
                        selectedCourse?.id ||
                        '—'}
                    </strong>

                  </div>


                  {/* LEVEL */}

                  <div className="course-detail-item">

                    <span>
                      Level
                    </span>

                    <strong>
                      {selectedCourse?.level ||
                        selectedCourse?.difficulty ||
                        selectedCourse?.course?.level ||
                        selectedCourse?.course?.difficulty ||
                        selectedCertificate.level ||
                        '—'}
                    </strong>

                  </div>


                  {/* CATEGORY */}

                  <div className="course-detail-item">

                    <span>
                      Category
                    </span>

                    <strong>
                      {selectedCourse?.category ||
                        selectedCourse?.course?.category ||
                        selectedCertificate.category ||
                        '—'}
                    </strong>

                  </div>


                  {/* INSTRUCTOR */}

                  <div className="course-detail-item">

                    <span>
                      Instructor
                    </span>

                    <strong>
                      {selectedCourse?.instructor ||
                        selectedCourse?.instructor_name ||
                        selectedCourse?.trainer_name ||
                        selectedCourse?.course?.instructor ||
                        selectedCourse?.course?.instructor_name ||
                        selectedCertificate.instructor ||
                        selectedCertificate.instructor_name ||
                        '—'}
                    </strong>

                  </div>


                  {/* DURATION */}

                  <div className="course-detail-item">

                    <span>
                      Duration
                    </span>

                    <strong>
                      {selectedCourse?.duration ||
                        selectedCourse?.course_duration ||
                        selectedCourse?.course?.duration ||
                        selectedCertificate.duration ||
                        '—'}
                    </strong>

                  </div>


                  {/* START DATE */}

                  <div className="course-detail-item">

                    <span>
                      Started
                    </span>

                    <strong>
                      {formatDate(
                        selectedCertificate.start_date
                      )}
                    </strong>

                  </div>


                  {/* COMPLETION DATE */}

                  <div className="course-detail-item">

                    <span>
                      Completed
                    </span>

                    <strong>
                      {formatDate(
                        selectedCertificate.end_date ||
                        selectedCertificate.completed_at
                      )}
                    </strong>

                  </div>


                  {/* DESCRIPTION */}

                  <div className="course-detail-item description-item">

                    <span>
                      Course Description
                    </span>

                    <p>
                      {selectedCourse?.description ||
                        selectedCourse?.course_description ||
                        selectedCourse?.course?.description ||
                        selectedCertificate.course_description ||
                        selectedCertificate.description ||
                        'Course successfully completed by the learner.'}
                    </p>

                  </div>

                </div>

              )}

            </div>


            {/* =====================================================
                MODAL FOOTER
            ===================================================== */}

            <div className="modal-footer">

              <button
                className="close-modal-button"
                onClick={closeCertificate}
              >
                Close
              </button>


              <button
                className="download-button"
                onClick={downloadCertificate}
              >
                ⬇ Download Certificate
              </button>

            </div>

          </div>

        </div>
      )}


      {/* =========================================================
          STYLES
      ========================================================= */}

      <style>{`

        /* =====================================================
           PAGE
        ===================================================== */

        .certificates-page {
          width: 100%;
          max-width: 1200px;
          margin: 0 auto;
          padding: 32px;
          box-sizing: border-box;
        }


        /* =====================================================
           HEADER
        ===================================================== */

        .certificates-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 20px;
          margin-bottom: 28px;
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

        .certificates-header h1 {
          margin: 0 0 5px;
          color: #172033;
          font-size: 30px;
          font-weight: 700;
          letter-spacing: -0.4px;
        }

        .certificates-header p {
          margin: 0;
          color: #667085;
          font-size: 15px;
        }


        /* =====================================================
           REFRESH
        ===================================================== */

        .refresh-button {
          border: none;
          border-radius: 8px;
          background: #3764e8;
          color: white;
          padding: 11px 18px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: 0.2s ease;
        }

        .refresh-button:hover {
          background: #2f56cc;
        }

        .refresh-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }


        /* =====================================================
           STATES
        ===================================================== */

        .state-card,
        .empty-card {
          background: white;
          border: 1px solid #e4e7ec;
          border-radius: 14px;
          padding: 55px 30px;
          text-align: center;
          box-shadow:
            0 3px 12px rgba(16, 24, 40, 0.04);
        }

        .loading-icon,
        .empty-icon {
          font-size: 38px;
          margin-bottom: 12px;
        }

        .state-card h3,
        .empty-card h2 {
          margin: 0 0 8px;
          color: #172033;
        }

        .state-card p,
        .empty-card p {
          margin: 0 auto;
          max-width: 500px;
          color: #667085;
          font-size: 14px;
          line-height: 1.6;
        }


        /* =====================================================
           ERROR
        ===================================================== */

        .error-card {
          padding: 20px;
          border-radius: 12px;
          background: #fef3f2;
          border: 1px solid #fecdca;
          color: #b42318;
        }

        .error-card p {
          margin: 6px 0 14px;
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


        /* =====================================================
           GRID
        ===================================================== */

        .certificate-grid {
          display: grid;
          grid-template-columns:
            repeat(auto-fit, minmax(430px, 1fr));
          gap: 22px;
        }


        /* =====================================================
           CARD
        ===================================================== */

        .certificate-card {
          background: white;
          border: 1px solid #e4e7ec;
          border-radius: 14px;
          overflow: hidden;
          box-shadow:
            0 3px 12px rgba(16, 24, 40, 0.05);
          transition:
            transform 0.2s ease,
            box-shadow 0.2s ease;
        }

        .certificate-card:hover {
          transform: translateY(-2px);
          box-shadow:
            0 8px 22px rgba(16, 24, 40, 0.09);
        }


        /* =====================================================
           CARD PREVIEW
        ===================================================== */

        .certificate-preview {
          min-height: 245px;
          padding: 28px;
          box-sizing: border-box;
          text-align: center;

          background:
            linear-gradient(
              135deg,
              #fffdf5,
              #ffffff 50%,
              #f5f8ff
            );

          border-bottom: 1px solid #e4e7ec;
        }

        .preview-decoration {
          font-size: 24px;
          margin-bottom: 6px;
        }

        .preview-title {
          color: #172033;
          font-size: 25px;
          font-weight: 800;
          letter-spacing: 3px;
        }

        .preview-subtitle {
          margin-top: 3px;
          color: #8b6b24;
          font-size: 10px;
          font-weight: 700;
          letter-spacing: 2px;
        }

        .preview-line {
          width: 90px;
          height: 2px;
          margin: 12px auto;
          background: #c9a84e;
        }

        .preview-presented {
          color: #667085;
          font-size: 11px;
        }

        .preview-name {
          margin: 8px 0;
          color: #172033;
          font-size: 23px;
          font-weight: 600;
          font-family: Georgia, serif;
        }

        .preview-description {
          color: #667085;
          font-size: 11px;
        }

        .preview-course {
          margin-top: 5px;
          color: #8b6b24;
          font-size: 15px;
          font-weight: 700;
        }

        .preview-date {
          margin-top: 14px;
          color: #344054;
          font-size: 11px;
          font-weight: 600;
        }

        .preview-id {
          margin-top: 8px;
          color: #667085;
          font-size: 10px;
        }


        /* =====================================================
           CARD DETAILS
        ===================================================== */

        .certificate-details {
          padding: 22px;
        }

        .certificate-heading {
          margin-bottom: 18px;
        }

        .certificate-heading h2 {
          margin: 0 0 8px;
          color: #172033;
          font-size: 18px;
        }

        .valid-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 4px 8px;
          border-radius: 999px;
          background: #ecfdf3;
          border: 1px solid #abefc6;
          color: #067647;
          font-size: 11px;
          font-weight: 600;
        }


        /* =====================================================
           DETAILS GRID
        ===================================================== */

        .details-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 15px;
        }

        .detail-item {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .detail-item span {
          color: #667085;
          font-size: 11px;
        }

        .detail-item strong {
          color: #344054;
          font-size: 13px;
        }

        .full-width {
          grid-column: 1 / -1;
        }


        /* =====================================================
           VIEW BUTTON
        ===================================================== */

        .certificate-actions {
          margin-top: 20px;
        }

        .view-button {
          width: 100%;
          border: none;
          border-radius: 8px;
          padding: 11px 16px;
          background: #3764e8;
          color: white;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: 0.2s ease;
        }

        .view-button:hover {
          background: #2f56cc;
        }


        /* =====================================================
           MODAL OVERLAY
        ===================================================== */

        .modal-overlay {
          position: fixed;
          inset: 0;
          z-index: 9999;

          display: flex;
          align-items: center;
          justify-content: center;

          padding: 24px;
          box-sizing: border-box;

          background:
            rgba(15, 23, 42, 0.62);

          backdrop-filter: blur(3px);
        }


        /* =====================================================
           MODAL
        ===================================================== */

        .certificate-modal {
          width: 100%;
          max-width: 950px;

          max-height: 92vh;
          overflow-y: auto;

          background: #ffffff;
          border-radius: 16px;

          box-shadow:
            0 24px 70px rgba(0, 0, 0, 0.25);

          animation:
            certificateModalIn
            0.2s ease;
        }

        @keyframes certificateModalIn {
          from {
            opacity: 0;
            transform: translateY(12px) scale(0.98);
          }

          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }


        /* =====================================================
           MODAL HEADER
        ===================================================== */

        .modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;

          padding: 18px 22px;

          border-bottom:
            1px solid #eaecf0;
        }

        .modal-title-row {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .modal-title-icon {
          width: 38px;
          height: 38px;

          display: flex;
          align-items: center;
          justify-content: center;

          border-radius: 10px;

          background: #eef4ff;
          border: 1px solid #dbe7ff;

          font-size: 18px;
        }

        .modal-header h2 {
          margin: 0 0 3px;
          color: #172033;
          font-size: 18px;
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
          color: #344054;

          cursor: pointer;
          font-size: 15px;
        }

        .close-button:hover {
          background: #e4e7ec;
        }


        /* =====================================================
           MODAL CERTIFICATE
        ===================================================== */

        .modal-certificate {
          margin: 22px 22px 0;
          padding: 10px;

          box-sizing: border-box;

          border: 6px solid #d4b45d;

          background:
            linear-gradient(
              135deg,
              #fffdf5,
              #ffffff 50%,
              #f5f8ff
            );
        }

        .certificate-inner {
          padding: 42px 30px;

          text-align: center;

          border:
            1px solid rgba(201, 168, 78, 0.45);
        }

        .modal-decoration {
          font-size: 32px;
          margin-bottom: 8px;
        }

        .modal-certificate-title {
          color: #172033;
          font-size: 40px;
          font-weight: 800;
          letter-spacing: 7px;
        }

        .modal-certificate-subtitle {
          color: #8b6b24;
          font-size: 12px;
          font-weight: 700;
          letter-spacing: 4px;
          margin-top: 4px;
        }

        .modal-divider {
          width: 150px;
          height: 2px;
          margin: 18px auto;

          background: #c9a84e;
        }

        .modal-presented {
          color: #667085;
          font-size: 13px;
        }

        .modal-name {
          margin: 14px 0;

          color: #172033;
          font-size: 36px;

          font-family: Georgia, serif;
          font-style: italic;
        }

        .modal-description {
          color: #475467;
          font-size: 14px;
        }

        .modal-course {
          margin-top: 8px;

          color: #8b6b24;
          font-size: 23px;
          font-weight: 700;
        }


        /* =====================================================
           CERTIFICATE BOTTOM
        ===================================================== */

        .modal-bottom {
          display: grid;
          grid-template-columns: 1fr 1fr;

          gap: 30px;

          margin-top: 35px;
          padding-top: 18px;

          border-top:
            1px solid #d0d5dd;
        }

        .modal-bottom div {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }

        .modal-bottom span {
          color: #667085;
          font-size: 11px;
        }

        .modal-bottom strong {
          color: #344054;
          font-size: 13px;
        }


        /* =====================================================
           COURSE DETAILS
        ===================================================== */

        .course-details-section {
          margin: 20px 22px 0;

          padding: 20px;

          border:
            1px solid #e4e7ec;

          border-radius: 12px;

          background: #f8faff;
        }

        .course-details-heading {
          display: flex;
          align-items: center;
          gap: 11px;

          margin-bottom: 18px;
        }

        .course-details-icon {
          width: 38px;
          height: 38px;

          display: flex;
          align-items: center;
          justify-content: center;

          border-radius: 9px;

          background: #ffffff;
          border: 1px solid #dbe7ff;

          font-size: 18px;
        }

        .course-details-heading h3 {
          margin: 0 0 3px;

          color: #172033;
          font-size: 16px;
        }

        .course-details-heading p {
          margin: 0;

          color: #667085;
          font-size: 12px;
        }

        .course-details-grid {
          display: grid;

          grid-template-columns:
            1fr 1fr;

          gap: 14px 20px;
        }

        .course-detail-item {
          display: flex;
          flex-direction: column;
          gap: 5px;

          padding: 12px;

          background: #ffffff;

          border:
            1px solid #e4e7ec;

          border-radius: 8px;
        }

        .course-detail-item span {
          color: #667085;
          font-size: 11px;
          font-weight: 500;
        }

        .course-detail-item strong {
          color: #172033;
          font-size: 13px;
          font-weight: 600;
        }

        .description-item {
          grid-column: 1 / -1;
        }

        .description-item p {
          margin: 0;

          color: #475467;

          font-size: 13px;
          line-height: 1.6;
        }

        .course-loading {
          padding: 20px;

          text-align: center;

          color: #667085;
          font-size: 13px;

          background: #ffffff;
          border-radius: 8px;
          border: 1px solid #e4e7ec;
        }


        /* =====================================================
           MODAL FOOTER
        ===================================================== */

        .modal-footer {
          display: flex;

          justify-content: flex-end;

          gap: 10px;

          padding: 20px 22px 22px;
        }

        .close-modal-button {
          border:
            1px solid #d0d5dd;

          border-radius: 8px;

          padding: 10px 18px;

          background: white;
          color: #344054;

          font-size: 14px;
          font-weight: 600;

          cursor: pointer;
        }

        .close-modal-button:hover {
          background: #f9fafb;
        }

        .download-button {
          border: none;

          border-radius: 8px;

          padding: 10px 18px;

          background: #3764e8;
          color: white;

          font-size: 14px;
          font-weight: 600;

          cursor: pointer;

          transition: 0.2s ease;
        }

        .download-button:hover {
          background: #2f56cc;
        }


        /* =====================================================
           RESPONSIVE
        ===================================================== */

        @media (max-width: 700px) {

          .certificates-page {
            padding: 20px;
          }

          .certificates-header {
            align-items: flex-start;
            flex-direction: column;
          }

          .certificate-grid {
            grid-template-columns: 1fr;
          }

          .details-grid {
            grid-template-columns: 1fr;
          }

          .full-width {
            grid-column: auto;
          }

          .modal-overlay {
            padding: 10px;
          }

          .certificate-modal {
            max-height: 95vh;
          }

          .modal-certificate {
            margin: 12px 12px 0;
          }

          .certificate-inner {
            padding: 28px 14px;
          }

          .modal-certificate-title {
            font-size: 27px;
            letter-spacing: 4px;
          }

          .modal-name {
            font-size: 28px;
          }

          .modal-course {
            font-size: 18px;
          }

          .modal-bottom {
            grid-template-columns: 1fr;
            gap: 15px;
          }

          .course-details-section {
            margin: 14px 12px 0;
            padding: 14px;
          }

          .course-details-grid {
            grid-template-columns: 1fr;
          }

          .description-item {
            grid-column: auto;
          }

          .modal-footer {
            flex-direction: column-reverse;
          }

          .close-modal-button,
          .download-button {
            width: 100%;
          }
        }


        /* =====================================================
           PRINT / DOWNLOAD
           
           When Download Certificate is clicked:
           browser opens print dialog.
           Select "Save as PDF".
        ===================================================== */

        @media print {

          body * {
            visibility: hidden !important;
          }

          #print-certificate,
          #print-certificate * {
            visibility: visible !important;
          }

          #print-certificate {
            position: absolute;

            left: 0;
            top: 0;

            width: 100%;

            margin: 0 !important;

            border: 6px solid #d4b45d !important;

            box-shadow: none !important;
          }

          .certificate-inner {
            padding: 60px 40px !important;
          }

          .modal-certificate-title {
            font-size: 44px !important;
          }

          .modal-name {
            font-size: 40px !important;
          }

          .modal-course {
            font-size: 25px !important;
          }

          @page {
            size: A4 landscape;
            margin: 10mm;
          }
        }

      `}</style>

    </DashboardLayout>
  )
}