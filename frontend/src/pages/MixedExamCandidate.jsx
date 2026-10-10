import React, {
  useEffect,
  useMemo,
  useState,
} from "react";
import { useParams } from "react-router-dom";
import { apiRequest } from "../services/api";

export default function MixedExamCandidate() {
  const { inviteCode } = useParams();

  // ============================================================
  // PAGE STATE
  // ============================================================

  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);

  const [error, setError] = useState("");

  const [invite, setInvite] = useState(null);
  const [exam, setExam] = useState(null);

  // ============================================================
  // CANDIDATE INFORMATION
  // ============================================================

  const [candidateName, setCandidateName] = useState("");
  const [candidateEmail, setCandidateEmail] = useState("");

  // ============================================================
  // ATTEMPT
  // ============================================================

  const [attempt, setAttempt] = useState(null);
  const [attemptId, setAttemptId] = useState(null);

  // ============================================================
  // ANSWERS
  // ============================================================

  const [answers, setAnswers] = useState({});
  const [savingQuestion, setSavingQuestion] = useState(null);

  // ============================================================
  // CURRENT QUESTION
  // ============================================================

  const [currentQuestionIndex, setCurrentQuestionIndex] =
    useState(0);

  // ============================================================
  // TIMER
  // ============================================================

  const [remainingSeconds, setRemainingSeconds] =
    useState(null);

  // ============================================================
  // SUBMISSION / RESULT
  // ============================================================

  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState(null);

  // ============================================================
  // LOAD INVITE
  // ============================================================

  useEffect(() => {
    loadInvite();
  }, [inviteCode]);

  const loadInvite = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await apiRequest(
        `/mixed-exam/invites/${inviteCode}`
      );

      setInvite(data?.invite || null);
      setExam(data?.exam || null);

      if (data?.invite?.candidate_name) {
        setCandidateName(
          data.invite.candidate_name
        );
      }

      if (data?.invite?.candidate_email) {
        setCandidateEmail(
          data.invite.candidate_email
        );
      }
    } catch (err) {
      setError(
        err.message ||
          "This invitation link is invalid or has expired."
      );
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // FORMAT TIME
  // ============================================================

  const formatTime = (seconds) => {
    if (
      seconds === null ||
      seconds === undefined ||
      seconds < 0
    ) {
      return "--:--";
    }

    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;

    return `${String(minutes).padStart(
      2,
      "0"
    )}:${String(secs).padStart(2, "0")}`;
  };

  // ============================================================
  // START EXAM
  // ============================================================

  const startExam = async (event) => {
    event.preventDefault();

    if (!candidateName.trim()) {
      alert("Please enter your name.");
      return;
    }

    if (!candidateEmail.trim()) {
      alert("Please enter your email.");
      return;
    }

    try {
      setStarting(true);
      setError("");

      const data = await apiRequest(
        `/mixed-exam/invites/${inviteCode}/start`,
        {
          method: "POST",
          body: JSON.stringify({
            candidate_name:
              candidateName.trim(),
            candidate_email:
              candidateEmail.trim(),
          }),
        }
      );

      const newAttempt =
        data?.attempt || null;

      const newAttemptId =
        data?.attempt_id ||
        newAttempt?.id ||
        data?.id;

      if (!newAttemptId) {
        throw new Error(
          "The exam started, but no attempt ID was returned."
        );
      }

      setAttempt(newAttempt);
      setAttemptId(newAttemptId);

      const durationMinutes = Number(
        data?.duration_minutes ||
          newAttempt?.duration_minutes ||
          exam?.duration_minutes ||
          60
      );

      setRemainingSeconds(
        durationMinutes * 60
      );

      setCurrentQuestionIndex(0);
      setSubmitted(false);
      setResult(null);
    } catch (err) {
      setError(
        err.message ||
          "Unable to start the exam."
      );
    } finally {
      setStarting(false);
    }
  };

  // ============================================================
  // FLATTEN QUESTIONS
  // ============================================================

  const questions = useMemo(() => {
    if (!exam?.sections) {
      return [];
    }

    const flattened = [];

    exam.sections.forEach((section) => {
      (section.questions || []).forEach(
        (question) => {
          flattened.push({
            ...question,
            sectionId: section.id,
            sectionTitle: section.title,
            sectionType:
              section.section_type,
          });
        }
      );
    });

    return flattened;
  }, [exam]);

  // ============================================================
  // CURRENT QUESTION
  // ============================================================

  const currentQuestion =
    questions[currentQuestionIndex] || null;

  // ============================================================
  // SAVE ANSWER
  // ============================================================

  const saveAnswer = async (
    question,
    selectedAnswer = null,
    sourceCode = null,
    language = null
  ) => {
    if (!attemptId || !question) {
      return;
    }

    try {
      setSavingQuestion(question.id);

      const payload = {
        question_id: question.id,
      };

      if (
        question.question_type === "mcq"
      ) {
        payload.selected_answer =
          selectedAnswer;
      }

      if (
        question.question_type === "coding"
      ) {
        payload.source_code =
          sourceCode ?? "";

        payload.language =
          language ||
          question.language ||
          "python";
      }

      await apiRequest(
        `/mixed-exam/attempts/${attemptId}/answers`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        }
      );
    } catch (err) {
      setError(
        err.message ||
          "Failed to save your answer."
      );
    } finally {
      setSavingQuestion(null);
    }
  };

  // ============================================================
  // HANDLE MCQ ANSWER
  // ============================================================

  const handleMcqAnswer = async (
    question,
    answer
  ) => {
    setAnswers((previous) => ({
      ...previous,
      [question.id]: {
        ...(previous[question.id] || {}),
        selectedAnswer: answer,
      },
    }));

    await saveAnswer(
      question,
      answer,
      null,
      null
    );
  };

  // ============================================================
  // HANDLE CODING ANSWER
  // ============================================================

  const handleCodingChange = (
    question,
    sourceCode
  ) => {
    setAnswers((previous) => ({
      ...previous,
      [question.id]: {
        ...(previous[question.id] || {}),
        sourceCode,
      },
    }));
  };

  // ============================================================
  // SAVE CODING ANSWER
  // ============================================================

  const saveCodingAnswer = async (
    question
  ) => {
    const sourceCode =
      answers[question.id]?.sourceCode ??
      question.starter_code ??
      "";

    await saveAnswer(
      question,
      null,
      sourceCode,
      question.language || "python"
    );
  };

  // ============================================================
  // SUBMIT EXAM
  // ============================================================

  const submitExam = async (
    automaticSubmit = false
  ) => {
    if (!attemptId) {
      return;
    }

    if (submitting || submitted) {
      return;
    }

    if (!automaticSubmit) {
      const confirmed = window.confirm(
        "Are you sure you want to submit your exam?\n\nYou will not be able to change your answers after submission."
      );

      if (!confirmed) {
        return;
      }
    }

    try {
      setSubmitting(true);
      setError("");

      const data = await apiRequest(
        `/mixed-exam/attempts/${attemptId}/submit`,
        {
          method: "POST",
        }
      );

      setResult(data || null);
      setSubmitted(true);
      setRemainingSeconds(0);
    } catch (err) {
      setError(
        err.message ||
          "Failed to submit the exam."
      );
    } finally {
      setSubmitting(false);
    }
  };

  // ============================================================
  // TIMER
  // ============================================================

  useEffect(() => {
    if (
      attemptId === null ||
      remainingSeconds === null ||
      submitted
    ) {
      return undefined;
    }

    if (remainingSeconds <= 0) {
      submitExam(true);
      return undefined;
    }

    const timer = window.setTimeout(() => {
      setRemainingSeconds(
        (previous) => {
          if (
            previous === null ||
            previous <= 0
          ) {
            return 0;
          }

          return previous - 1;
        }
      );
    }, 1000);

    return () => {
      window.clearTimeout(timer);
    };
  }, [
    attemptId,
    remainingSeconds,
    submitted,
  ]);

  // ============================================================
  // QUESTION NAVIGATION
  // ============================================================

  const goToQuestion = (index) => {
    if (
      index < 0 ||
      index >= questions.length
    ) {
      return;
    }

    setCurrentQuestionIndex(index);
  };

  // ============================================================
  // LOADING SCREEN
  // ============================================================

  if (loading) {
    return (
      <div className="candidate-page">
        <style>{candidateStyles}</style>

        <div className="center-card">
          <div className="loading-spinner">
            ⏳
          </div>

          <h2>
            Loading assessment...
          </h2>

          <p>
            Please wait while we verify
            your invitation.
          </p>
        </div>
      </div>
    );
  }

  // ============================================================
  // ERROR / INVALID INVITE
  // ============================================================

  if (!exam) {
    return (
      <div className="candidate-page">
        <style>{candidateStyles}</style>

        <div className="center-card error-card">
          <div className="error-icon">
            ⚠️
          </div>

          <h2>
            Unable to Open Assessment
          </h2>

          <p>
            {error ||
              "This invitation is not available."}
          </p>
        </div>
      </div>
    );
  }

  // ============================================================
  // RESULT SCREEN
  // ============================================================

  if (submitted && result) {
    const attemptResult =
      result.attempt || {};

    const score = Number(
      attemptResult.score || 0
    );

    const totalMarks = Number(
      attemptResult.total_marks || 0
    );

    const percentage =
      totalMarks > 0
        ? Math.round(
            (score / totalMarks) * 100
          )
        : 0;

    return (
      <div className="candidate-page">
        <style>{candidateStyles}</style>

        <div className="start-container">
          {/* BRAND */}

          <div className="brand">
            <div className="brand-icon">
              DS
            </div>

            <div>
              <div className="brand-name">
                DevSprint LMS
              </div>

              <div className="brand-subtitle">
                Assessment Result
              </div>
            </div>
          </div>

          {/* RESULT CARD */}

          <div className="result-card">
            <div className="result-icon">
              ✓
            </div>

            <h1>
              Exam Submitted Successfully
            </h1>

            <p className="result-message">
              Thank you,{" "}
              {candidateName}.
              Your assessment has been
              submitted successfully.
            </p>

            {/* SCORE */}

            <div className="result-score">
              <div className="score-label">
                Your Score
              </div>

              <div className="score-number">
                {score}

                <span>
                  / {totalMarks}
                </span>
              </div>

              <div className="percentage">
                {percentage}%
              </div>
            </div>

            {/* CODING PENDING */}

            {Number(
              result.coding_pending || 0
            ) > 0 && (
              <div className="pending-message">
                <strong>
                  Coding questions pending
                  review
                </strong>

                <p>
                  Your coding answers have
                  been submitted and will be
                  reviewed separately.
                </p>
              </div>
            )}

            {/* TIME EXPIRED */}

            {result.time_expired && (
              <div className="time-expired-message">
                Your exam was automatically
                submitted because the time
                limit expired.
              </div>
            )}

            {/* DETAILS */}

            <div className="result-details">
              <div>
                <span>
                  Candidate
                </span>

                <strong>
                  {candidateName}
                </strong>
              </div>

              <div>
                <span>
                  Email
                </span>

                <strong>
                  {candidateEmail}
                </strong>
              </div>

              <div>
                <span>
                  Status
                </span>

                <strong>
                  Submitted
                </strong>
              </div>
            </div>
          </div>

          <div className="footer">
            You can close this window now.
          </div>
        </div>
      </div>
    );
  }

  // ============================================================
  // START SCREEN
  // ============================================================

  if (!attemptId) {
    return (
      <div className="candidate-page">
        <style>{candidateStyles}</style>

        <div className="start-container">
          {/* BRAND */}

          <div className="brand">
            <div className="brand-icon">
              DS
            </div>

            <div>
              <div className="brand-name">
                DevSprint LMS
              </div>

              <div className="brand-subtitle">
                Candidate Assessment
              </div>
            </div>
          </div>

          {/* START CARD */}

          <div className="start-card">
            <div className="exam-icon">
              📝
            </div>

            <h1>
              {exam.title}
            </h1>

            <p className="exam-description">
              {exam.description ||
                "You have been invited to complete this assessment."}
            </p>

            {/* EXAM INFORMATION */}

            <div className="exam-info-grid">
              <div className="exam-info">
                <span>
                  Duration
                </span>

                <strong>
                  {exam.duration_minutes ||
                    60}{" "}
                  minutes
                </strong>
              </div>

              <div className="exam-info">
                <span>
                  Total Marks
                </span>

                <strong>
                  {exam.total_marks ||
                    exam.sections?.reduce(
                      (
                        total,
                        section
                      ) =>
                        total +
                        Number(
                          section.marks ||
                            0
                        ),
                      0
                    ) ||
                    0}
                </strong>
              </div>

              <div className="exam-info">
                <span>
                  Sections
                </span>

                <strong>
                  {exam.sections
                    ?.length || 0}
                </strong>
              </div>
            </div>

            {/* ERROR */}

            {error && (
              <div className="form-error">
                {error}
              </div>
            )}

            {/* FORM */}

            <form
              onSubmit={startExam}
              className="candidate-form"
            >
              <div className="field">
                <label>
                  Your Name
                </label>

                <input
                  value={candidateName}
                  onChange={(event) =>
                    setCandidateName(
                      event.target.value
                    )
                  }
                  placeholder="Enter your full name"
                  autoComplete="name"
                />
              </div>

              <div className="field">
                <label>
                  Email Address
                </label>

                <input
                  type="email"
                  value={candidateEmail}
                  onChange={(event) =>
                    setCandidateEmail(
                      event.target.value
                    )
                  }
                  placeholder="Enter your email"
                  autoComplete="email"
                />
              </div>

              {/* INSTRUCTIONS */}

              <div className="instructions">
                <strong>
                  Before you begin
                </strong>

                <ul>
                  <li>
                    Make sure you have a
                    stable internet
                    connection.
                  </li>

                  <li>
                    Your answers are
                    saved while you work.
                  </li>

                  <li>
                    The timer starts
                    when you click Start
                    Exam.
                  </li>

                  <li>
                    Do not close the
                    browser while taking
                    the assessment.
                  </li>
                </ul>
              </div>

              <button
                type="submit"
                className="start-button"
                disabled={starting}
              >
                {starting
                  ? "Starting Exam..."
                  : "Start Exam →"}
              </button>
            </form>
          </div>

          <div className="footer">
            Powered by DevSprint LMS
          </div>
        </div>
      </div>
    );
  }

  // ============================================================
  // EXAM SCREEN
  // ============================================================

  return (
    <div className="exam-page">
      <style>{candidateStyles}</style>

      {/* ======================================================
          TOP BAR
      ====================================================== */}

      <header className="exam-topbar">
        <div>
          <div className="exam-top-title">
            {exam.title}
          </div>

          <div className="candidate-label">
            {candidateName} •{" "}
            {candidateEmail}
          </div>
        </div>

        <div
          className={`timer ${
            remainingSeconds !== null &&
            remainingSeconds <= 300
              ? "timer-danger"
              : ""
          }`}
        >
          ⏱{" "}
          {formatTime(
            remainingSeconds
          )}
        </div>
      </header>

      {/* ======================================================
          ERROR
      ====================================================== */}

      {error && (
        <div className="exam-error">
          {error}
        </div>
      )}

      {/* ======================================================
          MAIN EXAM AREA
      ====================================================== */}

      <div className="exam-layout">
        {/* ====================================================
            QUESTION SIDEBAR
        ==================================================== */}

        <aside className="question-sidebar">
          <div className="sidebar-title">
            Questions
          </div>

          <div className="sidebar-subtitle">
            {questions.length} total
          </div>

          <div className="question-grid">
            {questions.map(
              (
                question,
                index
              ) => {
                const answered =
                  question.question_type ===
                  "mcq"
                    ? Boolean(
                        answers[
                          question.id
                        ]
                          ?.selectedAnswer
                      )
                    : Boolean(
                        answers[
                          question.id
                        ]?.sourceCode
                      );

                return (
                  <button
                    type="button"
                    key={question.id}
                    className={`question-number-button ${
                      index ===
                      currentQuestionIndex
                        ? "current"
                        : ""
                    } ${
                      answered
                        ? "answered"
                        : ""
                    }`}
                    onClick={() =>
                      goToQuestion(
                        index
                      )
                    }
                  >
                    {index + 1}
                  </button>
                );
              }
            )}
          </div>

          <div className="legend">
            <div>
              <span className="legend-box current-box" />
              Current
            </div>

            <div>
              <span className="legend-box answered-box" />
              Answered
            </div>

            <div>
              <span className="legend-box unanswered-box" />
              Unanswered
            </div>
          </div>
        </aside>

        {/* ====================================================
            QUESTION CONTENT
        ==================================================== */}

        <main className="question-content">
          {currentQuestion ? (
            <div className="question-card">
              {/* QUESTION HEADER */}

              <div className="question-header">
                <div>
                  <div className="section-label">
                    {
                      currentQuestion.sectionTitle
                    }
                  </div>

                  <div className="question-type-label">
                    {
                      currentQuestion.question_type
                    }
                  </div>
                </div>

                <div className="marks-label">
                  {currentQuestion.marks}{" "}
                  marks
                </div>
              </div>

              {/* QUESTION COUNTER */}

              <div className="question-counter">
                Question{" "}
                {currentQuestionIndex +
                  1}{" "}
                of{" "}
                {questions.length}
              </div>

              {/* QUESTION */}

              <h1 className="question-heading">
                {
                  currentQuestion.question_text
                }
              </h1>

              {/* =================================================
                  MCQ
              ================================================= */}

              {currentQuestion.question_type ===
                "mcq" && (
                <div className="options">
                  {[
                    [
                      "A",
                      currentQuestion.option_a,
                    ],
                    [
                      "B",
                      currentQuestion.option_b,
                    ],
                    [
                      "C",
                      currentQuestion.option_c,
                    ],
                    [
                      "D",
                      currentQuestion.option_d,
                    ],
                  ].map(
                    ([letter, text]) => {
                      if (!text) {
                        return null;
                      }

                      const selected =
                        answers[
                          currentQuestion.id
                        ]
                          ?.selectedAnswer ===
                        letter;

                      return (
                        <button
                          type="button"
                          key={letter}
                          className={`option ${
                            selected
                              ? "option-selected"
                              : ""
                          }`}
                          onClick={() =>
                            handleMcqAnswer(
                              currentQuestion,
                              letter
                            )
                          }
                        >
                          <span
                            className={`option-letter ${
                              selected
                                ? "option-letter-selected"
                                : ""
                            }`}
                          >
                            {letter}
                          </span>

                          <span className="option-text">
                            {text}
                          </span>

                          {selected && (
                            <span className="selected-check">
                              ✓
                            </span>
                          )}
                        </button>
                      );
                    }
                  )}
                </div>
              )}

              {/* =================================================
                  CODING
              ================================================= */}

              {currentQuestion.question_type ===
                "coding" && (
                <div className="coding-area">
                  {currentQuestion.coding_description && (
                    <div className="coding-description">
                      {
                        currentQuestion.coding_description
                      }
                    </div>
                  )}

                  <div className="language-row">
                    <span>
                      Language
                    </span>

                    <strong>
                      {currentQuestion.language ||
                        "python"}
                    </strong>
                  </div>

                  <textarea
                    className="code-editor"
                    value={
                      answers[
                        currentQuestion.id
                      ]?.sourceCode ??
                      currentQuestion.starter_code ??
                      ""
                    }
                    onChange={(event) =>
                      handleCodingChange(
                        currentQuestion,
                        event.target.value
                      )
                    }
                    spellCheck="false"
                  />

                  <button
                    type="button"
                    className="save-code-button"
                    onClick={() =>
                      saveCodingAnswer(
                        currentQuestion
                      )
                    }
                    disabled={
                      savingQuestion ===
                      currentQuestion.id
                    }
                  >
                    {savingQuestion ===
                    currentQuestion.id
                      ? "Saving..."
                      : "Save Code"}
                  </button>

                  <div className="coding-note">
                    Your code is saved as
                    your answer. Coding
                    execution and automatic
                    scoring will be added in
                    the next stage.
                  </div>
                </div>
              )}

              {/* =================================================
                  QUESTION ACTIONS
              ================================================= */}

              <div className="question-actions">
                <button
                  type="button"
                  className="previous-button"
                  onClick={() =>
                    goToQuestion(
                      currentQuestionIndex -
                        1
                    )
                  }
                  disabled={
                    currentQuestionIndex ===
                    0
                  }
                >
                  ← Previous
                </button>

                <div className="save-status">
                  {savingQuestion ===
                    currentQuestion.id && (
                    <span>
                      Saving...
                    </span>
                  )}

                  {answers[
                    currentQuestion.id
                  ] && (
                    <span className="saved">
                      ✓ Answer saved
                    </span>
                  )}
                </div>

                {/* NEXT */}

                {currentQuestionIndex <
                  questions.length - 1 && (
                  <button
                    type="button"
                    className="next-button"
                    onClick={() =>
                      goToQuestion(
                        currentQuestionIndex +
                          1
                      )
                    }
                  >
                    Next →
                  </button>
                )}

                {/* SUBMIT */}

                {currentQuestionIndex ===
                  questions.length - 1 && (
                  <button
                    type="button"
                    className="submit-exam-button"
                    onClick={() =>
                      submitExam(false)
                    }
                    disabled={submitting}
                  >
                    {submitting
                      ? "Submitting..."
                      : "Submit Exam"}
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="center-card">
              <h2>
                No questions found
              </h2>

              <p>
                This assessment does not
                have any questions yet.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

// ============================================================
// STYLES
// ============================================================

const candidateStyles = `
  * {
    box-sizing: border-box;
  }

  body {
    margin: 0;
  }

  .candidate-page {
    min-height: 100vh;
    background: #f5f7fb;
    color: #172033;
    font-family:
      Inter,
      -apple-system,
      BlinkMacSystemFont,
      "Segoe UI",
      sans-serif;
  }

  /* ==========================================================
     START PAGE
  ========================================================== */

  .start-container {
    width: min(760px, 100%);
    margin: 0 auto;
    padding: 45px 20px;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 25px;
  }

  .brand-icon {
    width: 44px;
    height: 44px;
    border-radius: 11px;
    background: #2563eb;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
  }

  .brand-name {
    font-weight: 700;
    font-size: 16px;
  }

  .brand-subtitle {
    color: #667085;
    font-size: 12px;
    margin-top: 2px;
  }

  .start-card {
    background: white;
    border: 1px solid #eaecf0;
    border-radius: 18px;
    padding: 35px;
    box-shadow:
      0 10px 30px
      rgba(16, 24, 40, 0.06);
  }

  .exam-icon {
    width: 58px;
    height: 58px;
    border-radius: 15px;
    background: #eef4ff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 27px;
    margin-bottom: 18px;
  }

  .start-card h1 {
    margin: 0;
    font-size: 29px;
  }

  .exam-description {
    color: #667085;
    line-height: 1.6;
    margin: 10px 0 25px;
  }

  .exam-info-grid {
    display: grid;
    grid-template-columns:
      repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 28px;
  }

  .exam-info {
    padding: 15px;
    border: 1px solid #eaecf0;
    border-radius: 11px;
    background: #f9fafb;
  }

  .exam-info span {
    display: block;
    color: #667085;
    font-size: 12px;
    margin-bottom: 5px;
  }

  .exam-info strong {
    font-size: 16px;
  }

  .candidate-form {
    border-top: 1px solid #eaecf0;
    padding-top: 25px;
  }

  .field {
    margin-bottom: 17px;
  }

  .field label {
    display: block;
    color: #344054;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 7px;
  }

  .field input {
    width: 100%;
    padding: 12px 13px;
    border: 1px solid #d0d5dd;
    border-radius: 9px;
    font-size: 14px;
    outline: none;
  }

  .field input:focus {
    border-color: #2563eb;
  }

  .instructions {
    padding: 15px;
    border-radius: 10px;
    background: #f8fafc;
    color: #475467;
    font-size: 13px;
    line-height: 1.5;
    margin: 20px 0;
  }

  .instructions strong {
    color: #172033;
  }

  .instructions ul {
    margin: 8px 0 0;
    padding-left: 20px;
  }

  .start-button {
    width: 100%;
    border: none;
    border-radius: 10px;
    padding: 13px 18px;
    background: #2563eb;
    color: white;
    font-weight: 700;
    font-size: 14px;
    cursor: pointer;
  }

  .start-button:hover {
    background: #1d4ed8;
  }

  .start-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .form-error {
    padding: 11px 13px;
    margin-bottom: 15px;
    border-radius: 9px;
    background: #fef3f2;
    border: 1px solid #fecdca;
    color: #b42318;
    font-size: 13px;
  }

  .center-card {
    width: min(
      600px,
      calc(100% - 40px)
    );
    margin: 100px auto;
    padding: 35px;
    background: white;
    border: 1px solid #eaecf0;
    border-radius: 16px;
    text-align: center;
  }

  .center-card h2 {
    margin: 10px 0;
  }

  .center-card p {
    color: #667085;
    line-height: 1.5;
  }

  .loading-spinner {
    font-size: 35px;
  }

  .error-icon {
    font-size: 40px;
  }

  .footer {
    text-align: center;
    color: #98a2b3;
    font-size: 12px;
    margin-top: 20px;
  }

  /* ==========================================================
     RESULT
  ========================================================== */

  .result-card {
    background: white;
    border: 1px solid #eaecf0;
    border-radius: 18px;
    padding: 35px;
    text-align: center;
    box-shadow:
      0 10px 30px
      rgba(16, 24, 40, 0.06);
  }

  .result-icon {
    width: 65px;
    height: 65px;
    margin: 0 auto 18px;
    border-radius: 50%;
    background: #ecfdf3;
    color: #027a48;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    font-weight: 800;
  }

  .result-card h1 {
    margin: 0;
    font-size: 26px;
  }

  .result-message {
    color: #667085;
    line-height: 1.5;
    margin: 10px 0 25px;
  }

  .result-score {
    padding: 25px;
    border-radius: 14px;
    background: #f8fafc;
    border: 1px solid #eaecf0;
    margin-bottom: 20px;
  }

  .score-label {
    color: #667085;
    font-size: 13px;
  }

  .score-number {
    margin-top: 7px;
    font-size: 42px;
    font-weight: 800;
    color: #172033;
  }

  .score-number span {
    font-size: 20px;
    color: #667085;
    font-weight: 500;
  }

  .percentage {
    margin-top: 5px;
    color: #2563eb;
    font-weight: 700;
  }

  .pending-message {
    padding: 14px;
    margin-bottom: 15px;
    border-radius: 10px;
    background: #fffaeb;
    border: 1px solid #fedf89;
    color: #93370d;
    text-align: left;
    font-size: 13px;
  }

  .pending-message p {
    margin: 5px 0 0;
  }

  .time-expired-message {
    padding: 13px;
    margin-bottom: 15px;
    border-radius: 10px;
    background: #fef3f2;
    border: 1px solid #fecdca;
    color: #b42318;
    font-size: 13px;
  }

  .result-details {
    display: grid;
    gap: 1px;
    background: #eaecf0;
    border: 1px solid #eaecf0;
    border-radius: 10px;
    overflow: hidden;
    text-align: left;
  }

  .result-details > div {
    background: white;
    padding: 13px 15px;
    display: flex;
    justify-content: space-between;
    gap: 15px;
  }

  .result-details span {
    color: #667085;
    font-size: 12px;
  }

  .result-details strong {
    color: #344054;
    font-size: 13px;
  }

  /* ==========================================================
     EXAM
  ========================================================== */

  .exam-page {
    min-height: 100vh;
    background: #f5f7fb;
    color: #172033;
    font-family:
      Inter,
      -apple-system,
      BlinkMacSystemFont,
      "Segoe UI",
      sans-serif;
  }

  .exam-topbar {
    min-height: 72px;
    padding: 12px 25px;
    background: white;
    border-bottom: 1px solid #eaecf0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    position: sticky;
    top: 0;
    z-index: 20;
  }

  .exam-top-title {
    font-weight: 700;
    font-size: 17px;
  }

  .candidate-label {
    color: #667085;
    font-size: 12px;
    margin-top: 4px;
  }

  .timer {
    min-width: 110px;
    text-align: center;
    padding: 11px 15px;
    border-radius: 10px;
    background: #eef4ff;
    color: #1d4ed8;
    font-weight: 800;
    font-size: 17px;
  }

  .timer-danger {
    background: #fef3f2;
    color: #b42318;
  }

  .exam-error {
    margin: 15px auto;
    width: min(
      1200px,
      calc(100% - 30px)
    );
    padding: 11px 14px;
    border-radius: 9px;
    background: #fef3f2;
    border: 1px solid #fecdca;
    color: #b42318;
    font-size: 13px;
  }

  .exam-layout {
    width: min(1250px, 100%);
    margin: 0 auto;
    padding: 25px;
    display: grid;
    grid-template-columns:
      230px minmax(0, 1fr);
    gap: 20px;
  }

  .question-sidebar {
    background: white;
    border: 1px solid #eaecf0;
    border-radius: 14px;
    padding: 18px;
    height: fit-content;
    position: sticky;
    top: 97px;
  }

  .sidebar-title {
    font-weight: 700;
    font-size: 15px;
  }

  .sidebar-subtitle {
    color: #667085;
    font-size: 12px;
    margin-top: 3px;
    margin-bottom: 15px;
  }

  .question-grid {
    display: grid;
    grid-template-columns:
      repeat(5, 1fr);
    gap: 7px;
  }

  .question-number-button {
    height: 35px;
    border: 1px solid #d0d5dd;
    border-radius: 8px;
    background: white;
    color: #475467;
    font-weight: 600;
    cursor: pointer;
  }

  .question-number-button:hover {
    border-color: #2563eb;
  }

  .question-number-button.current {
    border-color: #2563eb;
    background: #2563eb;
    color: white;
  }

  .question-number-button.answered {
    border-color: #12b76a;
    background: #ecfdf3;
    color: #027a48;
  }

  .question-number-button.current.answered {
    background: #2563eb;
    color: white;
    border-color: #2563eb;
  }

  .legend {
    margin-top: 18px;
    display: grid;
    gap: 8px;
    color: #667085;
    font-size: 11px;
  }

  .legend > div {
    display: flex;
    align-items: center;
    gap: 7px;
  }

  .legend-box {
    width: 12px;
    height: 12px;
    border-radius: 3px;
    border: 1px solid #d0d5dd;
  }

  .current-box {
    background: #2563eb;
    border-color: #2563eb;
  }

  .answered-box {
    background: #ecfdf3;
    border-color: #12b76a;
  }

  .unanswered-box {
    background: white;
  }

  .question-content {
    min-width: 0;
  }

  .question-card {
    background: white;
    border: 1px solid #eaecf0;
    border-radius: 16px;
    padding: 28px;
  }

  .question-header {
    display: flex;
    justify-content: space-between;
    gap: 15px;
    padding-bottom: 18px;
    border-bottom: 1px solid #eaecf0;
  }

  .section-label {
    color: #344054;
    font-size: 13px;
    font-weight: 700;
  }

  .question-type-label {
    display: inline-block;
    margin-top: 7px;
    padding: 4px 8px;
    border-radius: 999px;
    background: #eef4ff;
    color: #3538cd;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
  }

  .marks-label {
    color: #667085;
    font-size: 13px;
    white-space: nowrap;
  }

  .question-counter {
    color: #667085;
    font-size: 12px;
    margin-top: 22px;
  }

  .question-heading {
    font-size: 21px;
    line-height: 1.5;
    margin: 10px 0 25px;
  }

  /* ==========================================================
     MCQ
  ========================================================== */

  .options {
    display: grid;
    gap: 11px;
  }

  .option {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 13px;
    padding: 14px;
    border: 1px solid #d0d5dd;
    border-radius: 11px;
    background: white;
    text-align: left;
    cursor: pointer;
  }

  .option:hover {
    border-color: #2563eb;
    background: #f8fbff;
  }

  .option-selected {
    border-color: #2563eb;
    background: #eff6ff;
  }

  .option-letter {
    width: 32px;
    height: 32px;
    flex-shrink: 0;
    border-radius: 50%;
    background: #f2f4f7;
    color: #475467;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 12px;
  }

  .option-letter-selected {
    background: #2563eb;
    color: white;
  }

  .option-text {
    flex: 1;
    color: #344054;
    font-size: 14px;
  }

  .selected-check {
    color: #2563eb;
    font-weight: 800;
  }

  /* ==========================================================
     CODING
  ========================================================== */

  .coding-area {
    margin-top: 10px;
  }

  .coding-description {
    padding: 14px;
    border-radius: 9px;
    background: #f8fafc;
    color: #475467;
    font-size: 13px;
    line-height: 1.6;
    margin-bottom: 14px;
    white-space: pre-wrap;
  }

  .language-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    color: #667085;
    font-size: 12px;
  }

  .language-row strong {
    color: #344054;
    text-transform: capitalize;
  }

  .code-editor {
    width: 100%;
    min-height: 330px;
    resize: vertical;
    border: 1px solid #1d2939;
    border-radius: 10px;
    padding: 16px;
    background: #101828;
    color: #f8fafc;
    font-family:
      "SFMono-Regular",
      Consolas,
      monospace;
    font-size: 13px;
    line-height: 1.6;
    outline: none;
  }

  .save-code-button {
    margin-top: 12px;
    border: none;
    border-radius: 9px;
    padding: 10px 15px;
    background: #2563eb;
    color: white;
    font-weight: 600;
    cursor: pointer;
  }

  .save-code-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .coding-note {
    margin-top: 10px;
    padding: 10px 12px;
    background: #fffaeb;
    border: 1px solid #fedf89;
    color: #93370d;
    border-radius: 8px;
    font-size: 12px;
    line-height: 1.5;
  }

  /* ==========================================================
     QUESTION ACTIONS
  ========================================================== */

  .question-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-top: 30px;
    padding-top: 20px;
    border-top: 1px solid #eaecf0;
  }

  .previous-button,
  .next-button,
  .submit-exam-button {
    border-radius: 9px;
    padding: 10px 16px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }

  .previous-button {
    border: 1px solid #d0d5dd;
    background: white;
    color: #344054;
  }

  .next-button {
    border: none;
    background: #2563eb;
    color: white;
  }

  .submit-exam-button {
    border: none;
    background: #dc2626;
    color: white;
    font-weight: 700;
  }

  .submit-exam-button:hover {
    background: #b91c1c;
  }

  .submit-exam-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .previous-button:disabled,
  .next-button:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .save-status {
    flex: 1;
    text-align: center;
    color: #667085;
    font-size: 12px;
  }

  .saved {
    color: #027a48;
    font-weight: 600;
  }

  /* ==========================================================
     TABLET
  ========================================================== */

  @media (max-width: 800px) {
    .exam-layout {
      grid-template-columns: 1fr;
      padding: 15px;
    }

    .question-sidebar {
      position: static;
    }

    .question-grid {
      grid-template-columns:
        repeat(10, 1fr);
    }

    .exam-topbar {
      padding: 12px 15px;
    }
  }

  /* ==========================================================
     MOBILE
  ========================================================== */

  @media (max-width: 600px) {
    .start-container {
      padding: 25px 15px;
    }

    .start-card,
    .result-card {
      padding: 22px;
    }

    .exam-info-grid {
      grid-template-columns: 1fr;
    }

    .question-card {
      padding: 20px;
    }

    .question-heading {
      font-size: 18px;
    }

    .question-actions {
      flex-wrap: wrap;
    }

    .save-status {
      order: 3;
      flex-basis: 100%;
    }

    .submit-exam-button,
    .next-button,
    .previous-button {
      flex: 1;
    }

    .result-card h1 {
      font-size: 22px;
    }

    .result-details > div {
      flex-direction: column;
      gap: 4px;
    }
  }
`;