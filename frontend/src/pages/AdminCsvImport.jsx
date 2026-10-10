import { useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import { apiRequest } from '../services/api'

export default function AdminCsvImport() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const downloadTemplate = async () => {
    try {
      setError('')
      setMessage('')

      const token = localStorage.getItem('access_token')

      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/admin/learners/import-csv/template`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      if (!response.ok) {
        const data = await response.json().catch(() => null)
        throw new Error(data?.error || 'Unable to download template')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = url
      link.download = 'learner_import_template.csv'
      document.body.appendChild(link)
      link.click()
      link.remove()

      window.URL.revokeObjectURL(url)

      setMessage('CSV template downloaded successfully.')
    } catch (err) {
      setError(err.message || 'Unable to download template')
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a CSV file first.')
      return
    }

    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError('Please select a CSV file.')
      return
    }

    try {
      setLoading(true)
      setError('')
      setMessage('')
      setResult(null)

      const token = localStorage.getItem('access_token')

      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/admin/learners/import-csv`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        }
      )

      const data = await response.json().catch(() => null)

      if (!response.ok) {
        throw new Error(
          data?.error || data?.message || 'CSV import failed'
        )
      }

      setResult(data)
      setMessage(data.message || 'CSV import completed successfully.')
      setFile(null)

      const fileInput = document.getElementById('csv-file')
      if (fileInput) {
        fileInput.value = ''
      }
    } catch (err) {
      setError(err.message || 'CSV import failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <DashboardLayout role="admin">
      <div className="csv-page">
        <div className="page-header">
          <div>
            <h1>Bulk User Import</h1>
            <p>
              Import multiple learners into DevSprint LMS using a CSV file.
            </p>
          </div>

          <button
            type="button"
            className="template-button"
            onClick={downloadTemplate}
          >
            📥 Download CSV Template
          </button>
        </div>

        <div className="info-card">
          <h2>CSV Format</h2>

          <p>
            Your CSV file must contain these required columns:
          </p>

          <div className="columns">
            <span>name</span>
            <span>email</span>
            <span>password</span>
            <span>mobile</span>
            <span>education</span>
          </div>

          <p className="note">
            Passwords must contain at least 8 characters.
            Existing email addresses will be skipped.
          </p>
        </div>

        <div className="upload-card">
          <h2>Upload Learners</h2>

          <label htmlFor="csv-file" className="file-label">
            Select CSV File
          </label>

          <input
            id="csv-file"
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => {
              setFile(event.target.files?.[0] || null)
              setError('')
              setMessage('')
              setResult(null)
            }}
          />

          {file && (
            <div className="selected-file">
              <span>📄</span>
              <strong>{file.name}</strong>
              <span>
                {(file.size / 1024).toFixed(1)} KB
              </span>
            </div>
          )}

          <button
            type="button"
            className="upload-button"
            onClick={handleUpload}
            disabled={loading || !file}
          >
            {loading ? 'Uploading...' : '📤 Import Learners'}
          </button>
        </div>

        {message && (
          <div className="success-message">
            ✅ {message}
          </div>
        )}

        {error && (
          <div className="error-message">
            ❌ {error}
          </div>
        )}

        {result && (
          <div className="result-section">
            <h2>Import Result</h2>

            <div className="summary-grid">
              <div className="summary-card">
                <span>Created</span>
                <strong>
                  {result.summary?.created ?? 0}
                </strong>
              </div>

              <div className="summary-card">
                <span>Skipped</span>
                <strong>
                  {result.summary?.skipped ?? 0}
                </strong>
              </div>

              <div className="summary-card">
                <span>Errors</span>
                <strong>
                  {result.summary?.errors ?? 0}
                </strong>
              </div>

              <div className="summary-card">
                <span>Total Rows</span>
                <strong>
                  {result.summary?.total_rows ?? 0}
                </strong>
              </div>
            </div>

            {result.created?.length > 0 && (
              <div className="details-card">
                <h3>Created Learners</h3>

                {result.created.map((item, index) => (
                  <div
                    className="detail-row"
                    key={`${item.email}-${index}`}
                  >
                    <span>
                      Row {item.row}
                    </span>

                    <strong>
                      {item.name}
                    </strong>

                    <span>
                      {item.email}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {result.skipped?.length > 0 && (
              <div className="details-card">
                <h3>Skipped Rows</h3>

                {result.skipped.map((item, index) => (
                  <div
                    className="detail-row"
                    key={`${item.email}-${index}`}
                  >
                    <span>
                      Row {item.row}
                    </span>

                    <strong>
                      {item.email}
                    </strong>

                    <span>
                      {item.reason}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {result.errors?.length > 0 && (
              <div className="details-card">
                <h3>Errors</h3>

                {result.errors.map((item, index) => (
                  <div
                    className="detail-row error-row"
                    key={`${item.row}-${index}`}
                  >
                    <span>
                      Row {item.row}
                    </span>

                    <strong>
                      {item.email || 'Unknown email'}
                    </strong>

                    <span>
                      {item.error}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <style>{`
          .csv-page {
            max-width: 1100px;
            margin: 0 auto;
            padding: 28px;
          }

          .page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
            margin-bottom: 24px;
          }

          .page-header h1 {
            margin: 0 0 8px;
            font-size: 30px;
          }

          .page-header p {
            margin: 0;
            color: #64748b;
          }

          .template-button,
          .upload-button {
            border: none;
            border-radius: 10px;
            padding: 12px 18px;
            font-weight: 700;
            cursor: pointer;
          }

          .template-button {
            background: #e2e8f0;
            color: #0f172a;
          }

          .upload-button {
            width: 100%;
            margin-top: 20px;
            background: #2563eb;
            color: white;
          }

          .upload-button:disabled {
            opacity: 0.55;
            cursor: not-allowed;
          }

          .info-card,
          .upload-card,
          .details-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05);
          }

          .info-card h2,
          .upload-card h2,
          .result-section h2 {
            margin-top: 0;
          }

          .columns {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 18px 0;
          }

          .columns span {
            background: #eff6ff;
            color: #1d4ed8;
            padding: 8px 12px;
            border-radius: 8px;
            font-family: monospace;
            font-weight: 600;
          }

          .note {
            color: #64748b;
            font-size: 14px;
          }

          .file-label {
            display: block;
            margin-bottom: 8px;
            font-weight: 700;
          }

          input[type="file"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            box-sizing: border-box;
          }

          .selected-file {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 14px;
            padding: 12px;
            background: #f8fafc;
            border-radius: 10px;
          }

          .selected-file span:last-child {
            margin-left: auto;
            color: #64748b;
            font-size: 13px;
          }

          .success-message,
          .error-message {
            padding: 14px 18px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-weight: 600;
          }

          .success-message {
            background: #ecfdf5;
            color: #047857;
          }

          .error-message {
            background: #fef2f2;
            color: #b91c1c;
          }

          .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 20px;
          }

          .summary-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 20px;
          }

          .summary-card span {
            display: block;
            color: #64748b;
            font-size: 14px;
            margin-bottom: 8px;
          }

          .summary-card strong {
            font-size: 28px;
          }

          .detail-row {
            display: grid;
            grid-template-columns: 80px 1fr 1.5fr;
            gap: 16px;
            padding: 12px 0;
            border-bottom: 1px solid #e2e8f0;
          }

          .detail-row:last-child {
            border-bottom: none;
          }

          .error-row {
            color: #b91c1c;
          }

          @media (max-width: 800px) {
            .page-header {
              flex-direction: column;
              align-items: stretch;
            }

            .summary-grid {
              grid-template-columns: repeat(2, 1fr);
            }

            .detail-row {
              grid-template-columns: 1fr;
              gap: 4px;
            }
          }

          @media (max-width: 500px) {
            .csv-page {
              padding: 16px;
            }

            .summary-grid {
              grid-template-columns: 1fr;
            }
          }
        `}</style>
      </div>
    </DashboardLayout>
  )
}