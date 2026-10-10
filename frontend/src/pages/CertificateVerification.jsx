import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

const API_BASE = `${import.meta.env.VITE_API_BASE_URL}/api`

export default function CertificateVerification() {
  const { certificateNumber } = useParams()

  const [loading, setLoading] = useState(true)
  const [certificate, setCertificate] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    verifyCertificate()
  }, [certificateNumber])

  async function verifyCertificate() {
    if (!certificateNumber) {
      setError('Certificate ID is missing.')
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError('')

      const response = await fetch(
        `${API_BASE}/certificates/${encodeURIComponent(certificateNumber)}`,
        {
          method: 'GET',
          headers: {
            Accept: 'application/json',
          },
        }
      )

      const data = await response.json().catch(() => null)

      if (!response.ok) {
        throw new Error(
          data?.error || 'Certificate could not be verified.'
        )
      }

      if (!data?.valid || !data?.certificate) {
        setCertificate(data?.certificate || null)
        setError('This certificate is not valid.')
        return
      }

      setCertificate(data.certificate)
    } catch (err) {
      console.error('CERTIFICATE VERIFICATION ERROR:', err)

      setCertificate(null)
      setError(
        err.message || 'Unable to verify this certificate.'
      )
    } finally {
      setLoading(false)
    }
  }

  function formatDate(date) {
    if (!date) return '—'

    const parsed = new Date(date)

    if (Number.isNaN(parsed.getTime())) {
      return date
    }

    return parsed.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
    })
  }

  if (loading) {
    return (
      <div className="verification-page">
        <div className="verification-card loading-card">
          <div className="loading-icon">🔍</div>
          <h1>Verifying Certificate</h1>
          <p>Please wait while we verify the certificate.</p>
        </div>

        <VerificationStyles />
      </div>
    )
  }

  return (
    <div className="verification-page">
      <div className="verification-card">

        <div className="verification-header">
          <div className="brand-icon">🎓</div>

          <div>
            <div className="brand-name">
              DevSprint LMS
            </div>

            <div className="brand-subtitle">
              Certificate Verification
            </div>
          </div>
        </div>

        {certificate && !error ? (
          <>
            <div className="valid-icon">
              ✓
            </div>

            <h1>Certificate Verified</h1>

            <p className="verification-message">
              This certificate has been successfully verified
              against the DevSprint LMS records.
            </p>

            <div className="status-badge valid">
              ✓ VALID CERTIFICATE
            </div>

            <div className="certificate-details">

              <div className="detail-row">
                <span className="detail-label">
                  Certificate ID
                </span>

                <strong className="certificate-id">
                  {certificate.certificate_id || '—'}
                </strong>
              </div>

              <div className="detail-row">
                <span className="detail-label">
                  Learner
                </span>

                <strong>
                  {certificate.learner_name || '—'}
                </strong>
              </div>

              <div className="detail-row">
                <span className="detail-label">
                  Course
                </span>

                <strong>
                  {certificate.course_title || '—'}
                </strong>
              </div>

              <div className="detail-row">
                <span className="detail-label">
                  Course Start
                </span>

                <strong>
                  {formatDate(certificate.start_date)}
                </strong>
              </div>

              <div className="detail-row">
                <span className="detail-label">
                  Course End
                </span>

                <strong>
                  {formatDate(certificate.end_date)}
                </strong>
              </div>

              <div className="detail-row">
                <span className="detail-label">
                  Certificate Status
                </span>

                <strong className="valid-text">
                  {certificate.status || 'Valid'}
                </strong>
              </div>

            </div>

            <div className="verification-footer">
              <span>✓</span>

              <p>
                This certificate was verified directly
                from the DevSprint LMS certificate database.
              </p>
            </div>
          </>
        ) : (
          <>
            <div className="invalid-icon">
              !
            </div>

            <h1>Certificate Not Verified</h1>

            <p className="verification-message">
              {error ||
                'The certificate could not be verified.'}
            </p>

            <div className="status-badge invalid">
              ✕ INVALID CERTIFICATE
            </div>

            <div className="invalid-details">
              <p>
                The certificate ID may be incorrect,
                expired, revoked, or may not exist in
                the DevSprint LMS records.
              </p>

              {certificate?.certificate_id && (
                <div className="invalid-id">
                  Certificate ID:
                  <strong>
                    {certificate.certificate_id}
                  </strong>
                </div>
              )}
            </div>
          </>
        )}

        <div className="page-footer">
          <span>
            DevSprint LMS
          </span>

          <span>
            Secure Certificate Verification
          </span>
        </div>
      </div>

      <VerificationStyles />
    </div>
  )
}

function VerificationStyles() {
  return (
    <style>{`
      * {
        box-sizing: border-box;
      }

      .verification-page {
        min-height: 100vh;
        background:
          linear-gradient(
            135deg,
            #eef2ff 0%,
            #f8fafc 50%,
            #eff6ff 100%
          );
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 40px 20px;
        font-family:
          Inter,
          -apple-system,
          BlinkMacSystemFont,
          "Segoe UI",
          sans-serif;
      }

      .verification-card {
        width: 100%;
        max-width: 760px;
        background: white;
        border-radius: 24px;
        padding: 42px;
        box-shadow:
          0 20px 60px rgba(15, 23, 42, 0.12);
        text-align: center;
      }

      .loading-card {
        max-width: 560px;
      }

      .verification-header {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 14px;
        padding-bottom: 28px;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 32px;
      }

      .brand-icon {
        width: 54px;
        height: 54px;
        border-radius: 14px;
        background: #eef2ff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 27px;
      }

      .brand-name {
        font-size: 20px;
        font-weight: 800;
        color: #111827;
        text-align: left;
      }

      .brand-subtitle {
        margin-top: 3px;
        font-size: 13px;
        color: #6b7280;
        text-align: left;
      }

      .valid-icon,
      .invalid-icon,
      .loading-icon {
        width: 82px;
        height: 82px;
        margin: 0 auto 20px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 42px;
        font-weight: 800;
      }

      .valid-icon {
        background: #dcfce7;
        color: #15803d;
      }

      .invalid-icon {
        background: #fee2e2;
        color: #dc2626;
      }

      .loading-icon {
        background: #eef2ff;
        font-size: 34px;
      }

      .verification-card h1 {
        margin: 0;
        color: #111827;
        font-size: 30px;
        font-weight: 800;
      }

      .verification-message {
        max-width: 580px;
        margin: 12px auto 20px;
        color: #6b7280;
        font-size: 15px;
        line-height: 1.7;
      }

      .status-badge {
        display: inline-block;
        padding: 9px 16px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.4px;
      }

      .status-badge.valid {
        background: #dcfce7;
        color: #166534;
      }

      .status-badge.invalid {
        background: #fee2e2;
        color: #991b1b;
      }

      .certificate-details {
        margin-top: 32px;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        overflow: hidden;
        text-align: left;
      }

      .detail-row {
        display: grid;
        grid-template-columns: 180px 1fr;
        gap: 20px;
        padding: 17px 20px;
        border-bottom: 1px solid #e5e7eb;
      }

      .detail-row:last-child {
        border-bottom: none;
      }

      .detail-row:nth-child(even) {
        background: #f9fafb;
      }

      .detail-label {
        color: #6b7280;
        font-size: 13px;
        font-weight: 700;
      }

      .detail-row strong {
        color: #111827;
        font-size: 14px;
        word-break: break-word;
      }

      .certificate-id {
        font-family: monospace;
        font-size: 13px !important;
      }

      .valid-text {
        color: #15803d !important;
        text-transform: uppercase;
      }

      .verification-footer {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        margin-top: 28px;
        padding: 15px 18px;
        background: #f0fdf4;
        border-radius: 12px;
        color: #166534;
      }

      .verification-footer span {
        font-size: 18px;
        font-weight: 800;
      }

      .verification-footer p {
        margin: 0;
        font-size: 12px;
        line-height: 1.5;
      }

      .invalid-details {
        margin-top: 28px;
        padding: 20px;
        background: #fef2f2;
        border-radius: 12px;
        color: #7f1d1d;
        font-size: 14px;
        line-height: 1.6;
      }

      .invalid-details p {
        margin: 0;
      }

      .invalid-id {
        margin-top: 12px;
        display: flex;
        flex-direction: column;
        gap: 4px;
      }

      .page-footer {
        margin-top: 32px;
        padding-top: 20px;
        border-top: 1px solid #e5e7eb;
        display: flex;
        justify-content: space-between;
        gap: 20px;
        color: #9ca3af;
        font-size: 12px;
      }

      @media (max-width: 600px) {
        .verification-page {
          padding: 20px 12px;
        }

        .verification-card {
          padding: 28px 20px;
          border-radius: 18px;
        }

        .verification-card h1 {
          font-size: 25px;
        }

        .detail-row {
          grid-template-columns: 1fr;
          gap: 5px;
        }

        .page-footer {
          flex-direction: column;
          align-items: center;
        }
      }
    `}</style>
  )
}