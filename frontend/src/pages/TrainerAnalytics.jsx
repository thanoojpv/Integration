import React, { useEffect, useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import { apiRequest } from "../services/api";


export default function TrainerAnalytics() {

  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  // =========================================================
  // LOAD ANALYTICS
  // =========================================================

  const loadAnalytics = async () => {

    try {

      setLoading(true);
      setError("");

      const data = await apiRequest(
        "/trainer/analytics"
      );

      setAnalytics(data);

    } catch (err) {

      console.error(
        "Trainer analytics error:",
        err
      );

      setError(
        err.message ||
        "Unable to load trainer analytics."
      );

    } finally {

      setLoading(false);

    }
  };


  useEffect(() => {

    loadAnalytics();

  }, []);


  // =========================================================
  // LOADING
  // =========================================================

  if (loading) {

    return (

      <DashboardLayout role="trainer">

        <div style={styles.centerState}>

          <div style={styles.spinner}>
            ⏳
          </div>

          <h2>
            Loading analytics...
          </h2>

          <p>
            Please wait while we collect
            your course data.
          </p>

        </div>

      </DashboardLayout>

    );
  }


  // =========================================================
  // ERROR
  // =========================================================

  if (error) {

    return (

      <DashboardLayout role="trainer">

        <div style={styles.centerState}>

          <div style={styles.errorIcon}>
            ⚠️
          </div>

          <h2>
            Unable to load analytics
          </h2>

          <p style={styles.errorText}>
            {error}
          </p>

          <button
            onClick={loadAnalytics}
            style={styles.retryButton}
          >
            🔄 Try Again
          </button>

        </div>

      </DashboardLayout>

    );
  }


  const summary =
    analytics?.summary || {};

  const lessonDropoff =
    analytics?.lesson_dropoff || [];

  const quizQuestions =
    analytics?.quiz_questions || [];

  const assignments =
    analytics?.assignments || [];


  // =========================================================
  // MAIN PAGE
  // =========================================================

  return (

    <DashboardLayout role="trainer">

      <div style={styles.page}>

        {/* =================================================
            HEADER
        ================================================= */}

        <div style={styles.header}>

          <div>

            <div style={styles.eyebrow}>
              TRAINER ANALYTICS
            </div>

            <h1 style={styles.title}>
              Course Analytics
            </h1>

            <p style={styles.subtitle}>
              Understand learner progress,
              difficult quiz questions,
              and assignment submissions.
            </p>

          </div>


          <button
            onClick={loadAnalytics}
            style={styles.refreshButton}
          >
            🔄 Refresh
          </button>

        </div>


        {/* =================================================
            SUMMARY CARDS
        ================================================= */}

        <div style={styles.summaryGrid}>

          <SummaryCard
            icon="📚"
            label="Courses"
            value={summary.courses || 0}
          />

          <SummaryCard
            icon="👥"
            label="Learners"
            value={summary.learners || 0}
          />

          <SummaryCard
            icon="📖"
            label="Lessons Completed"
            value={summary.lesson_completed || 0}
          />

          <SummaryCard
            icon="📉"
            label="Lesson Drop-offs"
            value={summary.lesson_dropoff || 0}
          />

          <SummaryCard
            icon="📝"
            label="Quizzes"
            value={summary.quizzes || 0}
          />

          <SummaryCard
            icon="📅"
            label="Assignments"
            value={summary.assignments || 0}
          />

        </div>


        {/* =================================================
            LESSON DROP-OFF
        ================================================= */}

        <section style={styles.section}>

          <div style={styles.sectionHeader}>

            <div>

              <h2 style={styles.sectionTitle}>
                📉 Lesson Drop-off
              </h2>

              <p style={styles.sectionDescription}>
                Shows lessons where learners
                started but did not complete them.
              </p>

            </div>

          </div>


          {lessonDropoff.length === 0 ? (

            <EmptyState
              icon="📖"
              message="No lesson progress data available yet."
            />

          ) : (

            <div style={styles.tableWrapper}>

              <table style={styles.table}>

                <thead>

                  <tr>

                    <th style={styles.th}>
                      Lesson
                    </th>

                    <th style={styles.th}>
                      Course
                    </th>

                    <th style={styles.th}>
                      Started
                    </th>

                    <th style={styles.th}>
                      Completed
                    </th>

                    <th style={styles.th}>
                      Drop-off
                    </th>

                    <th style={styles.th}>
                      Rate
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {lessonDropoff.map(
                    (lesson) => (

                      <tr
                        key={lesson.lesson_id}
                        style={styles.tr}
                      >

                        <td style={styles.td}>

                          <strong>
                            {lesson.lesson_title}
                          </strong>

                        </td>

                        <td style={styles.td}>
                          {lesson.course_title}
                        </td>

                        <td style={styles.td}>
                          {lesson.started}
                        </td>

                        <td style={styles.td}>
                          {lesson.completed}
                        </td>

                        <td style={styles.td}>

                          <span
                            style={
                              lesson.dropoff > 0
                                ? styles.badgeDanger
                                : styles.badgeSuccess
                            }
                          >
                            {lesson.dropoff}
                          </span>

                        </td>

                        <td style={styles.td}>

                          <div
                            style={
                              styles.progressContainer
                            }
                          >

                            <div
                              style={{
                                ...styles.progressBar,
                                width: `${Math.min(
                                  lesson.dropoff_percentage || 0,
                                  100
                                )}%`,
                              }}
                            />

                          </div>

                          <span
                            style={
                              styles.percentage
                            }
                          >
                            {lesson.dropoff_percentage || 0}%
                          </span>

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
            QUIZ QUESTION ANALYTICS
        ================================================= */}

        <section style={styles.section}>

          <div style={styles.sectionHeader}>

            <div>

              <h2 style={styles.sectionTitle}>
                📝 Most Difficult Quiz Questions
              </h2>

              <p style={styles.sectionDescription}>
                Questions with the highest percentage
                of incorrect answers appear first.
              </p>

            </div>

          </div>


          {quizQuestions.length === 0 ? (

            <EmptyState
              icon="📝"
              message="No quiz answer data available yet."
            />

          ) : (

            <div style={styles.tableWrapper}>

              <table style={styles.table}>

                <thead>

                  <tr>

                    <th style={styles.th}>
                      Question
                    </th>

                    <th style={styles.th}>
                      Quiz
                    </th>

                    <th style={styles.th}>
                      Attempts
                    </th>

                    <th style={styles.th}>
                      Correct
                    </th>

                    <th style={styles.th}>
                      Wrong
                    </th>

                    <th style={styles.th}>
                      Wrong %
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {quizQuestions.map(
                    (question) => (

                      <tr
                        key={question.question_id}
                        style={styles.tr}
                      >

                        <td style={styles.questionCell}>

                          {question.question}

                        </td>

                        <td style={styles.td}>
                          {question.quiz_title}
                        </td>

                        <td style={styles.td}>
                          {question.attempts}
                        </td>

                        <td style={styles.td}>

                          <span
                            style={styles.badgeSuccess}
                          >
                            {question.correct}
                          </span>

                        </td>

                        <td style={styles.td}>

                          <span
                            style={
                              question.wrong > 0
                                ? styles.badgeDanger
                                : styles.badgeSuccess
                            }
                          >
                            {question.wrong}
                          </span>

                        </td>

                        <td style={styles.td}>

                          <strong
                            style={{
                              color:
                                question.wrong_percentage >= 70
                                  ? "#dc2626"
                                  : question.wrong_percentage >= 40
                                  ? "#d97706"
                                  : "#15803d",
                            }}
                          >
                            {question.wrong_percentage}%
                          </strong>

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
            ASSIGNMENT ANALYTICS
        ================================================= */}

        <section style={styles.section}>

          <div style={styles.sectionHeader}>

            <div>

              <h2 style={styles.sectionTitle}>
                📅 Assignment Submission Analytics
              </h2>

              <p style={styles.sectionDescription}>
                See how learners are submitting
                assignments.
              </p>

            </div>

          </div>


          {assignments.length === 0 ? (

            <EmptyState
              icon="📅"
              message="No assignments have been created for your courses yet."
            />

          ) : (

            <div style={styles.tableWrapper}>

              <table style={styles.table}>

                <thead>

                  <tr>

                    <th style={styles.th}>
                      Assignment
                    </th>

                    <th style={styles.th}>
                      Enrolled
                    </th>

                    <th style={styles.th}>
                      On Time
                    </th>

                    <th style={styles.th}>
                      Late
                    </th>

                    <th style={styles.th}>
                      Missing
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {assignments.map(
                    (assignment) => (

                      <tr
                        key={assignment.assignment_id}
                        style={styles.tr}
                      >

                        <td style={styles.td}>

                          <strong>
                            {assignment.title}
                          </strong>

                        </td>

                        <td style={styles.td}>
                          {assignment.enrolled}
                        </td>

                        <td style={styles.td}>

                          <span
                            style={styles.badgeSuccess}
                          >
                            {assignment.on_time}
                          </span>

                        </td>

                        <td style={styles.td}>

                          <span
                            style={
                              assignment.late > 0
                                ? styles.badgeWarning
                                : styles.badgeSuccess
                            }
                          >
                            {assignment.late}
                          </span>

                        </td>

                        <td style={styles.td}>

                          <span
                            style={
                              assignment.missing > 0
                                ? styles.badgeDanger
                                : styles.badgeSuccess
                            }
                          >
                            {assignment.missing}
                          </span>

                        </td>

                      </tr>

                    )
                  )}

                </tbody>

              </table>

            </div>

          )}

        </section>

      </div>

    </DashboardLayout>
  );
}


// =========================================================
// SUMMARY CARD
// =========================================================

function SummaryCard({
  icon,
  label,
  value,
}) {

  return (

    <div style={styles.summaryCard}>

      <div style={styles.summaryIcon}>
        {icon}
      </div>

      <div>

        <div style={styles.summaryValue}>
          {value}
        </div>

        <div style={styles.summaryLabel}>
          {label}
        </div>

      </div>

    </div>
  );
}


// =========================================================
// EMPTY STATE
// =========================================================

function EmptyState({
  icon,
  message,
}) {

  return (

    <div style={styles.emptyState}>

      <div style={styles.emptyIcon}>
        {icon}
      </div>

      <p>
        {message}
      </p>

    </div>
  );
}


// =========================================================
// STYLES
// =========================================================

const styles = {

  page: {
    padding: "28px",
    maxWidth: "1400px",
    margin: "0 auto",
  },

  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: "20px",
    marginBottom: "28px",
  },

  eyebrow: {
    fontSize: "12px",
    fontWeight: "700",
    letterSpacing: "1.5px",
    color: "#64748b",
    marginBottom: "6px",
  },

  title: {
    margin: "0",
    fontSize: "32px",
    fontWeight: "800",
    color: "#0f172a",
  },

  subtitle: {
    marginTop: "8px",
    color: "#64748b",
    fontSize: "15px",
  },

  refreshButton: {
    border: "none",
    borderRadius: "10px",
    padding: "11px 18px",
    background: "#0f172a",
    color: "#fff",
    fontWeight: "700",
    cursor: "pointer",
  },

  summaryGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(auto-fit, minmax(180px, 1fr))",
    gap: "16px",
    marginBottom: "28px",
  },

  summaryCard: {
    display: "flex",
    alignItems: "center",
    gap: "14px",
    padding: "20px",
    background: "#fff",
    border: "1px solid #e2e8f0",
    borderRadius: "14px",
    boxShadow:
      "0 4px 15px rgba(15, 23, 42, 0.05)",
  },

  summaryIcon: {
    width: "46px",
    height: "46px",
    borderRadius: "12px",
    background: "#f1f5f9",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "22px",
  },

  summaryValue: {
    fontSize: "25px",
    fontWeight: "800",
    color: "#0f172a",
  },

  summaryLabel: {
    marginTop: "3px",
    fontSize: "13px",
    color: "#64748b",
  },

  section: {
    background: "#fff",
    border:
      "1px solid #e2e8f0",
    borderRadius: "16px",
    marginBottom: "24px",
    overflow: "hidden",
    boxShadow:
      "0 4px 18px rgba(15, 23, 42, 0.04)",
  },

  sectionHeader: {
    padding: "22px 24px",
    borderBottom:
      "1px solid #e2e8f0",
  },

  sectionTitle: {
    margin: "0",
    fontSize: "20px",
    fontWeight: "800",
    color: "#0f172a",
  },

  sectionDescription: {
    margin: "6px 0 0",
    color: "#64748b",
    fontSize: "14px",
  },

  tableWrapper: {
    width: "100%",
    overflowX: "auto",
  },

  table: {
    width: "100%",
    borderCollapse: "collapse",
    minWidth: "850px",
  },

  th: {
    padding: "13px 18px",
    textAlign: "left",
    background: "#f8fafc",
    color: "#475569",
    fontSize: "12px",
    fontWeight: "800",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },

  tr: {
    borderTop:
      "1px solid #f1f5f9",
  },

  td: {
    padding: "15px 18px",
    color: "#334155",
    fontSize: "14px",
    verticalAlign: "middle",
  },

  questionCell: {
    padding: "15px 18px",
    color: "#334155",
    fontSize: "14px",
    maxWidth: "420px",
    lineHeight: "1.5",
  },

  badgeSuccess: {
    display: "inline-block",
    padding: "5px 9px",
    borderRadius: "999px",
    background: "#dcfce7",
    color: "#166534",
    fontSize: "12px",
    fontWeight: "800",
  },

  badgeWarning: {
    display: "inline-block",
    padding: "5px 9px",
    borderRadius: "999px",
    background: "#fef3c7",
    color: "#92400e",
    fontSize: "12px",
    fontWeight: "800",
  },

  badgeDanger: {
    display: "inline-block",
    padding: "5px 9px",
    borderRadius: "999px",
    background: "#fee2e2",
    color: "#991b1b",
    fontSize: "12px",
    fontWeight: "800",
  },

  progressContainer: {
    width: "110px",
    height: "7px",
    background: "#e2e8f0",
    borderRadius: "999px",
    overflow: "hidden",
    display: "inline-block",
    verticalAlign: "middle",
    marginRight: "8px",
  },

  progressBar: {
    height: "100%",
    background: "#ef4444",
    borderRadius: "999px",
  },

  percentage: {
    fontSize: "12px",
    color: "#64748b",
    fontWeight: "700",
  },

  emptyState: {
    padding: "50px 24px",
    textAlign: "center",
    color: "#64748b",
  },

  emptyIcon: {
    fontSize: "38px",
    marginBottom: "10px",
  },

  centerState: {
    minHeight: "60vh",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    textAlign: "center",
    padding: "30px",
  },

  spinner: {
    fontSize: "42px",
    marginBottom: "10px",
  },

  errorIcon: {
    fontSize: "42px",
    marginBottom: "10px",
  },

  errorText: {
    color: "#dc2626",
    maxWidth: "600px",
  },

  retryButton: {
    marginTop: "12px",
    border: "none",
    borderRadius: "10px",
    padding: "11px 18px",
    background: "#2563eb",
    color: "#fff",
    fontWeight: "700",
    cursor: "pointer",
  },

};