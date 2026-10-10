import React, { useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import DashboardLayout from "../components/DashboardLayout";

export default function TrainerQuestionBank() {
  const [banks, setBanks] = useState([]);
  const [selectedBank, setSelectedBank] = useState(null);
  const [questions, setQuestions] = useState([]);

  const [loading, setLoading] = useState(true);
  const [questionsLoading, setQuestionsLoading] = useState(false);
  const [error, setError] = useState("");

  const [showCreateBank, setShowCreateBank] = useState(false);
  const [showAddQuestion, setShowAddQuestion] = useState(false);

  const [bankTitle, setBankTitle] = useState("");
  const [bankDescription, setBankDescription] = useState("");

  const [questionType, setQuestionType] = useState("mcq");
  const [questionText, setQuestionText] = useState("");

  const [optionA, setOptionA] = useState("");
  const [optionB, setOptionB] = useState("");
  const [optionC, setOptionC] = useState("");
  const [optionD, setOptionD] = useState("");
  const [correctAnswer, setCorrectAnswer] = useState("");

  const [codingDescription, setCodingDescription] = useState("");
  const [starterCode, setStarterCode] = useState("");
  const [language, setLanguage] = useState("python");

  const [difficulty, setDifficulty] = useState("medium");
  const [marks, setMarks] = useState(1);

  // ============================================================
  // LOAD QUESTION BANKS
  // ============================================================

  const loadBanks = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await apiRequest("/trainer/question-banks");

      setBanks(data?.banks || []);
    } catch (err) {
      setError(err.message || "Failed to load question banks");
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // LOAD QUESTIONS FOR SELECTED BANK
  // ============================================================

  const loadBankQuestions = async (bankId) => {
    try {
      setQuestionsLoading(true);
      setError("");

      const data = await apiRequest(
        `/trainer/question-banks/${bankId}`
      );

      setSelectedBank(data?.bank || null);
      setQuestions(data?.bank?.questions || []);
    } catch (err) {
      setError(err.message || "Failed to load questions");
    } finally {
      setQuestionsLoading(false);
    }
  };

  useEffect(() => {
    loadBanks();
  }, []);

  // ============================================================
  // RESET QUESTION FORM
  // ============================================================

  const resetQuestionForm = () => {
    setQuestionType("mcq");
    setQuestionText("");

    setOptionA("");
    setOptionB("");
    setOptionC("");
    setOptionD("");
    setCorrectAnswer("");

    setCodingDescription("");
    setStarterCode("");
    setLanguage("python");

    setDifficulty("medium");
    setMarks(1);
  };

  // ============================================================
  // CREATE QUESTION BANK
  // ============================================================

  const createBank = async (event) => {
    event.preventDefault();

    if (!bankTitle.trim()) {
      alert("Please enter a question bank title.");
      return;
    }

    try {
      await apiRequest("/trainer/question-banks", {
        method: "POST",
        body: JSON.stringify({
          title: bankTitle.trim(),
          description: bankDescription.trim(),
        }),
      });

      setBankTitle("");
      setBankDescription("");
      setShowCreateBank(false);

      await loadBanks();

      alert("Question bank created successfully.");
    } catch (err) {
      alert(err.message || "Failed to create question bank.");
    }
  };

  // ============================================================
  // ADD QUESTION
  // ============================================================

  const addQuestion = async (event) => {
    event.preventDefault();

    if (!selectedBank) {
      alert("Please select a question bank.");
      return;
    }

    if (!questionText.trim()) {
      alert("Please enter the question.");
      return;
    }

    if (questionType === "mcq") {
      if (!optionA.trim() || !optionB.trim() || !optionC.trim() || !optionD.trim()) {
        alert("Please enter all four options.");
        return;
      }

      if (!correctAnswer) {
        alert("Please select the correct answer.");
        return;
      }
    }

    if (
      questionType === "coding" &&
      !codingDescription.trim()
    ) {
      alert("Please enter the coding description.");
      return;
    }

    if (Number(marks) < 1) {
      alert("Marks must be at least 1.");
      return;
    }

    try {
      await apiRequest(
        `/trainer/question-banks/${selectedBank.id}/questions`,
        {
          method: "POST",
          body: JSON.stringify({
            question_type: questionType,
            question_text: questionText.trim(),

            option_a:
              questionType === "mcq"
                ? optionA.trim()
                : null,

            option_b:
              questionType === "mcq"
                ? optionB.trim()
                : null,

            option_c:
              questionType === "mcq"
                ? optionC.trim()
                : null,

            option_d:
              questionType === "mcq"
                ? optionD.trim()
                : null,

            correct_answer:
              questionType === "mcq"
                ? correctAnswer
                : null,

            coding_description:
              questionType === "coding"
                ? codingDescription.trim()
                : "",

            starter_code:
              questionType === "coding"
                ? starterCode
                : "",

            language:
              questionType === "coding"
                ? language
                : "python",

            difficulty,
            marks: Number(marks),
          }),
        }
      );

      resetQuestionForm();
      setShowAddQuestion(false);

      await loadBankQuestions(selectedBank.id);

      alert("Question added successfully.");
    } catch (err) {
      alert(err.message || "Failed to add question.");
    }
  };

  // ============================================================
  // DELETE QUESTION
  // ============================================================

  const deleteQuestion = async (questionId) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this question?"
    );

    if (!confirmed) {
      return;
    }

    try {
      await apiRequest(
        `/trainer/question-bank-questions/${questionId}`,
        {
          method: "DELETE",
        }
      );

      await loadBankQuestions(selectedBank.id);

      alert("Question deleted successfully.");
    } catch (err) {
      alert(err.message || "Failed to delete question.");
    }
  };

  // ============================================================
  // DELETE QUESTION BANK
  // ============================================================

  const deleteBank = async (bankId) => {
    const confirmed = window.confirm(
      "Delete this question bank and all its questions?"
    );

    if (!confirmed) {
      return;
    }

    try {
      await apiRequest(
        `/trainer/question-banks/${bankId}`,
        {
          method: "DELETE",
        }
      );

      if (selectedBank?.id === bankId) {
        setSelectedBank(null);
        setQuestions([]);
      }

      await loadBanks();

      alert("Question bank deleted successfully.");
    } catch (err) {
      alert(err.message || "Failed to delete question bank.");
    }
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <DashboardLayout role="trainer">

      <div className="question-bank-page">

        <style>{`
          .question-bank-page {
            padding: 28px;
            min-height: 100%;
            background: #f7f8fc;
            box-sizing: border-box;
          }

          .page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
            margin-bottom: 24px;
          }

          .page-title {
            margin: 0;
            font-size: 28px;
            font-weight: 700;
            color: #172033;
          }

          .page-subtitle {
            margin: 6px 0 0;
            color: #667085;
            font-size: 14px;
          }

          .primary-button {
            border: none;
            border-radius: 10px;
            padding: 11px 18px;
            background: #2563eb;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: 0.2s ease;
          }

          .primary-button:hover {
            background: #1d4ed8;
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

          .danger-button {
            border: none;
            border-radius: 8px;
            padding: 8px 12px;
            background: #fee4e2;
            color: #b42318;
            font-weight: 600;
            cursor: pointer;
          }

          .danger-button:hover {
            background: #fecdca;
          }

          .layout {
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 22px;
          }

          .card {
            background: white;
            border: 1px solid #eaecf0;
            border-radius: 14px;
            box-shadow: 0 2px 8px rgba(16, 24, 40, 0.04);
            overflow: hidden;
          }

          .card-header {
            padding: 18px 20px;
            border-bottom: 1px solid #eaecf0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 15px;
          }

          .card-title {
            margin: 0;
            font-size: 17px;
            color: #172033;
          }

          .bank-list {
            padding: 10px;
          }

          .bank-item {
            width: 100%;
            text-align: left;
            border: 1px solid transparent;
            background: transparent;
            padding: 14px;
            border-radius: 10px;
            cursor: pointer;
            margin-bottom: 8px;
            transition: 0.2s ease;
          }

          .bank-item:hover {
            background: #f2f4f7;
          }

          .bank-item.active {
            background: #eff6ff;
            border-color: #bfdbfe;
          }

          .bank-name {
            font-weight: 650;
            color: #172033;
          }

          .bank-description {
            margin-top: 5px;
            color: #667085;
            font-size: 12px;
            line-height: 1.4;
          }

          .bank-actions {
            margin-top: 10px;
          }

          .empty {
            padding: 35px 20px;
            text-align: center;
            color: #667085;
          }

          .question-content {
            padding: 20px;
          }

          .question-card {
            border: 1px solid #eaecf0;
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 14px;
            background: white;
          }

          .question-card:last-child {
            margin-bottom: 0;
          }

          .question-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 15px;
          }

          .badge {
            display: inline-flex;
            padding: 5px 9px;
            border-radius: 999px;
            background: #eef4ff;
            color: #3538cd;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
          }

          .coding-badge {
            background: #ecfdf3;
            color: #027a48;
          }

          .question-text {
            margin: 13px 0;
            font-weight: 600;
            color: #172033;
            line-height: 1.5;
          }

          .options {
            display: grid;
            gap: 7px;
            color: #475467;
            font-size: 14px;
          }

          .correct-option {
            font-weight: 700;
            color: #027a48;
          }

          .question-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 14px;
            color: #667085;
            font-size: 12px;
          }

          .meta-pill {
            background: #f2f4f7;
            padding: 5px 9px;
            border-radius: 999px;
          }

          .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(16, 24, 40, 0.55);
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            z-index: 1000;
          }

          .modal {
            width: min(650px, 100%);
            max-height: 90vh;
            overflow-y: auto;
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-sizing: border-box;
          }

          .modal-title {
            margin: 0 0 20px;
            font-size: 21px;
            color: #172033;
          }

          .form-group {
            margin-bottom: 16px;
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
            box-sizing: border-box;
            border: 1px solid #d0d5dd;
            border-radius: 9px;
            padding: 10px 12px;
            font-size: 14px;
            outline: none;
            background: white;
          }

          .input:focus,
          .textarea:focus,
          .select:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
          }

          .textarea {
            min-height: 100px;
            resize: vertical;
          }

          .code-area {
            min-height: 150px;
            font-family: monospace;
            line-height: 1.5;
          }

          .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
          }

          .modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            margin-top: 20px;
          }

          .error {
            background: #fef3f2;
            color: #b42318;
            border: 1px solid #fecdca;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 18px;
          }

          .question-description {
            margin-top: 10px;
            color: #475467;
            font-size: 14px;
            line-height: 1.5;
          }

          @media (max-width: 1100px) {
            .layout {
              grid-template-columns: 280px 1fr;
            }
          }

          @media (max-width: 900px) {
            .layout {
              grid-template-columns: 1fr;
            }
          }

          @media (max-width: 600px) {
            .question-bank-page {
              padding: 18px;
            }

            .page-header {
              align-items: flex-start;
              flex-direction: column;
            }

            .primary-button {
              width: 100%;
            }

            .form-row {
              grid-template-columns: 1fr;
            }

            .card-header {
              align-items: flex-start;
              flex-direction: column;
            }
          }
        `}</style>

        {/* ======================================================
            PAGE HEADER
        ====================================================== */}

        <div className="page-header">

          <div>
            <h1 className="page-title">
              Question Bank
            </h1>

            <p className="page-subtitle">
              Create reusable MCQ and coding questions for mixed exams.
            </p>
          </div>

          <button
            className="primary-button"
            onClick={() => setShowCreateBank(true)}
          >
            + Create Question Bank
          </button>

        </div>

        {/* ======================================================
            ERROR
        ====================================================== */}

        {error && (
          <div className="error">
            {error}
          </div>
        )}

        {/* ======================================================
            MAIN LAYOUT
        ====================================================== */}

        <div className="layout">

          {/* ====================================================
              QUESTION BANK LIST
          ==================================================== */}

          <div className="card">

            <div className="card-header">

              <h2 className="card-title">
                My Question Banks
              </h2>

            </div>

            {loading ? (
              <div className="empty">
                Loading question banks...
              </div>
            ) : banks.length === 0 ? (
              <div className="empty">
                No question banks created yet.
              </div>
            ) : (
              <div className="bank-list">

                {banks.map((bank) => (

                  <div
                    key={bank.id}
                    className={`bank-item ${
                      selectedBank?.id === bank.id
                        ? "active"
                        : ""
                    }`}
                  >

                    <button
                      type="button"
                      style={{
                        border: "none",
                        background: "transparent",
                        padding: 0,
                        margin: 0,
                        width: "100%",
                        textAlign: "left",
                        cursor: "pointer",
                      }}
                      onClick={() =>
                        loadBankQuestions(bank.id)
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

                    <div className="bank-actions">

                      <button
                        type="button"
                        className="danger-button"
                        onClick={() =>
                          deleteBank(bank.id)
                        }
                      >
                        Delete
                      </button>

                    </div>

                  </div>

                ))}

              </div>
            )}

          </div>

          {/* ====================================================
              QUESTIONS
          ==================================================== */}

          <div className="card">

            <div className="card-header">

              <div>

                <h2 className="card-title">
                  {selectedBank
                    ? selectedBank.title
                    : "Questions"}
                </h2>

              </div>

              {selectedBank && (
                <button
                  className="primary-button"
                  onClick={() => {
                    resetQuestionForm();
                    setShowAddQuestion(true);
                  }}
                >
                  + Add Question
                </button>
              )}

            </div>

            <div className="question-content">

              {!selectedBank ? (

                <div className="empty">
                  Select a question bank to view its questions.
                </div>

              ) : questionsLoading ? (

                <div className="empty">
                  Loading questions...
                </div>

              ) : questions.length === 0 ? (

                <div className="empty">
                  This question bank has no questions yet.
                </div>

              ) : (

                questions.map((question) => (

                  <div
                    className="question-card"
                    key={question.id}
                  >

                    <div className="question-top">

                      <span
                        className={
                          question.question_type === "coding"
                            ? "badge coding-badge"
                            : "badge"
                        }
                      >
                        {question.question_type}
                      </span>

                      <button
                        type="button"
                        className="danger-button"
                        onClick={() =>
                          deleteQuestion(question.id)
                        }
                      >
                        Delete
                      </button>

                    </div>

                    <div className="question-text">
                      {question.question_text}
                    </div>

                    {/* MCQ */}

                    {question.question_type === "mcq" && (
                      <div className="options">

                        <div
                          className={
                            question.correct_answer === "A"
                              ? "correct-option"
                              : ""
                          }
                        >
                          A. {question.option_a}
                        </div>

                        <div
                          className={
                            question.correct_answer === "B"
                              ? "correct-option"
                              : ""
                          }
                        >
                          B. {question.option_b}
                        </div>

                        <div
                          className={
                            question.correct_answer === "C"
                              ? "correct-option"
                              : ""
                          }
                        >
                          C. {question.option_c}
                        </div>

                        <div
                          className={
                            question.correct_answer === "D"
                              ? "correct-option"
                              : ""
                          }
                        >
                          D. {question.option_d}
                        </div>

                      </div>
                    )}

                    {/* CODING */}

                    {question.question_type === "coding" && (
                      <div className="options">

                        <div className="question-description">
                          <strong>
                            Description:
                          </strong>{" "}
                          {question.coding_description}
                        </div>

                        <div>
                          <strong>
                            Language:
                          </strong>{" "}
                          {question.language}
                        </div>

                      </div>
                    )}

                    <div className="question-meta">

                      <span className="meta-pill">
                        Marks: {question.marks}
                      </span>

                      <span className="meta-pill">
                        Difficulty: {question.difficulty}
                      </span>

                    </div>

                  </div>

                ))

              )}

            </div>

          </div>

        </div>

        {/* ======================================================
            CREATE QUESTION BANK MODAL
        ====================================================== */}

        {showCreateBank && (

          <div className="modal-overlay">

            <div className="modal">

              <h2 className="modal-title">
                Create Question Bank
              </h2>

              <form onSubmit={createBank}>

                <div className="form-group">

                  <label className="form-label">
                    Bank Title
                  </label>

                  <input
                    className="input"
                    value={bankTitle}
                    onChange={(e) =>
                      setBankTitle(e.target.value)
                    }
                    placeholder="Example: Java Interview Questions"
                  />

                </div>

                <div className="form-group">

                  <label className="form-label">
                    Description
                  </label>

                  <textarea
                    className="textarea"
                    value={bankDescription}
                    onChange={(e) =>
                      setBankDescription(
                        e.target.value
                      )
                    }
                    placeholder="Describe this question bank"
                  />

                </div>

                <div className="modal-actions">

                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                      setShowCreateBank(false)
                    }
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    className="primary-button"
                  >
                    Create Bank
                  </button>

                </div>

              </form>

            </div>

          </div>

        )}

        {/* ======================================================
            ADD QUESTION MODAL
        ====================================================== */}

        {showAddQuestion && (

          <div className="modal-overlay">

            <div className="modal">

              <h2 className="modal-title">
                Add Question
              </h2>

              <form onSubmit={addQuestion}>

                {/* QUESTION TYPE */}

                <div className="form-group">

                  <label className="form-label">
                    Question Type
                  </label>

                  <select
                    className="select"
                    value={questionType}
                    onChange={(e) => {
                      const newType = e.target.value;

                      resetQuestionForm();

                      setQuestionType(newType);
                    }}
                  >

                    <option value="mcq">
                      Multiple Choice Question
                    </option>

                    <option value="coding">
                      Coding Question
                    </option>

                  </select>

                </div>

                {/* QUESTION */}

                <div className="form-group">

                  <label className="form-label">
                    Question
                  </label>

                  <textarea
                    className="textarea"
                    value={questionText}
                    onChange={(e) =>
                      setQuestionText(
                        e.target.value
                      )
                    }
                    placeholder="Enter the question"
                  />

                </div>

                {/* MCQ FIELDS */}

                {questionType === "mcq" && (
                  <>

                    <div className="form-row">

                      <div className="form-group">

                        <label className="form-label">
                          Option A
                        </label>

                        <input
                          className="input"
                          value={optionA}
                          onChange={(e) =>
                            setOptionA(
                              e.target.value
                            )
                          }
                          placeholder="Enter option A"
                        />

                      </div>

                      <div className="form-group">

                        <label className="form-label">
                          Option B
                        </label>

                        <input
                          className="input"
                          value={optionB}
                          onChange={(e) =>
                            setOptionB(
                              e.target.value
                            )
                          }
                          placeholder="Enter option B"
                        />

                      </div>

                    </div>

                    <div className="form-row">

                      <div className="form-group">

                        <label className="form-label">
                          Option C
                        </label>

                        <input
                          className="input"
                          value={optionC}
                          onChange={(e) =>
                            setOptionC(
                              e.target.value
                            )
                          }
                          placeholder="Enter option C"
                        />

                      </div>

                      <div className="form-group">

                        <label className="form-label">
                          Option D
                        </label>

                        <input
                          className="input"
                          value={optionD}
                          onChange={(e) =>
                            setOptionD(
                              e.target.value
                            )
                          }
                          placeholder="Enter option D"
                        />

                      </div>

                    </div>

                    <div className="form-group">

                      <label className="form-label">
                        Correct Answer
                      </label>

                      <select
                        className="select"
                        value={correctAnswer}
                        onChange={(e) =>
                          setCorrectAnswer(
                            e.target.value
                          )
                        }
                      >

                        <option value="">
                          Select correct answer
                        </option>

                        <option value="A">
                          A
                        </option>

                        <option value="B">
                          B
                        </option>

                        <option value="C">
                          C
                        </option>

                        <option value="D">
                          D
                        </option>

                      </select>

                    </div>

                  </>
                )}

                {/* CODING FIELDS */}

                {questionType === "coding" && (
                  <>

                    <div className="form-group">

                      <label className="form-label">
                        Coding Description
                      </label>

                      <textarea
                        className="textarea"
                        value={codingDescription}
                        onChange={(e) =>
                          setCodingDescription(
                            e.target.value
                          )
                        }
                        placeholder="Explain the coding problem"
                      />

                    </div>

                    <div className="form-group">

                      <label className="form-label">
                        Starter Code
                      </label>

                      <textarea
                        className="textarea code-area"
                        value={starterCode}
                        onChange={(e) =>
                          setStarterCode(
                            e.target.value
                          )
                        }
                        placeholder="Enter starter code"
                      />

                    </div>

                    <div className="form-group">

                      <label className="form-label">
                        Programming Language
                      </label>

                      <select
                        className="select"
                        value={language}
                        onChange={(e) =>
                          setLanguage(
                            e.target.value
                          )
                        }
                      >

                        <option value="python">
                          Python
                        </option>

                        <option value="javascript">
                          JavaScript
                        </option>

                        <option value="java">
                          Java
                        </option>

                        <option value="cpp">
                          C++
                        </option>

                      </select>

                    </div>

                  </>
                )}

                {/* DIFFICULTY + MARKS */}

                <div className="form-row">

                  <div className="form-group">

                    <label className="form-label">
                      Difficulty
                    </label>

                    <select
                      className="select"
                      value={difficulty}
                      onChange={(e) =>
                        setDifficulty(
                          e.target.value
                        )
                      }
                    >

                      <option value="easy">
                        Easy
                      </option>

                      <option value="medium">
                        Medium
                      </option>

                      <option value="hard">
                        Hard
                      </option>

                    </select>

                  </div>

                  <div className="form-group">

                    <label className="form-label">
                      Marks
                    </label>

                    <input
                      className="input"
                      type="number"
                      min="1"
                      value={marks}
                      onChange={(e) =>
                        setMarks(e.target.value)
                      }
                    />

                  </div>

                </div>

                {/* MODAL ACTIONS */}

                <div className="modal-actions">

                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => {
                      setShowAddQuestion(false);
                      resetQuestionForm();
                    }}
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    className="primary-button"
                  >
                    Add Question
                  </button>

                </div>

              </form>

            </div>

          </div>

        )}

      </div>

    </DashboardLayout>
  );
}