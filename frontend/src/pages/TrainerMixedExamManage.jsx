import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { apiRequest } from "../services/api";
import DashboardLayout from "../components/DashboardLayout";

export default function TrainerMixedExamManage() {
  const { examId } = useParams();
  const navigate = useNavigate();

  const [exam, setExam] = useState(null);

  const [banks, setBanks] = useState([]);
  const [selectedBank, setSelectedBank] = useState(null);
  const [bankQuestions, setBankQuestions] = useState([]);

  const [loading, setLoading] = useState(true);
  const [questionsLoading, setQuestionsLoading] = useState(false);
  const [error, setError] = useState("");

  // ============================================================
  // SECTION / QUESTION MODALS
  // ============================================================

  const [showSectionModal, setShowSectionModal] = useState(false);
  const [showQuestionModal, setShowQuestionModal] = useState(false);

  const [sectionTitle, setSectionTitle] = useState("");
  const [sectionType, setSectionType] = useState("mcq");

  const [selectedSection, setSelectedSection] = useState(null);

  // ============================================================
  // STATUS
  // ============================================================

  const [statusUpdating, setStatusUpdating] = useState(false);

  // ============================================================
  // INVITE CANDIDATE
  // ============================================================

  const [showInviteModal, setShowInviteModal] = useState(false);

  const [candidateName, setCandidateName] = useState("");
  const [candidateEmail, setCandidateEmail] = useState("");
  const [inviteExpiryDays, setInviteExpiryDays] = useState("7");
  const [maxAttempts, setMaxAttempts] = useState("1");

  const [inviteLoading, setInviteLoading] = useState(false);
  const [generatedInvite, setGeneratedInvite] = useState(null);

  // ============================================================
  // LOAD EXAM
  // ============================================================

  const loadExam = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await apiRequest(
        `/trainer/mixed-exams/${examId}`
      );

      setExam(data?.exam || null);
    } catch (err) {
      setError(
        err.message || "Failed to load exam."
      );
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // LOAD QUESTION BANKS
  // ============================================================

  const loadBanks = async () => {
    try {
      const data = await apiRequest(
        "/trainer/question-banks"
      );

      setBanks(data?.banks || []);
    } catch (err) {
      setError(
        err.message || "Failed to load question banks."
      );
    }
  };

  // ============================================================
  // LOAD QUESTIONS FROM QUESTION BANK
  // ============================================================

  const loadBankQuestions = async (bankId) => {
    try {
      setQuestionsLoading(true);
      setError("");

      const data = await apiRequest(
        `/trainer/question-banks/${bankId}`
      );

      setSelectedBank(data?.bank || null);

      setBankQuestions(
        data?.bank?.questions || []
      );
    } catch (err) {
      setError(
        err.message || "Failed to load questions."
      );
    } finally {
      setQuestionsLoading(false);
    }
  };

  // ============================================================
  // INITIAL LOAD
  // ============================================================

  useEffect(() => {
    loadExam();
    loadBanks();
  }, [examId]);

  // ============================================================
  // UPDATE EXAM STATUS
  // ============================================================

  const updateExamStatus = async (newStatus) => {
    let actionText = "";

    if (newStatus === "published") {
      actionText = "publish";
    } else if (newStatus === "closed") {
      actionText = "close";
    } else {
      actionText = "move this exam back to draft";
    }

    const confirmed = window.confirm(
      `Are you sure you want to ${actionText} this exam?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setStatusUpdating(true);
      setError("");

      await apiRequest(
        `/trainer/mixed-exams/${examId}/status`,
        {
          method: "PUT",
          body: JSON.stringify({
            status: newStatus,
          }),
        }
      );

      await loadExam();

      if (newStatus === "published") {
        alert("Exam published successfully.");
      } else if (newStatus === "closed") {
        alert("Exam closed successfully.");
      } else {
        alert("Exam moved back to draft.");
      }
    } catch (err) {
      setError(
        err.message ||
        "Failed to update exam status."
      );
    } finally {
      setStatusUpdating(false);
    }
  };

  // ============================================================
  // OPEN INVITE MODAL
  // ============================================================

  const openInviteModal = () => {
    setGeneratedInvite(null);

    setCandidateName("");
    setCandidateEmail("");
    setInviteExpiryDays("7");
    setMaxAttempts("1");

    setError("");
    setShowInviteModal(true);
  };

  // ============================================================
  // CLOSE INVITE MODAL
  // ============================================================

  const closeInviteModal = () => {
    if (inviteLoading) {
      return;
    }

    setShowInviteModal(false);
    setGeneratedInvite(null);

    setCandidateName("");
    setCandidateEmail("");
    setInviteExpiryDays("7");
    setMaxAttempts("1");
  };

  // ============================================================
  // CREATE CANDIDATE INVITE
  // ============================================================

  const createCandidateInvite = async (event) => {
    event.preventDefault();

    if (!candidateName.trim()) {
      alert("Please enter the candidate name.");
      return;
    }

    if (!candidateEmail.trim()) {
      alert("Please enter the candidate email.");
      return;
    }

    try {
      setInviteLoading(true);
      setError("");

      const expiryDate = new Date(
        Date.now() +
        Number(inviteExpiryDays) *
        24 *
        60 *
        60 *
        1000
      );

      const data = await apiRequest(
        `/trainer/mixed-exams/${examId}/invites`,
        {
          method: "POST",
          body: JSON.stringify({
            candidate_name: candidateName.trim(),
            candidate_email: candidateEmail.trim(),
            expires_at: expiryDate.toISOString(),
            max_attempts: Number(maxAttempts),
          }),
        }
      );

      const inviteCode =
        data?.invite?.invite_code ||
        data?.invite_code ||
        data?.code;

      if (!inviteCode) {
        throw new Error(
          "Invite was created, but no invite code was returned by the server."
        );
      }

      const inviteLink =
        `${window.location.origin}/mixed-exam/invite/${inviteCode}`;

      setGeneratedInvite({
        code: inviteCode,
        link: inviteLink,
        candidateName: candidateName.trim(),
        candidateEmail: candidateEmail.trim(),
      });

    } catch (err) {
      setError(
        err.message ||
        "Failed to create candidate invite."
      );
    } finally {
      setInviteLoading(false);
    }
  };

  // ============================================================
  // COPY INVITE LINK
  // ============================================================

  const copyInviteLink = async () => {
    if (!generatedInvite?.link) {
      return;
    }

    try {
      await navigator.clipboard.writeText(
        generatedInvite.link
      );

      alert("Invite link copied to clipboard.");
    } catch (err) {
      alert(
        "Unable to copy the link. Please copy it manually."
      );
    }
  };

  // ============================================================
  // CREATE SECTION
  // ============================================================

  const createSection = async (event) => {
    event.preventDefault();

    if (!sectionTitle.trim()) {
      alert("Please enter a section title.");
      return;
    }

    try {
      await apiRequest(
        `/trainer/mixed-exams/${examId}/sections`,
        {
          method: "POST",
          body: JSON.stringify({
            title: sectionTitle.trim(),
            section_type: sectionType,
            order_index:
              (exam?.sections?.length || 0) + 1,
          }),
        }
      );

      setSectionTitle("");
      setSectionType("mcq");
      setShowSectionModal(false);

      await loadExam();

      alert("Section created successfully.");
    } catch (err) {
      alert(
        err.message ||
        "Failed to create section."
      );
    }
  };

  // ============================================================
  // ADD QUESTION TO SECTION
  // ============================================================

  const addQuestionToSection = async (question) => {
    if (!selectedSection) {
      alert("Please select a section.");
      return;
    }

    if (
      question.question_type !==
      selectedSection.section_type
    ) {
      alert(
        `This section accepts ${selectedSection.section_type.toUpperCase()} questions only.`
      );
      return;
    }

    try {
      await apiRequest(
        `/trainer/mixed-exam-sections/${selectedSection.id}/questions`,
        {
          method: "POST",
          body: JSON.stringify({
            question_bank_item_id: question.id,
            order_index:
              (selectedSection.questions?.length || 0) + 1,
          }),
        }
      );

      setShowQuestionModal(false);
      setSelectedBank(null);
      setBankQuestions([]);

      await loadExam();

      alert("Question added to exam.");
    } catch (err) {
      alert(
        err.message ||
        "Failed to add question to exam."
      );
    }
  };

  // ============================================================
  // GET SECTION QUESTIONS
  // ============================================================

  const getSectionQuestions = (section) => {
    return section.questions || [];
  };

  // ============================================================
  // OPEN QUESTION SELECTOR
  // ============================================================

  const openQuestionSelector = (section) => {
    setSelectedSection(section);
    setSelectedBank(null);
    setBankQuestions([]);
    setShowQuestionModal(true);
  };

  // ============================================================
  // CALCULATE TOTAL MARKS
  // ============================================================

  const calculateTotalMarks = () => {
    if (!exam?.sections) {
      return exam?.total_marks || 0;
    }

    return exam.sections.reduce(
      (total, section) =>
        total + Number(section.marks || 0),
      0
    );
  };

  // ============================================================
  // LOADING
  // ============================================================

  if (loading) {
    return (
      <DashboardLayout role="trainer">

        <div className="page">

          <div className="empty">
            Loading exam...
          </div>

        </div>

      </DashboardLayout>
    );
  }

  // ============================================================
  // EXAM NOT FOUND
  // ============================================================

  if (!exam) {
    return (
      <DashboardLayout role="trainer">

        <div className="page">

          <div className="error">
            {error || "Exam not found."}
          </div>

          <button
            className="secondary-button"
            onClick={() =>
              navigate("/trainer/mixed-exams")
            }
          >
            ← Back to Mixed Exams
          </button>

        </div>

      </DashboardLayout>
    );
  }

  // ============================================================
  // MAIN PAGE
  // ============================================================

  return (
    <DashboardLayout role="trainer">

      <div className="page">

        <style>{`

          * {
            box-sizing: border-box;
          }

          .page {
            min-height: 100%;
            padding: 28px;
            background: #f7f8fc;
          }

          .back-button {
            border: none;
            background: transparent;
            color: #475467;
            font-weight: 600;
            cursor: pointer;
            padding: 0;
            margin-bottom: 18px;
          }

          .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 20px;
            margin-bottom: 24px;
          }

          .title {
            margin: 0;
            color: #172033;
            font-size: 28px;
            font-weight: 700;
          }

          .description {
            margin: 7px 0 0;
            color: #667085;
            font-size: 14px;
          }

          .header-actions {
            display: flex;
            gap: 10px;
            align-items: center;
            justify-content: flex-end;
            flex-wrap: wrap;
          }

          .primary-button {
            border: none;
            border-radius: 10px;
            padding: 11px 18px;
            background: #2563eb;
            color: white;
            font-weight: 600;
            cursor: pointer;
          }

          .primary-button:hover {
            background: #1d4ed8;
          }

          .primary-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
          }

          .secondary-button {
            border: 1px solid #d0d5dd;
            border-radius: 10px;
            padding: 10px 16px;
            background: white;
            color: #344054;
            font-weight: 600;
            cursor: pointer;
          }

          .secondary-button:hover {
            background: #f9fafb;
          }

          .secondary-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
          }

          .error {
            padding: 12px 14px;
            margin-bottom: 18px;
            border-radius: 10px;
            background: #fef3f2;
            border: 1px solid #fecdca;
            color: #b42318;
          }

          .summary {
            display: grid;
            grid-template-columns:
              repeat(4, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 24px;
          }

          .summary-card {
            background: white;
            border: 1px solid #eaecf0;
            border-radius: 13px;
            padding: 17px;
          }

          .summary-label {
            color: #667085;
            font-size: 12px;
            margin-bottom: 6px;
          }

          .summary-value {
            color: #172033;
            font-size: 20px;
            font-weight: 700;
          }

          .status-value {
            text-transform: capitalize;
          }

          .status-badge {
            display: inline-flex;
            align-items: center;
            margin-top: 8px;
            padding: 5px 10px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
          }

          .status-draft {
            background: #f2f4f7;
            color: #475467;
          }

          .status-published {
            background: #ecfdf3;
            color: #027a48;
          }

          .status-closed {
            background: #fef3f2;
            color: #b42318;
          }

          .section-list {
            display: grid;
            gap: 18px;
          }

          .section-card {
            background: white;
            border: 1px solid #eaecf0;
            border-radius: 15px;
            overflow: hidden;
          }

          .section-header {
            padding: 18px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 15px;
            border-bottom: 1px solid #eaecf0;
          }

          .section-title {
            margin: 0;
            color: #172033;
            font-size: 17px;
            font-weight: 700;
          }

          .section-type {
            display: inline-flex;
            margin-top: 6px;
            padding: 4px 8px;
            border-radius: 999px;
            background: #eef4ff;
            color: #3538cd;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
          }

          .section-body {
            padding: 20px;
          }

          .question-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 15px;
            padding: 13px 0;
            border-bottom: 1px solid #f2f4f7;
          }

          .question-row:last-child {
            border-bottom: none;
          }

          .question-number {
            min-width: 30px;
            color: #667085;
            font-size: 13px;
            font-weight: 700;
          }

          .question-text {
            flex: 1;
            color: #344054;
            font-size: 14px;
            line-height: 1.45;
          }

          .question-marks {
            color: #667085;
            font-size: 12px;
            white-space: nowrap;
          }

          .add-question-button {
            width: 100%;
            margin-top: 15px;
            border: 1px dashed #98a2b3;
            border-radius: 9px;
            padding: 11px;
            background: #f9fafb;
            color: #344054;
            font-weight: 600;
            cursor: pointer;
          }

          .add-question-button:hover {
            background: #f2f4f7;
          }

          .add-question-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }

          .empty-section {
            padding: 15px 0;
            color: #667085;
            font-size: 14px;
          }

          .empty {
            padding: 60px 20px;
            background: white;
            border: 1px solid #eaecf0;
            border-radius: 15px;
            text-align: center;
            color: #667085;
          }

          .modal-overlay {
            position: fixed;
            inset: 0;
            z-index: 1000;
            background: rgba(16, 24, 40, 0.55);
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
          }

          .modal {
            width: min(720px, 100%);
            max-height: 90vh;
            overflow-y: auto;
            background: white;
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 20px 50px rgba(16, 24, 40, 0.2);
          }

          .modal-title {
            margin: 0 0 20px;
            color: #172033;
            font-size: 21px;
          }

          .modal-subtitle {
            margin-top: -10px;
            margin-bottom: 20px;
            color: #667085;
            font-size: 13px;
            line-height: 1.5;
          }

          .form-group {
            margin-bottom: 17px;
          }

          .form-label {
            display: block;
            margin-bottom: 7px;
            color: #344054;
            font-size: 13px;
            font-weight: 600;
          }

          .input,
          .textarea,
          .select {
            width: 100%;
            padding: 11px 12px;
            border: 1px solid #d0d5dd;
            border-radius: 9px;
            background: white;
            font-size: 14px;
            outline: none;
          }

          .input:focus,
          .textarea:focus,
          .select:focus {
            border-color: #2563eb;
          }

          .modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            margin-top: 22px;
          }

          .bank-selector {
            display: grid;
            grid-template-columns:
              repeat(2, minmax(0, 1fr));
            gap: 12px;
          }

          .bank-button {
            text-align: left;
            padding: 14px;
            border: 1px solid #d0d5dd;
            border-radius: 10px;
            background: white;
            cursor: pointer;
          }

          .bank-button:hover {
            border-color: #2563eb;
            background: #eff6ff;
          }

          .bank-button.selected {
            border-color: #2563eb;
            background: #eff6ff;
          }

          .bank-name {
            color: #172033;
            font-weight: 700;
          }

          .bank-description {
            margin-top: 5px;
            color: #667085;
            font-size: 12px;
          }

          .available-question {
            display: flex;
            justify-content: space-between;
            gap: 15px;
            align-items: center;
            padding: 14px 0;
            border-bottom: 1px solid #eaecf0;
          }

          .available-question:last-child {
            border-bottom: none;
          }

          .available-question-text {
            color: #344054;
            font-size: 14px;
            line-height: 1.45;
          }

          .small-button {
            flex-shrink: 0;
            border: none;
            border-radius: 8px;
            padding: 8px 12px;
            background: #2563eb;
            color: white;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
          }

          .small-button:hover {
            background: #1d4ed8;
          }

          /* =====================================================
             INVITE SUCCESS
          ===================================================== */

          .invite-success {
            margin-top: 10px;
            padding: 18px;
            border: 1px solid #abefc6;
            border-radius: 12px;
            background: #ecfdf3;
          }

          .invite-success-title {
            color: #027a48;
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 15px;
          }

          .invite-info {
            margin-bottom: 14px;
            color: #344054;
            font-size: 13px;
          }

          .invite-link-box {
            display: flex;
            gap: 8px;
            margin-top: 8px;
          }

          .invite-link-input {
            flex: 1;
            min-width: 0;
            padding: 10px 12px;
            border: 1px solid #d0d5dd;
            border-radius: 8px;
            background: white;
            color: #344054;
            font-size: 13px;
          }

          .copy-button {
            border: none;
            border-radius: 8px;
            padding: 10px 14px;
            background: #027a48;
            color: white;
            font-weight: 600;
            cursor: pointer;
          }

          .copy-button:hover {
            background: #05603a;
          }

          .invite-note {
            margin-top: 14px;
            padding: 10px 12px;
            border-radius: 8px;
            background: #f8fafc;
            color: #667085;
            font-size: 12px;
            line-height: 1.5;
          }

          @media (max-width: 900px) {

            .summary {
              grid-template-columns:
                repeat(2, 1fr);
            }

            .header {
              flex-direction: column;
            }

            .header-actions {
              width: 100%;
              justify-content: flex-start;
            }

          }

          @media (max-width: 600px) {

            .page {
              padding: 18px;
            }

            .summary {
              grid-template-columns: 1fr;
            }

            .section-header {
              flex-direction: column;
              align-items: flex-start;
            }

            .bank-selector {
              grid-template-columns: 1fr;
            }

            .available-question {
              flex-direction: column;
              align-items: flex-start;
            }

            .header-actions {
              width: 100%;
              flex-direction: column;
              align-items: stretch;
            }

            .header-actions button {
              width: 100%;
            }

            .invite-link-box {
              flex-direction: column;
            }

            .copy-button {
              width: 100%;
            }

          }

        `}</style>

        {/* =====================================================
            BACK
        ===================================================== */}

        <button
          className="back-button"
          onClick={() =>
            navigate("/trainer/mixed-exams")
          }
        >
          ← Back to Mixed Exams
        </button>

        {/* =====================================================
            HEADER
        ===================================================== */}

        <div className="header">

          <div>

            <h1 className="title">
              {exam.title}
            </h1>

            <p className="description">
              {exam.description ||
                "Manage sections and questions for this exam."}
            </p>

          </div>

          <div className="header-actions">

            {/* ADD SECTION */}

            <button
              className="secondary-button"
              onClick={() =>
                setShowSectionModal(true)
              }
              disabled={
                statusUpdating ||
                exam.status === "closed"
              }
            >
              + Add Section
            </button>

            {/* INVITE CANDIDATE */}

            {exam.status === "published" && (
              <button
                className="primary-button"
                onClick={openInviteModal}
              >
                👤 Invite Candidate
              </button>
            )}

            {/* PUBLISH */}

            {exam.status === "draft" && (
              <button
                className="primary-button"
                disabled={statusUpdating}
                onClick={() =>
                  updateExamStatus("published")
                }
              >
                {statusUpdating
                  ? "Publishing..."
                  : "Publish Exam"}
              </button>
            )}

            {/* CLOSE */}

            {exam.status === "published" && (
              <button
                className="secondary-button"
                disabled={statusUpdating}
                onClick={() =>
                  updateExamStatus("closed")
                }
              >
                {statusUpdating
                  ? "Closing..."
                  : "Close Exam"}
              </button>
            )}

            {/* MOVE BACK TO DRAFT */}

            {exam.status === "closed" && (
              <button
                className="secondary-button"
                disabled={statusUpdating}
                onClick={() =>
                  updateExamStatus("draft")
                }
              >
                {statusUpdating
                  ? "Updating..."
                  : "Move to Draft"}
              </button>
            )}

          </div>

        </div>

        {/* =====================================================
            ERROR
        ===================================================== */}

        {error && (
          <div className="error">
            {error}
          </div>
        )}

        {/* =====================================================
            SUMMARY
        ===================================================== */}

        <div className="summary">

          <div className="summary-card">

            <div className="summary-label">
              Duration
            </div>

            <div className="summary-value">
              {exam.duration_minutes} min
            </div>

          </div>

          <div className="summary-card">

            <div className="summary-label">
              Total Marks
            </div>

            <div className="summary-value">
              {calculateTotalMarks()}
            </div>

          </div>

          <div className="summary-card">

            <div className="summary-label">
              Sections
            </div>

            <div className="summary-value">
              {exam.sections?.length || 0}
            </div>

          </div>

          <div className="summary-card">

            <div className="summary-label">
              Status
            </div>

            <div className="summary-value status-value">
              {exam.status || "draft"}
            </div>

            <span
              className={`status-badge ${
                exam.status === "published"
                  ? "status-published"
                  : exam.status === "closed"
                    ? "status-closed"
                    : "status-draft"
              }`}
            >
              {exam.status || "draft"}
            </span>

          </div>

        </div>

        {/* =====================================================
            SECTIONS
        ===================================================== */}

        {exam.sections?.length === 0 ? (

          <div className="empty">

            <div style={{ fontSize: "40px" }}>
              📚
            </div>

            <div
              style={{
                marginTop: "10px",
                color: "#172033",
                fontWeight: 700,
              }}
            >
              No sections yet
            </div>

            <div style={{ marginTop: "5px" }}>
              Add an MCQ section or coding section to begin.
            </div>

          </div>

        ) : (

          <div className="section-list">

            {exam.sections.map((section) => {

              const sectionQuestions =
                getSectionQuestions(section);

              return (

                <div
                  className="section-card"
                  key={section.id}
                >

                  <div className="section-header">

                    <div>

                      <h2 className="section-title">
                        {section.title}
                      </h2>

                      <span className="section-type">
                        {section.section_type}
                      </span>

                    </div>

                    <div>
                      <strong>
                        {section.marks || 0}
                      </strong>{" "}
                      marks
                    </div>

                  </div>

                  <div className="section-body">

                    {sectionQuestions.length === 0 ? (

                      <div className="empty-section">
                        No questions added to this section yet.
                      </div>

                    ) : (

                      sectionQuestions.map(
                        (question, index) => (

                          <div
                            className="question-row"
                            key={question.id}
                          >

                            <div className="question-number">
                              {index + 1}
                            </div>

                            <div className="question-text">
                              {question.question_text}
                            </div>

                            <div className="question-marks">
                              {question.marks} marks
                            </div>

                          </div>

                        )
                      )

                    )}

                    <button
                      className="add-question-button"
                      onClick={() =>
                        openQuestionSelector(section)
                      }
                      disabled={
                        exam.status === "closed"
                      }
                    >
                      + Add Question from Question Bank
                    </button>

                  </div>

                </div>

              );
            })}

          </div>

        )}

        {/* =====================================================
            CREATE SECTION MODAL
        ===================================================== */}

        {showSectionModal && (

          <div className="modal-overlay">

            <div className="modal">

              <h2 className="modal-title">
                Add Exam Section
              </h2>

              <form onSubmit={createSection}>

                <div className="form-group">

                  <label className="form-label">
                    Section Title
                  </label>

                  <input
                    className="input"
                    value={sectionTitle}
                    onChange={(e) =>
                      setSectionTitle(
                        e.target.value
                      )
                    }
                    placeholder="Example: Multiple Choice Questions"
                  />

                </div>

                <div className="form-group">

                  <label className="form-label">
                    Section Type
                  </label>

                  <select
                    className="select"
                    value={sectionType}
                    onChange={(e) =>
                      setSectionType(
                        e.target.value
                      )
                    }
                  >

                    <option value="mcq">
                      Multiple Choice Questions
                    </option>

                    <option value="coding">
                      Coding Questions
                    </option>

                  </select>

                </div>

                <div className="modal-actions">

                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                      setShowSectionModal(false)
                    }
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    className="primary-button"
                  >
                    Create Section
                  </button>

                </div>

              </form>

            </div>

          </div>

        )}

        {/* =====================================================
            QUESTION SELECTOR MODAL
        ===================================================== */}

        {showQuestionModal && (

          <div className="modal-overlay">

            <div className="modal">

              <h2 className="modal-title">
                Add Question
              </h2>

              <p className="modal-subtitle">
                Select a question from a Question Bank.
                Only{" "}
                <strong>
                  {selectedSection?.section_type?.toUpperCase()}
                </strong>{" "}
                questions can be added to this section.
              </p>

              {/* QUESTION BANKS */}

              <div className="form-group">

                <label className="form-label">
                  Question Bank
                </label>

                {banks.length === 0 ? (

                  <div className="empty-section">
                    No question banks available.
                  </div>

                ) : (

                  <div className="bank-selector">

                    {banks.map((bank) => (

                      <button
                        type="button"
                        key={bank.id}
                        className={`bank-button ${
                          selectedBank?.id === bank.id
                            ? "selected"
                            : ""
                        }`}
                        onClick={() =>
                          loadBankQuestions(
                            bank.id
                          )
                        }
                      >

                        <div className="bank-name">
                          {bank.title}
                        </div>

                        <div className="bank-description">
                          {bank.description ||
                            "No description"}
                        </div>

                      </button>

                    ))}

                  </div>

                )}

              </div>

              {/* AVAILABLE QUESTIONS */}

              {selectedBank && (

                <div className="form-group">

                  <label className="form-label">
                    Available Questions
                  </label>

                  {questionsLoading ? (

                    <div className="empty-section">
                      Loading questions...
                    </div>

                  ) : bankQuestions.length === 0 ? (

                    <div className="empty-section">
                      This question bank has no questions.
                    </div>

                  ) : (

                    bankQuestions
                      .filter(
                        (question) =>
                          question.question_type ===
                          selectedSection?.section_type
                      )
                      .map((question) => (

                        <div
                          className="available-question"
                          key={question.id}
                        >

                          <div>

                            <div className="available-question-text">
                              {question.question_text}
                            </div>

                            <div
                              style={{
                                marginTop: "5px",
                                color: "#667085",
                                fontSize: "11px",
                              }}
                            >
                              {question.marks} marks •{" "}
                              {question.difficulty}
                            </div>

                          </div>

                          <button
                            type="button"
                            className="small-button"
                            onClick={() =>
                              addQuestionToSection(
                                question
                              )
                            }
                          >
                            Add
                          </button>

                        </div>

                      ))

                  )}

                </div>

              )}

              <div className="modal-actions">

                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => {
                    setShowQuestionModal(false);
                    setSelectedBank(null);
                    setBankQuestions([]);
                  }}
                >
                  Close
                </button>

              </div>

            </div>

          </div>

        )}

        {/* =====================================================
            INVITE CANDIDATE MODAL
        ===================================================== */}

        {showInviteModal && (

          <div className="modal-overlay">

            <div className="modal">

              <h2 className="modal-title">
                Invite Candidate
              </h2>

              {!generatedInvite ? (

                <form onSubmit={createCandidateInvite}>

                  <p className="modal-subtitle">
                    Create a unique invitation link for an
                    outside candidate to take this exam.
                  </p>

                  {/* CANDIDATE NAME */}

                  <div className="form-group">

                    <label className="form-label">
                      Candidate Name
                    </label>

                    <input
                      className="input"
                      value={candidateName}
                      onChange={(e) =>
                        setCandidateName(
                          e.target.value
                        )
                      }
                      placeholder="Enter candidate name"
                    />

                  </div>

                  {/* CANDIDATE EMAIL */}

                  <div className="form-group">

                    <label className="form-label">
                      Candidate Email
                    </label>

                    <input
                      className="input"
                      type="email"
                      value={candidateEmail}
                      onChange={(e) =>
                        setCandidateEmail(
                          e.target.value
                        )
                      }
                      placeholder="candidate@example.com"
                    />

                  </div>

                  {/* EXPIRY */}

                  <div className="form-group">

                    <label className="form-label">
                      Link Expiry
                    </label>

                    <select
                      className="select"
                      value={inviteExpiryDays}
                      onChange={(e) =>
                        setInviteExpiryDays(
                          e.target.value
                        )
                      }
                    >

                      <option value="1">
                        1 day
                      </option>

                      <option value="3">
                        3 days
                      </option>

                      <option value="7">
                        7 days
                      </option>

                      <option value="14">
                        14 days
                      </option>

                      <option value="30">
                        30 days
                      </option>

                    </select>

                  </div>

                  {/* MAX ATTEMPTS */}

                  <div className="form-group">

                    <label className="form-label">
                      Maximum Attempts
                    </label>

                    <select
                      className="select"
                      value={maxAttempts}
                      onChange={(e) =>
                        setMaxAttempts(
                          e.target.value
                        )
                      }
                    >

                      <option value="1">
                        1 attempt
                      </option>

                      <option value="2">
                        2 attempts
                      </option>

                      <option value="3">
                        3 attempts
                      </option>

                      <option value="5">
                        5 attempts
                      </option>

                    </select>

                  </div>

                  {/* BUTTONS */}

                  <div className="modal-actions">

                    <button
                      type="button"
                      className="secondary-button"
                      onClick={closeInviteModal}
                      disabled={inviteLoading}
                    >
                      Cancel
                    </button>

                    <button
                      type="submit"
                      className="primary-button"
                      disabled={inviteLoading}
                    >
                      {inviteLoading
                        ? "Generating..."
                        : "Generate Invite Link"}
                    </button>

                  </div>

                </form>

              ) : (

                <>

                  <div className="invite-success">

                    <div className="invite-success-title">
                      ✓ Invite Created Successfully
                    </div>

                    <div className="invite-info">
                      <strong>Candidate:</strong>{" "}
                      {generatedInvite.candidateName}
                    </div>

                    <div className="invite-info">
                      <strong>Email:</strong>{" "}
                      {generatedInvite.candidateEmail}
                    </div>

                    <div className="invite-info">

                      <strong>
                        Invite Link:
                      </strong>

                      <div className="invite-link-box">

                        <input
                          className="invite-link-input"
                          value={generatedInvite.link}
                          readOnly
                        />

                        <button
                          type="button"
                          className="copy-button"
                          onClick={copyInviteLink}
                        >
                          Copy
                        </button>

                      </div>

                    </div>

                    <div className="invite-note">
                      Send this link to the candidate.
                      The candidate can open the link
                      without having a trainer account.
                    </div>

                  </div>

                  <div className="modal-actions">

                    <button
                      type="button"
                      className="secondary-button"
                      onClick={closeInviteModal}
                    >
                      Close
                    </button>

                    <button
                      type="button"
                      className="primary-button"
                      onClick={() => {
                        setGeneratedInvite(null);
                        setCandidateName("");
                        setCandidateEmail("");
                        setInviteExpiryDays("7");
                        setMaxAttempts("1");
                      }}
                    >
                      Invite Another
                    </button>

                  </div>

                </>

              )}

            </div>

          </div>

        )}

      </div>

    </DashboardLayout>
  );
}