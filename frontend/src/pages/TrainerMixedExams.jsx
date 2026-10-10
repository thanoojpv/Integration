import React, { useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import DashboardLayout from "../components/DashboardLayout";

export default function TrainerMixedExams() {
  const [exams, setExams] = useState([]);
  const [courses, setCourses] = useState([]);

  const [loading, setLoading] = useState(true);
  const [coursesLoading, setCoursesLoading] = useState(true);

  const [error, setError] = useState("");

  const [showCreateExam, setShowCreateExam] = useState(false);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [courseId, setCourseId] = useState("");
  const [durationMinutes, setDurationMinutes] = useState(60);

  // ============================================================
  // LOAD MIXED EXAMS
  // ============================================================

  const loadExams = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await apiRequest("/trainer/mixed-exams");

      setExams(data?.exams || []);
    } catch (err) {
      setError(
        err.message || "Failed to load mixed exams."
      );
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // LOAD TRAINER COURSES
  // ============================================================

  const loadCourses = async () => {
    try {
      setCoursesLoading(true);

      const data = await apiRequest("/trainer/courses");

      setCourses(
        data?.courses ||
        data?.items ||
        []
      );
    } catch (err) {
      /*
       * If the trainer course endpoint is not available,
       * the trainer can still enter the course ID manually.
       */
      console.error(
        "Failed to load trainer courses:",
        err
      );

      setCourses([]);
    } finally {
      setCoursesLoading(false);
    }
  };

  useEffect(() => {
    loadExams();
    loadCourses();
  }, []);

  // ============================================================
  // CREATE EXAM
  // ============================================================

  const createExam = async (event) => {
    event.preventDefault();

    if (!title.trim()) {
      alert("Please enter the exam title.");
      return;
    }

    if (!courseId.trim()) {
      alert("Please select or enter a course ID.");
      return;
    }

    if (Number(durationMinutes) < 1) {
      alert("Duration must be at least 1 minute.");
      return;
    }

    try {
      await apiRequest("/trainer/mixed-exams", {
        method: "POST",
        body: JSON.stringify({
          title: title.trim(),
          description: description.trim(),
          course_id: courseId.trim(),
          duration_minutes: Number(durationMinutes),
        }),
      });

      setTitle("");
      setDescription("");
      setCourseId("");
      setDurationMinutes(60);

      setShowCreateExam(false);

      await loadExams();

      alert("Mixed exam created successfully.");
    } catch (err) {
      alert(
        err.message ||
        "Failed to create mixed exam."
      );
    }
  };

  // ============================================================
  // STATUS BADGE
  // ============================================================

  const getStatusClass = (status) => {
    if (status === "published") {
      return "status published";
    }

    if (status === "active") {
      return "status active";
    }

    return "status draft";
  };

  return (
    <DashboardLayout role="trainer">

      <div className="mixed-exams-page">

        <style>{`

          .mixed-exams-page {
            min-height: 100%;
            padding: 28px;
            background: #f7f8fc;
            box-sizing: border-box;
          }

          .page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
            margin-bottom: 26px;
          }

          .page-title {
            margin: 0;
            color: #172033;
            font-size: 28px;
            font-weight: 700;
          }

          .page-subtitle {
            margin: 7px 0 0;
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

          .error {
            margin-bottom: 20px;
            padding: 12px 14px;
            border-radius: 10px;
            border: 1px solid #fecdca;
            background: #fef3f2;
            color: #b42318;
          }

          .exam-grid {
            display: grid;
            grid-template-columns: repeat(
              auto-fill,
              minmax(300px, 1fr)
            );
            gap: 20px;
          }

          .exam-card {
            background: white;
            border: 1px solid #eaecf0;
            border-radius: 15px;
            padding: 20px;
            box-shadow:
              0 2px 8px rgba(16, 24, 40, 0.04);
            transition: 0.2s ease;
          }

          .exam-card:hover {
            transform: translateY(-2px);
            box-shadow:
              0 8px 20px rgba(16, 24, 40, 0.08);
          }

          .exam-card-top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 15px;
          }

          .exam-title {
            margin: 0;
            color: #172033;
            font-size: 18px;
            font-weight: 700;
          }

          .exam-description {
            margin: 10px 0 18px;
            color: #667085;
            font-size: 13px;
            line-height: 1.5;
          }

          .status {
            display: inline-flex;
            align-items: center;
            padding: 5px 9px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            white-space: nowrap;
          }

          .status.draft {
            background: #f2f4f7;
            color: #475467;
          }

          .status.published {
            background: #ecfdf3;
            color: #027a48;
          }

          .status.active {
            background: #eff8ff;
            color: #175cd3;
          }

          .exam-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 15px;
          }

          .info-box {
            padding: 12px;
            border-radius: 10px;
            background: #f8fafc;
          }

          .info-label {
            color: #667085;
            font-size: 11px;
            margin-bottom: 4px;
          }

          .info-value {
            color: #172033;
            font-size: 14px;
            font-weight: 700;
          }

          .exam-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #eaecf0;
          }

          .manage-button {
            width: 100%;
            border: none;
            border-radius: 9px;
            padding: 10px 14px;
            background: #eef4ff;
            color: #175cd3;
            font-weight: 600;
            cursor: pointer;
          }

          .manage-button:hover {
            background: #dbeafe;
          }

          .empty {
            padding: 60px 20px;
            background: white;
            border: 1px solid #eaecf0;
            border-radius: 15px;
            text-align: center;
            color: #667085;
          }

          .empty-icon {
            font-size: 40px;
            margin-bottom: 12px;
          }

          .empty-title {
            color: #172033;
            font-size: 17px;
            font-weight: 700;
            margin-bottom: 7px;
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
            width: min(650px, 100%);
            max-height: 90vh;
            overflow-y: auto;
            background: white;
            border-radius: 16px;
            padding: 25px;
            box-sizing: border-box;
          }

          .modal-title {
            margin: 0 0 20px;
            color: #172033;
            font-size: 21px;
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
            box-sizing: border-box;
            padding: 11px 12px;
            border: 1px solid #d0d5dd;
            border-radius: 9px;
            background: white;
            font-size: 14px;
            outline: none;
          }

          .textarea {
            min-height: 100px;
            resize: vertical;
          }

          .input:focus,
          .textarea:focus,
          .select:focus {
            border-color: #2563eb;
            box-shadow:
              0 0 0 3px rgba(37, 99, 235, 0.1);
          }

          .helper-text {
            margin-top: 6px;
            color: #667085;
            font-size: 12px;
          }

          .modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            margin-top: 22px;
          }

          @media (max-width: 700px) {

            .mixed-exams-page {
              padding: 18px;
            }

            .page-header {
              flex-direction: column;
              align-items: flex-start;
            }

            .page-header .primary-button {
              width: 100%;
            }

          }

        `}</style>

        {/* =====================================================
            HEADER
        ===================================================== */}

        <div className="page-header">

          <div>

            <h1 className="page-title">
              Mixed Exams
            </h1>

            <p className="page-subtitle">
              Create assessments containing both MCQ and coding
              questions for learners and hiring candidates.
            </p>

          </div>

          <button
            className="primary-button"
            onClick={() =>
              setShowCreateExam(true)
            }
          >
            + Create Mixed Exam
          </button>

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
            EXAM LIST
        ===================================================== */}

        {loading ? (

          <div className="empty">
            Loading mixed exams...
          </div>

        ) : exams.length === 0 ? (

          <div className="empty">

            <div className="empty-icon">
              📝
            </div>

            <div className="empty-title">
              No mixed exams yet
            </div>

            <div>
              Create your first mixed exam with MCQ and coding
              sections.
            </div>

          </div>

        ) : (

          <div className="exam-grid">

            {exams.map((exam) => (

              <div
                className="exam-card"
                key={exam.id}
              >

                <div className="exam-card-top">

                  <h2 className="exam-title">
                    {exam.title}
                  </h2>

                  <span
                    className={getStatusClass(
                      exam.status
                    )}
                  >
                    {exam.status || "draft"}
                  </span>

                </div>

                <div className="exam-description">

                  {exam.description ||
                    "No description provided."}

                </div>

                <div className="exam-info">

                  <div className="info-box">

                    <div className="info-label">
                      Course
                    </div>

                    <div className="info-value">
                      {exam.course_id}
                    </div>

                  </div>

                  <div className="info-box">

                    <div className="info-label">
                      Duration
                    </div>

                    <div className="info-value">
                      {exam.duration_minutes} min
                    </div>

                  </div>

                  <div className="info-box">

                    <div className="info-label">
                      Total Marks
                    </div>

                    <div className="info-value">
                      {exam.total_marks ?? 0}
                    </div>

                  </div>

                  <div className="info-box">

                    <div className="info-label">
                      Exam ID
                    </div>

                    <div className="info-value">
                      #{exam.id}
                    </div>

                  </div>

                </div>

                <div className="exam-footer">

                  <button
                    className="manage-button"
                    onClick={() => {
                      window.location.href =
                        `/trainer/mixed-exams/${exam.id}`;
                    }}
                  >
                    Manage Exam →
                  </button>

                </div>

              </div>

            ))}

          </div>

        )}

        {/* =====================================================
            CREATE EXAM MODAL
        ===================================================== */}

        {showCreateExam && (

          <div className="modal-overlay">

            <div className="modal">

              <h2 className="modal-title">
                Create Mixed Exam
              </h2>

              <form onSubmit={createExam}>

                {/* TITLE */}

                <div className="form-group">

                  <label className="form-label">
                    Exam Title
                  </label>

                  <input
                    className="input"
                    value={title}
                    onChange={(e) =>
                      setTitle(e.target.value)
                    }
                    placeholder="Example: Java Hiring Assessment"
                  />

                </div>

                {/* DESCRIPTION */}

                <div className="form-group">

                  <label className="form-label">
                    Description
                  </label>

                  <textarea
                    className="textarea"
                    value={description}
                    onChange={(e) =>
                      setDescription(
                        e.target.value
                      )
                    }
                    placeholder="Describe the purpose of this exam"
                  />

                </div>

                {/* COURSE */}

                <div className="form-group">

                  <label className="form-label">
                    Course
                  </label>

                  {coursesLoading ? (

                    <select
                      className="select"
                      disabled
                    >
                      <option>
                        Loading courses...
                      </option>
                    </select>

                  ) : courses.length > 0 ? (

                    <select
                      className="select"
                      value={courseId}
                      onChange={(e) =>
                        setCourseId(
                          e.target.value
                        )
                      }
                    >

                      <option value="">
                        Select a course
                      </option>

                      {courses.map((course) => (

                        <option
                          key={
                            course.id ||
                            course.course_id
                          }
                          value={
                            course.id ||
                            course.course_id
                          }
                        >
                          {course.title ||
                            course.name ||
                            course.course_id ||
                            course.id}
                        </option>

                      ))}

                    </select>

                  ) : (

                    <>

                      <input
                        className="input"
                        value={courseId}
                        onChange={(e) =>
                          setCourseId(
                            e.target.value
                          )
                        }
                        placeholder="Example: course-node"
                      />

                      <div className="helper-text">
                        Enter the course ID connected to
                        this exam.
                      </div>

                    </>

                  )}

                </div>

                {/* DURATION */}

                <div className="form-group">

                  <label className="form-label">
                    Duration
                  </label>

                  <input
                    className="input"
                    type="number"
                    min="1"
                    value={durationMinutes}
                    onChange={(e) =>
                      setDurationMinutes(
                        e.target.value
                      )
                    }
                  />

                  <div className="helper-text">
                    Duration is measured in minutes.
                  </div>

                </div>

                {/* ACTIONS */}

                <div className="modal-actions">

                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                      setShowCreateExam(false)
                    }
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    className="primary-button"
                  >
                    Create Exam
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