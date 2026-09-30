import React, { useEffect, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'

const API_BASE =
  `${import.meta.env.VITE_API_BASE_URL}/api`
export default function Leaderboard({ role }) {
  const [leaderboard, setLeaderboard] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchLeaderboard = async () => {
    try {
      setLoading(true)
      setError('')

      const token = localStorage.getItem('access_token')

      if (!token) {
        throw new Error(
          'Login session not found. Please login again.'
        )
      }

      /*
        Learner:
        /api/learner/leaderboard

        Trainer/Admin:
        /api/leaderboard
      */
      const isLearner = role === 'learner'

      const endpoint = isLearner
        ? `${API_BASE}/learner/leaderboard`
        : `${API_BASE}/leaderboard`

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.error ||
          data.message ||
          'Unable to load leaderboard.'
        )
      }

      /*
        The learner endpoint already returns:

        courses
        completedLessons
        progress
        rank

        The general endpoint returns:

        completed_courses
        average_progress
        quiz_score
        rank

        Convert both formats into the same frontend format.
      */

      const rawLeaderboard = data.leaderboard || []

      const normalizedLeaderboard =
       rawLeaderboard.map(
     (learner, index) => ({
          learner_id: learner.learner_id,
            user_id: learner.user_id,
            name: learner.name,
            email: learner.email || '',
            courses: learner.courses || 0,
            completedLessons:
              learner.completedLessons || 0,
            progress: learner.progress || 0,
            rank: learner.rank || index + 1,
         })
      )

      setLeaderboard(normalizedLeaderboard)
    } catch (error) {
      console.error('LEADERBOARD ERROR:', error)

      setError(
        error.message || 'Something went wrong.'
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLeaderboard()
  }, [role])

  return (
    <DashboardLayout role={role}>
      <div className="leaderboard-page">

        {/* =========================================
            HEADER
        ========================================= */}

        <div className="leaderboard-header">

          <div className="header-content">

            <div className="title-icon">
              🏆
            </div>

            <div>
              <h1>Leaderboard</h1>

              <p>
                Learners ranked by their overall course progress.
              </p>
            </div>

          </div>

          <button
            className="refresh-button"
            onClick={fetchLeaderboard}
            disabled={loading}
          >
            <span className="refresh-icon">
              ↻
            </span>

            {loading
              ? 'Loading...'
              : 'Refresh'}
          </button>

        </div>


        {/* =========================================
            LOADING
        ========================================= */}

        {loading && (
          <div className="state-card">

            <div className="loading-spinner"></div>

            <h3>
              Loading leaderboard
            </h3>

            <p>
              Fetching the latest learner progress...
            </p>

          </div>
        )}


        {/* =========================================
            ERROR
        ========================================= */}

        {!loading && error && (
          <div className="error-card">

            <div className="error-icon">
              !
            </div>

            <div>
              <strong>
                Unable to load leaderboard
              </strong>

              <p>
                {error}
              </p>
            </div>

          </div>
        )}


        {/* =========================================
            EMPTY
        ========================================= */}

        {!loading &&
          !error &&
          leaderboard.length === 0 && (

            <div className="state-card">

              <div className="empty-icon">
                🏆
              </div>

              <h3>
                No learner progress yet
              </h3>

              <p>
                The leaderboard will appear here once
                learners start completing courses.
              </p>

            </div>
          )}


        {/* =========================================
            LEADERBOARD
        ========================================= */}

        {!loading &&
          !error &&
          leaderboard.length > 0 && (

            <div className="leaderboard-card">

              {/* TABLE HEADER */}

              <div className="table-header">

                <div className="header-rank">
                  Rank
                </div>

                <div>
                  Learner
                </div>

                <div>
                  Courses
                </div>

                <div>
                  Completed Lessons
                </div>

                <div>
                  Progress
                </div>

              </div>


              {/* LEARNER ROWS */}

              {leaderboard.map((learner) => (

                <div
                  className={`leaderboard-row ${
                    learner.rank <= 3
                      ? `top-${learner.rank}`
                      : ''
                  }`}
                  key={learner.learner_id}
                >

                  {/* =================================
                      RANK
                  ================================= */}

                  <div className="rank">

                    {learner.rank === 1 && (
                      <div className="medal gold">
                        🥇
                      </div>
                    )}

                    {learner.rank === 2 && (
                      <div className="medal silver">
                        🥈
                      </div>
                    )}

                    {learner.rank === 3 && (
                      <div className="medal bronze">
                        🥉
                      </div>
                    )}

                    {learner.rank > 3 && (
                      <div className="rank-number">
                        {learner.rank}
                      </div>
                    )}

                  </div>


                  {/* =================================
                      LEARNER
                  ================================= */}

                  <div className="learner-info">

                    <div className="learner-avatar">
                      {learner.name
                        ? learner.name
                            .charAt(0)
                            .toUpperCase()
                        : '?'}
                    </div>

                    <div className="learner-details">

                      <div className="learner-name">
                        {learner.name ||
                          'Unknown Learner'}
                      </div>

                      <div className="learner-email">
                        {learner.email || ''}
                      </div>

                    </div>

                  </div>


                  {/* =================================
                      COURSES
                  ================================= */}

                  <div className="table-value">

                    <span className="number-badge">
                      {learner.courses}
                    </span>

                  </div>


                  {/* =================================
                      COMPLETED LESSONS
                  ================================= */}

                  <div className="table-value">

                    <span className="number-badge">
                      {learner.completedLessons}
                    </span>

                  </div>


                  {/* =================================
                      PROGRESS
                  ================================= */}

                  <div className="progress-cell">

                    <div className="progress-top">

                      <span className="progress-number">
                        {learner.progress}%
                      </span>

                      {learner.progress >= 100 && (
                        <span className="completed-label">
                          Completed
                        </span>
                      )}

                    </div>

                    <div className="progress-bar">

                      <div
                        className="progress-fill"
                        style={{
                          width: `${Math.min(
                            Math.max(
                              learner.progress || 0,
                              0
                            ),
                            100
                          )}%`,
                        }}
                      />

                    </div>

                  </div>

                </div>

              ))}

            </div>
          )}

      </div>


      {/* =========================================
          STYLES
      ========================================= */}

      <style>{`

        .leaderboard-page {
          width: 100%;
          max-width: 1200px;
          margin: 0 auto;
          padding: 32px;
          box-sizing: border-box;
        }

        .leaderboard-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 24px;
          margin-bottom: 26px;
        }

        .header-content {
          display: flex;
          align-items: center;
          gap: 14px;
        }

        .title-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;

          display: flex;
          align-items: center;
          justify-content: center;

          background: #eef4ff;
          border: 1px solid #dbe7ff;

          font-size: 23px;
        }

        .leaderboard-header h1 {
          margin: 0 0 5px;

          color: #172033;

          font-size: 30px;
          font-weight: 700;

          letter-spacing: -0.5px;
        }

        .leaderboard-header p {
          margin: 0;

          color: #667085;

          font-size: 14px;
          line-height: 1.5;
        }

        .refresh-button {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 7px;

          min-width: 105px;

          border: 1px solid #2f5bea;
          border-radius: 8px;

          background: #2f5bea;
          color: #ffffff;

          padding: 11px 17px;

          font-size: 14px;
          font-weight: 600;

          cursor: pointer;

          transition:
            background 0.2s ease,
            box-shadow 0.2s ease,
            transform 0.2s ease;
        }

        .refresh-button:hover {
          background: #2449c8;

          box-shadow:
            0 4px 10px rgba(47, 91, 234, 0.22);

          transform: translateY(-1px);
        }

        .refresh-button:disabled {
          opacity: 0.65;
          cursor: not-allowed;
          transform: none;
          box-shadow: none;
        }

        .refresh-icon {
          font-size: 16px;
          line-height: 1;
        }

        .state-card {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;

          min-height: 260px;

          padding: 40px;

          background: #ffffff;

          border: 1px solid #e4e7ec;
          border-radius: 14px;

          box-sizing: border-box;

          box-shadow:
            0 2px 8px rgba(16, 24, 40, 0.04);

          text-align: center;
        }

        .state-card h3 {
          margin: 16px 0 6px;

          color: #172033;

          font-size: 17px;
          font-weight: 600;
        }

        .state-card p {
          margin: 0;

          max-width: 420px;

          color: #667085;

          font-size: 14px;
          line-height: 1.5;
        }

        .loading-spinner {
          width: 36px;
          height: 36px;

          border: 3px solid #e4e7ec;
          border-top-color: #2f5bea;

          border-radius: 50%;

          animation:
            leaderboard-spin 0.8s linear infinite;
        }

        @keyframes leaderboard-spin {
          to {
            transform: rotate(360deg);
          }
        }

        .empty-icon {
          width: 58px;
          height: 58px;

          display: flex;
          align-items: center;
          justify-content: center;

          border-radius: 50%;

          background: #eef4ff;

          font-size: 27px;
        }

        .error-card {
          display: flex;
          align-items: flex-start;
          gap: 12px;

          padding: 16px 18px;

          background: #fff7f7;

          border: 1px solid #fecdca;
          border-radius: 10px;

          color: #b42318;
        }

        .error-icon {
          width: 24px;
          height: 24px;

          flex-shrink: 0;

          display: flex;
          align-items: center;
          justify-content: center;

          border-radius: 50%;

          background: #fecdca;

          color: #b42318;

          font-size: 13px;
          font-weight: 700;
        }

        .error-card strong {
          display: block;

          margin-bottom: 3px;

          font-size: 14px;
        }

        .error-card p {
          margin: 0;

          color: #b42318;

          font-size: 13px;
        }

        .leaderboard-card {
          width: 100%;

          background: #ffffff;

          border: 1px solid #e4e7ec;
          border-radius: 14px;

          overflow: hidden;

          box-shadow:
            0 4px 14px rgba(16, 24, 40, 0.06);
        }

        .table-header {
          display: grid;

          grid-template-columns:
            80px
            minmax(250px, 1.5fr)
            110px
            180px
            minmax(190px, 1fr);

          align-items: center;

          gap: 20px;

          padding: 16px 22px;

          background: #f8faff;

          border-bottom: 1px solid #e4e7ec;

          color: #667085;

          font-size: 12px;
          font-weight: 600;

          text-transform: uppercase;
          letter-spacing: 0.3px;
        }

        .header-rank {
          padding-left: 1px;
        }

        .leaderboard-row {
          display: grid;

          grid-template-columns:
            80px
            minmax(250px, 1.5fr)
            110px
            180px
            minmax(190px, 1fr);

          align-items: center;

          gap: 20px;

          min-height: 82px;

          padding: 16px 22px;

          box-sizing: border-box;

          background: #ffffff;

          border-bottom: 1px solid #eaecf0;

          transition:
            background 0.2s ease,
            box-shadow 0.2s ease;
        }

        .leaderboard-row:last-child {
          border-bottom: none;
        }

        .leaderboard-row:hover {
          background: #f8faff;

          box-shadow:
            inset 3px 0 0 #2f5bea;
        }

        .leaderboard-row.top-1 {
          background: #fffdf5;
        }

        .leaderboard-row.top-2 {
          background: #fafbff;
        }

        .leaderboard-row.top-3 {
          background: #fcfcfc;
        }

        .leaderboard-row.top-1:hover,
        .leaderboard-row.top-2:hover,
        .leaderboard-row.top-3:hover {
          background: #f8faff;
        }

        .rank {
          display: flex;
          align-items: center;
          justify-content: flex-start;
        }

        .medal {
          display: flex;
          align-items: center;
          justify-content: center;

          width: 34px;
          height: 34px;

          font-size: 21px;
        }

        .rank-number {
          width: 34px;
          height: 34px;

          display: flex;
          align-items: center;
          justify-content: center;

          color: #344054;

          font-size: 15px;
          font-weight: 700;
        }

        .learner-info {
          display: flex;
          align-items: center;

          gap: 12px;

          min-width: 0;
        }

        .learner-avatar {
          width: 42px;
          height: 42px;

          min-width: 42px;

          display: flex;
          align-items: center;
          justify-content: center;

          border-radius: 50%;

          background: #eef4ff;

          border: 1px solid #dbe7ff;

          color: #2f5bea;

          font-size: 15px;
          font-weight: 700;
        }

        .learner-details {
          min-width: 0;
        }

        .learner-name {
          margin-bottom: 3px;

          color: #172033;

          font-size: 14px;
          font-weight: 600;

          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .learner-email {
          color: #667085;

          font-size: 12px;

          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .table-value {
          color: #344054;

          font-size: 14px;
          font-weight: 600;
        }

        .number-badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;

          min-width: 30px;
          height: 28px;

          padding: 0 9px;

          box-sizing: border-box;

          background: #f2f4f7;

          border: 1px solid #eaecf0;

          border-radius: 7px;

          color: #344054;

          font-size: 13px;
          font-weight: 600;
        }

        .progress-cell {
          min-width: 0;
        }

        .progress-top {
          display: flex;
          align-items: center;
          justify-content: space-between;

          gap: 10px;

          margin-bottom: 8px;
        }

        .progress-number {
          color: #172033;

          font-size: 14px;
          font-weight: 700;
        }

        .completed-label {
          padding: 3px 7px;

          background: #ecfdf3;

          border: 1px solid #abefc6;

          border-radius: 5px;

          color: #067647;

          font-size: 10px;
          font-weight: 600;
        }

        .progress-bar {
          width: 100%;
          height: 7px;

          background: #eaecf0;

          border-radius: 999px;

          overflow: hidden;
        }

        .progress-fill {
          height: 100%;

          background: #2f5bea;

          border-radius: 999px;

          transition: width 0.5s ease;
        }

        @media (max-width: 950px) {

          .leaderboard-page {
            padding: 24px;
          }

          .leaderboard-card {
            overflow-x: auto;
          }

          .table-header,
          .leaderboard-row {
            min-width: 900px;
          }

        }

        @media (max-width: 650px) {

          .leaderboard-page {
            padding: 18px;
          }

          .leaderboard-header {
            align-items: flex-start;
            flex-direction: column;
          }

          .refresh-button {
            width: 100%;
          }

          .title-icon {
            width: 42px;
            height: 42px;
          }

          .leaderboard-header h1 {
            font-size: 25px;
          }

        }

      `}</style>

    </DashboardLayout>
  )
}