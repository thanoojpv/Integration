import React, { useEffect, useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import { apiRequest } from "../services/api";

export default function Community() {

  // =====================================================
  // STATE
  // =====================================================

  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState("");

  const [lessons, setLessons] = useState([]);
  const [selectedLesson, setSelectedLesson] = useState("");

  const [discussions, setDiscussions] = useState([]);

  const [loadingCourses, setLoadingCourses] = useState(true);
  const [loadingCommunity, setLoadingCommunity] = useState(false);

  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);

  const [message, setMessage] = useState("");

  const [posting, setPosting] = useState(false);


  // =====================================================
  // LOAD COURSES
  // =====================================================

  useEffect(() => {
    loadCourses();
  }, []);


  async function loadCourses() {

    setLoadingCourses(true);
    setError("");

    try {

      const data = await apiRequest(
        "/my-learning"
      );

      const courseList =
        data?.courses ||
        [];

      setCourses(courseList);

      if (courseList.length > 0) {

        setSelectedCourse(
          courseList[0].id
        );

      }

    } catch (err) {

      console.error(err);

      setError(
        err.message ||
        "Unable to load your courses."
      );

    } finally {

      setLoadingCourses(false);

    }
  }


  // =====================================================
  // LOAD COMMUNITY WHEN COURSE CHANGES
  // =====================================================

  useEffect(() => {

    if (!selectedCourse) {

      setLessons([]);
      setDiscussions([]);
      setSelectedLesson("");

      return;

    }

    loadCommunity(
      selectedCourse
    );

  }, [selectedCourse]);


  async function loadCommunity(
    courseId
  ) {

    setLoadingCommunity(true);
    setError("");

    try {

      const data = await apiRequest(
        `/courses/${courseId}/discussions`
      );

      const lessonList =
        data?.lessons ||
        [];

      const discussionList =
        data?.discussions ||
        [];

      setLessons(
        lessonList
      );

      setDiscussions(
        discussionList
      );

      if (lessonList.length > 0) {

        setSelectedLesson(
          lessonList[0].id
        );

      } else {

        setSelectedLesson("");

      }

    } catch (err) {

      console.error(err);

      setError(
        err.message ||
        "Unable to load community discussions."
      );

      setLessons([]);
      setDiscussions([]);

    } finally {

      setLoadingCommunity(false);

    }
  }


  // =====================================================
  // CREATE DISCUSSION
  // =====================================================

  async function createDiscussion(
    event
  ) {

    event.preventDefault();

    setError("");

    if (!selectedCourse) {

      setError(
        "Please select a course."
      );

      return;
    }

    if (!selectedLesson) {

      setError(
        "Please select a lesson."
      );

      return;
    }

    if (!message.trim()) {

      setError(
        "Please enter your question."
      );

      return;
    }

    setPosting(true);

    try {

      await apiRequest(
        `/courses/${selectedCourse}/discussions`,
        {
          method: "POST",

          body: JSON.stringify({
            lesson_id: selectedLesson,
            message: message.trim(),
          }),
        }
      );

      setMessage("");

      setShowForm(false);

      await loadCommunity(
        selectedCourse
      );

    } catch (err) {

      console.error(err);

      setError(
        err.message ||
        "Unable to post your question."
      );

    } finally {

      setPosting(false);

    }
  }


  // =====================================================
  // FORMAT DATE
  // =====================================================

  function formatDate(value) {

    if (!value) {
      return "";
    }

    const date = new Date(value);

    if (
      Number.isNaN(
        date.getTime()
      )
    ) {

      return "";

    }

    return date.toLocaleString();

  }


  // =====================================================
  // FIND LESSON NAME
  // =====================================================

  function lessonName(
    lessonId
  ) {

    const lesson =
      lessons.find(
        (item) =>
          String(item.id) ===
          String(lessonId)
      );

    return (
      lesson?.title ||
      "Lesson"
    );
  }


  // =====================================================
  // SELECTED COURSE NAME
  // =====================================================

  function selectedCourseName() {

    const course =
      courses.find(
        (item) =>
          String(item.id) ===
          String(selectedCourse)
      );

    return (
      course?.title ||
      "Course"
    );
  }


  // =====================================================
  // MAIN UI
  // =====================================================

  return (

    <DashboardLayout role="learner">

      <div className="community-page">


        {/* =================================================
            HEADER
        ================================================= */}

        <div className="community-header">

          <div>

            <div className="community-eyebrow">
              LEARNING COMMUNITY
            </div>

            <h1>
              Community
            </h1>

            <p>
              Ask questions, share ideas,
              and learn together with
              other learners.
            </p>

          </div>


          <button
            className="community-primary-button"
            onClick={() => {

              setShowForm(
                (value) => !value
              );

              setError("");

            }}
          >

            {showForm
              ? "Close"
              : "+ Ask a Question"}

          </button>

        </div>


        {/* =================================================
            ERROR
        ================================================= */}

        {error && (

          <div className="community-error">

            {error}

          </div>

        )}


        {/* =================================================
            COURSE SELECTOR
        ================================================= */}

        <div className="community-toolbar">

          <div className="community-course-control">

            <label>
              Course
            </label>

            <select
              value={selectedCourse}
              onChange={(event) =>
                setSelectedCourse(
                  event.target.value
                )
              }
              disabled={
                loadingCourses ||
                courses.length === 0
              }
            >

              {loadingCourses && (

                <option value="">
                  Loading courses...
                </option>

              )}

              {!loadingCourses &&
                courses.length === 0 && (

                  <option value="">
                    No courses available
                  </option>

                )}

              {courses.map(
                (course) => (

                  <option
                    key={course.id}
                    value={course.id}
                  >

                    {course.title ||
                      course.name ||
                      course.id}

                  </option>

                )
              )}

            </select>

          </div>


          <div className="community-course-info">

            <span>
              Current course
            </span>

            <strong>
              {selectedCourseName()}
            </strong>

          </div>

        </div>


        {/* =================================================
            ASK QUESTION FORM
        ================================================= */}

        {showForm && (

          <form
            className="community-question-form"
            onSubmit={createDiscussion}
          >

            <div className="form-heading">

              <h2>
                Ask a Question
              </h2>

              <p>
                Select the lesson related
                to your question.
              </p>

            </div>


            {/* LESSON SELECTOR */}

            <div className="community-form-field">

              <label>
                Lesson
              </label>

              <select
                value={selectedLesson}
                onChange={(event) =>
                  setSelectedLesson(
                    event.target.value
                  )
                }
                disabled={
                  lessons.length === 0
                }
              >

                {lessons.length === 0 && (

                  <option value="">
                    No lessons available
                  </option>

                )}

                {lessons.map(
                  (lesson) => (

                    <option
                      key={lesson.id}
                      value={lesson.id}
                    >

                      {lesson.module_title
                        ? `${lesson.module_title} — ${lesson.title}`
                        : lesson.title}

                    </option>

                  )
                )}

              </select>

            </div>


            {/* QUESTION */}

            <div className="community-form-field">

              <label>
                Your Question
              </label>

              <textarea
                value={message}
                onChange={(event) =>
                  setMessage(
                    event.target.value
                  )
                }
                placeholder="Write your question here..."
                rows={6}
                maxLength={5000}
              />

            </div>


            <div className="community-form-footer">

              <span>
                {message.length}/5000
              </span>

              <button
                type="submit"
                className="community-primary-button"
                disabled={
                  posting ||
                  !selectedLesson
                }
              >

                {posting
                  ? "Posting..."
                  : "Post Question"}

              </button>

            </div>

          </form>

        )}


        {/* =================================================
            RECENT DISCUSSIONS
        ================================================= */}

        <section className="community-section">

          <div className="community-section-header">

            <div>

              <h2>
                Recent Discussions
              </h2>

              <p>
                Questions and conversations
                from this course.
              </p>

            </div>


            <button
              className="community-refresh-button"
              onClick={() => {

                if (selectedCourse) {

                  loadCommunity(
                    selectedCourse
                  );

                }

              }}
              disabled={
                loadingCommunity ||
                !selectedCourse
              }
            >

              {loadingCommunity
                ? "Refreshing..."
                : "Refresh"}

            </button>

          </div>


          {/* LOADING */}

          {loadingCommunity && (

            <div className="community-state-card">

              <div className="community-spinner" />

              <h3>
                Loading discussions
              </h3>

              <p>
                Please wait while we
                load the latest questions.
              </p>

            </div>

          )}


          {/* EMPTY */}

          {!loadingCommunity &&
            discussions.length === 0 && (

              <div className="community-empty-card">

                <div className="community-empty-icon">
                  💬
                </div>

                <h3>
                  No discussions yet
                </h3>

                <p>
                  Be the first learner to
                  ask a question about
                  this course.
                </p>

                <button
                  className="community-primary-button"
                  onClick={() => {

                    setShowForm(true);
                    setError("");

                  }}
                  disabled={
                    lessons.length === 0
                  }
                >

                  Ask the First Question

                </button>

              </div>

            )}


          {/* DISCUSSION LIST */}

          {!loadingCommunity &&
            discussions.length > 0 && (

              <div className="community-list">

                {discussions.map(
                  (discussion, index) => (

                    <article
                      className="discussion-card"
                      key={
                        discussion.id ||
                        `discussion-${index}`
                      }
                    >

                      <div className="discussion-avatar">

                        {(discussion.user ||
                          "L")
                          .charAt(0)
                          .toUpperCase()}

                      </div>


                      <div className="discussion-content">

                        <div className="discussion-top">

                          <div>

                            <h3>
                              {discussion.message}
                            </h3>

                            <div className="discussion-meta">

                              <strong>
                                {discussion.user ||
                                  "Learner"}
                              </strong>

                              <span>
                                •
                              </span>

                              <span>
                                {formatDate(
                                  discussion.createdAt
                                )}
                              </span>

                            </div>

                          </div>

                        </div>


                        <div className="discussion-lesson">

                          📚

                          <span>
                            {discussion.module_title
                              ? `${discussion.module_title} → `
                              : ""}

                            {discussion.lesson_title ||
                              lessonName(
                                discussion.lesson_id
                              )}
                          </span>

                        </div>


                        <div className="discussion-footer">

                          <span>
                            Community Question
                          </span>

                          <button
                            className="discussion-view-button"
                            type="button"
                            onClick={() => {

                              setSelectedLesson(
                                discussion.lesson_id
                              );

                              setShowForm(true);

                            }}
                          >

                            Ask Follow-up →

                          </button>

                        </div>

                      </div>

                    </article>

                  )
                )}

              </div>

            )}

        </section>

      </div>


      {/* =================================================
          STYLES
      ================================================= */}

      <style>{`

        .community-page {
          max-width: 1200px;
          margin: 0 auto;
          padding: 10px 0 50px;
        }

        .community-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 30px;
          margin-bottom: 28px;
        }

        .community-eyebrow {
          font-size: 12px;
          font-weight: 800;
          letter-spacing: 1.5px;
          margin-bottom: 8px;
          opacity: 0.65;
        }

        .community-header h1 {
          margin: 0;
          font-size: 34px;
          line-height: 1.2;
        }

        .community-header p {
          margin: 10px 0 0;
          max-width: 650px;
          opacity: 0.7;
          line-height: 1.6;
        }

        .community-primary-button {
          border: none;
          border-radius: 10px;
          padding: 12px 18px;
          font-size: 14px;
          font-weight: 700;
          cursor: pointer;
          background: #111827;
          color: white;
          transition: 0.2s ease;
          white-space: nowrap;
        }

        .community-primary-button:hover {
          transform: translateY(-1px);
          opacity: 0.92;
        }

        .community-primary-button:disabled {
          cursor: not-allowed;
          opacity: 0.55;
          transform: none;
        }

        .community-error {
          margin-bottom: 20px;
          padding: 13px 16px;
          border-radius: 10px;
          background: #fef2f2;
          border: 1px solid #fecaca;
          color: #991b1b;
          font-size: 14px;
        }

        .community-toolbar {
          display: flex;
          align-items: flex-end;
          gap: 25px;
          padding: 18px;
          border-radius: 14px;
          border: 1px solid #e5e7eb;
          background: white;
          margin-bottom: 20px;
        }

        .community-course-control {
          width: 100%;
          max-width: 420px;
        }

        .community-course-control label,
        .community-form-field label {
          display: block;
          margin-bottom: 8px;
          font-size: 13px;
          font-weight: 700;
        }

        .community-course-control select,
        .community-form-field select {
          width: 100%;
          padding: 12px 13px;
          border: 1px solid #d1d5db;
          border-radius: 9px;
          background: white;
          font-size: 14px;
          outline: none;
          box-sizing: border-box;
        }

        .community-course-control select:focus,
        .community-form-field select:focus {
          border-color: #6b7280;
        }

        .community-course-info {
          display: flex;
          flex-direction: column;
          gap: 5px;
          font-size: 12px;
          opacity: 0.65;
        }

        .community-course-info strong {
          color: #111827;
          font-size: 14px;
          opacity: 1;
        }

        .community-question-form {
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 14px;
          padding: 22px;
          margin-bottom: 25px;
        }

        .form-heading h2 {
          margin: 0;
          font-size: 20px;
        }

        .form-heading p {
          margin: 6px 0 18px;
          opacity: 0.65;
          font-size: 14px;
        }

        .community-form-field {
          margin-bottom: 18px;
        }

        .community-form-field textarea {
          width: 100%;
          box-sizing: border-box;
          resize: vertical;
          padding: 14px;
          border-radius: 10px;
          border: 1px solid #d1d5db;
          font-family: inherit;
          font-size: 14px;
          line-height: 1.6;
          outline: none;
        }

        .community-form-field textarea:focus {
          border-color: #6b7280;
        }

        .community-form-footer {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 20px;
          margin-top: 14px;
        }

        .community-form-footer span {
          font-size: 12px;
          opacity: 0.55;
        }

        .community-section {
          margin-top: 25px;
        }

        .community-section-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 20px;
          margin-bottom: 18px;
        }

        .community-section-header h2 {
          margin: 0;
          font-size: 22px;
        }

        .community-section-header p {
          margin: 5px 0 0;
          font-size: 14px;
          opacity: 0.65;
        }

        .community-refresh-button {
          border: 1px solid #d1d5db;
          background: white;
          border-radius: 9px;
          padding: 9px 14px;
          cursor: pointer;
          font-weight: 700;
        }

        .community-refresh-button:disabled {
          cursor: not-allowed;
          opacity: 0.55;
        }

        .community-state-card,
        .community-empty-card {
          min-height: 220px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-direction: column;
          text-align: center;
          border: 1px solid #e5e7eb;
          border-radius: 14px;
          background: white;
          padding: 30px;
        }

        .community-state-card h3,
        .community-empty-card h3 {
          margin: 12px 0 6px;
        }

        .community-state-card p,
        .community-empty-card p {
          margin: 0 0 18px;
          opacity: 0.65;
        }

        .community-empty-icon {
          font-size: 40px;
        }

        .community-spinner {
          width: 28px;
          height: 28px;
          border: 3px solid #e5e7eb;
          border-top-color: #111827;
          border-radius: 50%;
          animation: community-spin 0.8s linear infinite;
        }

        @keyframes community-spin {
          to {
            transform: rotate(360deg);
          }
        }

        .community-list {
          display: flex;
          flex-direction: column;
          gap: 14px;
        }

        .discussion-card {
          display: flex;
          gap: 16px;
          padding: 20px;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 14px;
          transition: 0.2s ease;
        }

        .discussion-card:hover {
          border-color: #cbd5e1;
          transform: translateY(-1px);
        }

        .discussion-avatar {
          flex: 0 0 44px;
          width: 44px;
          height: 44px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f3f4f6;
          font-weight: 800;
          font-size: 16px;
        }

        .discussion-content {
          flex: 1;
          min-width: 0;
        }

        .discussion-top h3 {
          margin: 0;
          font-size: 16px;
          line-height: 1.5;
          font-weight: 600;
        }

        .discussion-meta {
          display: flex;
          gap: 7px;
          flex-wrap: wrap;
          margin-top: 5px;
          font-size: 12px;
          opacity: 0.6;
        }

        .discussion-lesson {
          display: inline-flex;
          gap: 7px;
          align-items: center;
          margin-top: 14px;
          padding: 8px 10px;
          border-radius: 8px;
          background: #f8fafc;
          font-size: 12px;
          font-weight: 600;
        }

        .discussion-footer {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 15px;
          margin-top: 15px;
          font-size: 13px;
          opacity: 0.7;
        }

        .discussion-view-button {
          border: none;
          background: transparent;
          font-weight: 700;
          cursor: pointer;
          padding: 5px;
        }

        @media (max-width: 700px) {

          .community-header {
            flex-direction: column;
          }

          .community-primary-button {
            width: 100%;
          }

          .community-toolbar {
            flex-direction: column;
            align-items: stretch;
          }

          .community-course-control {
            max-width: none;
          }

          .community-section-header {
            align-items: flex-start;
            flex-direction: column;
          }

          .discussion-card {
            padding: 15px;
          }

        }

      `}</style>

    </DashboardLayout>

  );
}