import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest } from '../services/api'
import './TrainerCodingExams.css'
import { useNotification } from '../context/NotificationContext'

// =========================================================
// TRAINER CODING EXAMS
// =========================================================

export default function TrainerCodingExams() {

  const navigate = useNavigate()
  const { showNotification } = useNotification()

  // -------------------------------------------------------
  // DATA
  // -------------------------------------------------------

  const [exams, setExams] = useState([])
  const [courses, setCourses] = useState([])

  // -------------------------------------------------------
  // UI STATE
  // -------------------------------------------------------

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState(null)

  // -------------------------------------------------------
  // MODALS
  // -------------------------------------------------------

  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)

  // -------------------------------------------------------
  // FORM
  // -------------------------------------------------------

  const emptyForm = {
    title: '',
    description: '',
    course_id: '',
    duration: 60,
    status: 'draft',
  }

  const [form, setForm] = useState(emptyForm)
  const [editingExam, setEditingExam] = useState(null)

  // =======================================================
  // LOAD EXAMS
  // =======================================================

  async function loadExams() {

    try {

      setLoading(true)
      setError('')

      const data = await apiRequest(
        '/api/trainer/coding-exams'
      )

      const examList =
        Array.isArray(data)
          ? data
          : (
              data?.exams ||
              data?.coding_exams ||
              []
            )

      setExams(examList)

    } catch (err) {

      console.error(err)

      setError(
        err.message ||
        'Failed to load coding exams'
      )

    } finally {

      setLoading(false)
    }
  }


  // =======================================================
  // LOAD TRAINER COURSES
  // =======================================================

  async function loadCourses() {

    try {

      const data = await apiRequest(
        '/api/trainer/courses'
      )

      const courseList =
        Array.isArray(data)
          ? data
          : (
              data?.courses ||
              []
            )

      setCourses(courseList)

    } catch (err) {

      console.error(
        'Failed to load courses:',
        err
      )
    }
  }


  // =======================================================
  // INITIAL LOAD
  // =======================================================

  useEffect(() => {

    loadExams()
    loadCourses()

  }, [])


  // =======================================================
  // STATISTICS
  // =======================================================

  const statistics = useMemo(() => {

    const totalExams = exams.length

    const totalQuestions = exams.reduce(
      (sum, exam) =>
        sum +
        Number(
          exam.question_count ??
          exam.questions ??
          0
        ),
      0
    )

    const totalAttempts = exams.reduce(
      (sum, exam) =>
        sum +
        Number(
          exam.attempt_count ??
          exam.attempts ??
          0
        ),
      0
    )

    return {
      totalExams,
      totalQuestions,
      totalAttempts,
    }

  }, [exams])


  // =======================================================
  // FORM CHANGE
  // =======================================================

  function handleChange(event) {

    const {
      name,
      value,
    } = event.target

    setForm(previous => ({
      ...previous,
      [name]:
        name === 'duration'
          ? value
          : value,
    }))
  }


  // =======================================================
  // OPEN CREATE
  // =======================================================

  function openCreateModal() {

    setEditingExam(null)

    setForm({
      ...emptyForm,
      course_id:
        courses.length > 0
          ? courses[0].id
          : '',
    })

    setShowCreateModal(true)
  }


  // =======================================================
  // OPEN EDIT
  // =======================================================

  function openEditModal(exam) {

    setEditingExam(exam)

    setForm({
      title: exam.title || '',
      description: exam.description || '',
      course_id: exam.course_id || '',
      duration:
        exam.duration ||
        60,
      status:
        String(
          exam.status || 'draft'
        ).toLowerCase(),
    })

    setShowEditModal(true)
  }


  // =======================================================
  // CLOSE MODALS
  // =======================================================

  function closeModal() {

    if (saving) {
      return
    }

    setShowCreateModal(false)
    setShowEditModal(false)
    setEditingExam(null)
    setForm(emptyForm)
  }


  // =======================================================
  // CREATE EXAM
  // =======================================================

  async function handleCreateExam(event) {

    event.preventDefault()

    if (!form.title.trim()) {

      alert(
        'Please enter an exam title.'
      )

      return
    }

    if (!form.course_id) {

      alert(
        'Please select a course.'
      )

      return
    }

    try {

      setSaving(true)

      const response = await apiRequest(
        '/api/trainer/coding-exams',
        {
          method: 'POST',
          body: JSON.stringify({
            title: form.title.trim(),
            description:
              form.description.trim(),
            course_id:
              form.course_id,
            duration:
              Number(form.duration),
            status:
              form.status,
          }),
        }
      )

      const createdExam =
        response?.exam

      if (createdExam) {

        setExams(previous => [
          createdExam,
          ...previous,
        ])

      } else {

        await loadExams()
      }

      closeModal()

    } catch (err) {

      console.error(err)

      showNotification(
        err.message ||
        'Failed to create coding exam.'
      )

    } finally {

      setSaving(false)
    }
  }


  // =======================================================
  // UPDATE EXAM
  // =======================================================

  async function handleUpdateExam(event) {

    event.preventDefault()

    if (!editingExam) {
      return
    }

    if (!form.title.trim()) {

      alert(
        'Please enter an exam title.'
      )

      return
    }

    if (!form.course_id) {

      alert(
        'Please select a course.'
      )

      return
    }

    try {

      setSaving(true)

      const response = await apiRequest(
        `/api/trainer/coding-exams/${editingExam.id}`,
        {
          method: 'PUT',
          body: JSON.stringify({
            title: form.title.trim(),
            description:
              form.description.trim(),
            duration:
              Number(form.duration),
            status:
              form.status,
            course_id:
              form.course_id,
          }),
        }
      )

      const updatedExam =
        response?.exam

      if (updatedExam) {

        setExams(previous =>
          previous.map(exam =>
            exam.id === updatedExam.id
              ? {
                  ...exam,
                  ...updatedExam,
                }
              : exam
          )
        )

      } else {

        await loadExams()
      }

      closeModal()

    } catch (err) {

      console.error(err)

      showNotification(
        err.message ||
        'Failed to update coding exam.'
      )

    } finally {

      setSaving(false)
    }
  }


  // =======================================================
  // DELETE EXAM
  // =======================================================

  async function handleDeleteExam(exam) {

    const confirmed = window.confirm(
      `Delete "${exam.title}"?\n\nThis will also remove its coding questions and related data.`
    )

    if (!confirmed) {
      return
    }

    try {

      setDeletingId(exam.id)

      await apiRequest(
        `/api/trainer/coding-exams/${exam.id}`,
        {
          method: 'DELETE',
        }
      )

      setExams(previous =>
        previous.filter(
          item =>
            item.id !== exam.id
        )
      )

    } catch (err) {

      console.error(err)

      showNotification(
        err.message ||
        'Failed to delete coding exam.'
      )

    } finally {

      setDeletingId(null)
    }
  }


  // =======================================================
  // TOGGLE PUBLISH STATUS
  // =======================================================

  async function togglePublish(exam) {

    const currentStatus =
      String(
        exam.status || 'draft'
      ).toLowerCase()

    const newStatus =
      currentStatus === 'published'
        ? 'draft'
        : 'published'

    const actionText =
      newStatus === 'published'
        ? 'publish'
        : 'move back to draft'

    const confirmed = window.confirm(
      `Are you sure you want to ${actionText} "${exam.title}"?`
    )

    if (!confirmed) {
      return
    }

    try {

      const response = await apiRequest(
        `/api/trainer/coding-exams/${exam.id}`,
        {
          method: 'PUT',
          body: JSON.stringify({
            status: newStatus,
          }),
        }
      )

      const updatedExam =
        response?.exam

      if (updatedExam) {

        setExams(previous =>
          previous.map(item =>
            item.id === updatedExam.id
              ? {
                  ...item,
                  ...updatedExam,
                }
              : item
          )
        )

      } else {

        await loadExams()
      }

    } catch (err) {

      console.error(err)

      showNotification(
        err.message ||
        'Failed to update exam status.'
      )
    }
  }


  // =======================================================
  // COURSE NAME
  // =======================================================

  function getCourseName(exam) {

    const course =
      courses.find(
        item =>
          String(item.id) ===
          String(exam.course_id)
      )

    if (course) {
      return (
        course.title ||
        course.name ||
        exam.course_id ||
        'Course'
      )
    }

    return (
      exam.course_title ||
      exam.course_name ||
      exam.course_id ||
      'Course'
    )
  }


  // =======================================================
  // LOADING
  // =======================================================

  if (loading) {

    return (
      <div className="trainer-coding-page">

        <div className="trainer-coding-loading">
          Loading coding exams...
        </div>

      </div>
    )
  }


  // =======================================================
  // PAGE
  // =======================================================

  return (

    <div className="trainer-coding-page">

      {/* =================================================
          HEADER
      ================================================= */}

      <div className="trainer-coding-header">

        <div>

          <h1>
            Coding Exams
          </h1>

          <p>
            Create and manage coding assessments
            for your learners.
          </p>

        </div>

        <button
          className="trainer-coding-primary-button"
          onClick={openCreateModal}
        >
          + Create Coding Exam
        </button>

      </div>


      {/* =================================================
          ERROR
      ================================================= */}

      {error && (

        <div className="trainer-coding-error">
          {error}
        </div>

      )}


      {/* =================================================
          STATISTICS
      ================================================= */}

      <div className="trainer-coding-stats">

        <div className="trainer-coding-stat-card">

          <div className="trainer-coding-stat-icon">
            💻
          </div>

          <div>

            <strong>
              {statistics.totalExams}
            </strong>

            <span>
              Total Coding Exams
            </span>

          </div>

        </div>


        <div className="trainer-coding-stat-card">

          <div className="trainer-coding-stat-icon">
            📝
          </div>

          <div>

            <strong>
              {statistics.totalQuestions}
            </strong>

            <span>
              Total Questions
            </span>

          </div>

        </div>


        <div className="trainer-coding-stat-card">

          <div className="trainer-coding-stat-icon">
            👥
          </div>

          <div>

            <strong>
              {statistics.totalAttempts}
            </strong>

            <span>
              Total Attempts
            </span>

          </div>

        </div>

      </div>


      {/* =================================================
          EXAMS
      ================================================= */}

      <section className="trainer-coding-section">

        <div className="trainer-coding-section-header">

          <div>

            <h2>
              Your Coding Exams
            </h2>

            <p>
              Manage your coding assessments
              and questions.
            </p>

          </div>

        </div>


        {exams.length === 0 ? (

          <div className="trainer-coding-empty">

            <div className="trainer-coding-empty-icon">
              💻
            </div>

            <h3>
              No coding exams yet
            </h3>

            <p>
              Create your first coding exam
              to get started.
            </p>

            <button
              className="trainer-coding-primary-button"
              onClick={openCreateModal}
            >
              + Create Coding Exam
            </button>

          </div>

        ) : (

          <div className="trainer-coding-exam-list">

            {exams.map(exam => {

              const status =
                String(
                  exam.status ||
                  'draft'
                ).toLowerCase()

              const questionCount =
                exam.question_count ??
                exam.questions ??
                0

              const attempts =
                exam.attempt_count ??
                exam.attempts ??
                0

              const duration =
                exam.duration ||
                60

              return (

                <div
                  key={exam.id}
                  className="trainer-coding-exam-card"
                >

                  {/* ---------------------------------------
                      EXAM HEADER
                  --------------------------------------- */}

                  <div className="trainer-coding-exam-top">

                    <div className="trainer-coding-exam-title-area">

                      <div className="trainer-coding-exam-icon">
                        💻
                      </div>

                      <div>

                        <h3>
                          {exam.title}
                        </h3>

                        <p>
                          {getCourseName(exam)}
                        </p>

                      </div>

                    </div>


                    <span
                      className={
                        status === 'published'
                          ? 'status published'
                          : 'status draft'
                      }
                    >
                      {status}
                    </span>

                  </div>


                  {/* ---------------------------------------
                      DESCRIPTION
                  --------------------------------------- */}

                  <p className="trainer-coding-exam-description">

                    {exam.description
                      ? exam.description
                      : 'No description provided.'}

                  </p>


                  {/* ---------------------------------------
                      DETAILS
                  --------------------------------------- */}

                  <div className="trainer-coding-exam-details">

                    <div>

                      <span>
                        Questions
                      </span>

                      <strong>
                        {questionCount}
                      </strong>

                    </div>


                    <div>

                      <span>
                        Duration
                      </span>

                      <strong>
                        {duration} min
                      </strong>

                    </div>


                    <div>

                      <span>
                        Attempts
                      </span>

                      <strong>
                        {attempts}
                      </strong>

                    </div>

                  </div>


                  {/* ---------------------------------------
                      ACTIONS
                  --------------------------------------- */}

                  <div className="trainer-coding-exam-actions">

                    <button
                      className="trainer-coding-primary-button small"
                      onClick={() =>
                        navigate(
                          `/trainer/coding-exams/${exam.id}/questions`
                        )
                      }
                    >
                      Manage Questions
                    </button>


                    <button
                      className="trainer-coding-secondary-button"
                      onClick={() =>
                        navigate(
                          `/trainer/coding-exams/${exam.id}/results`
                        )
                      }
                    >
                      Results
                    </button>


                    <button
                      className="trainer-coding-secondary-button"
                      onClick={() =>
                        openEditModal(exam)
                      }
                    >
                      Edit
                    </button>


                    <button
                      className={
                        status === 'published'
                          ? 'trainer-coding-warning-button'
                          : 'trainer-coding-publish-button'
                      }
                      onClick={() =>
                        togglePublish(exam)
                      }
                    >
                      {status === 'published'
                        ? 'Unpublish'
                        : 'Publish'}
                    </button>


                    <button
                      className="trainer-coding-delete-button"
                      onClick={() =>
                        handleDeleteExam(exam)
                      }
                      disabled={
                        deletingId === exam.id
                      }
                    >
                      {deletingId === exam.id
                        ? 'Deleting...'
                        : 'Delete'}
                    </button>

                  </div>

                </div>

              )
            })}

          </div>

        )}

      </section>


      {/* =================================================
          CREATE MODAL
      ================================================= */}

      {showCreateModal && (

        <div
          className="trainer-coding-modal-overlay"
          onMouseDown={event => {

            if (
              event.target ===
              event.currentTarget
            ) {
              closeModal()
            }

          }}
        >

          <div className="trainer-coding-modal">

            <div className="trainer-coding-modal-header">

              <div>

                <h2>
                  Create Coding Exam
                </h2>

                <p>
                  Create a new coding assessment.
                </p>

              </div>

              <button
                className="trainer-coding-modal-close"
                onClick={closeModal}
              >
                ×
              </button>

            </div>


            <form
              onSubmit={handleCreateExam}
              className="trainer-coding-form"
            >

              <div className="trainer-coding-form-group">

                <label>
                  Exam Title
                </label>

                <input
                  type="text"
                  name="title"
                  value={form.title}
                  onChange={handleChange}
                  placeholder="Example: Python Programming Assessment"
                  required
                />

              </div>


              <div className="trainer-coding-form-group">

                <label>
                  Course
                </label>

                <select
                  name="course_id"
                  value={form.course_id}
                  onChange={handleChange}
                  required
                >

                  <option value="">
                    Select a course
                  </option>

                  {courses.map(course => (

                    <option
                      key={course.id}
                      value={course.id}
                    >
                      {course.title ||
                        course.name ||
                        course.id}
                    </option>

                  ))}

                </select>

              </div>


              <div className="trainer-coding-form-group">

                <label>
                  Description
                </label>

                <textarea
                  name="description"
                  value={form.description}
                  onChange={handleChange}
                  placeholder="Describe what learners will be tested on."
                  rows="4"
                />

              </div>


              <div className="trainer-coding-form-row">

                <div className="trainer-coding-form-group">

                  <label>
                    Duration (minutes)
                  </label>

                  <input
                    type="number"
                    name="duration"
                    value={form.duration}
                    onChange={handleChange}
                    min="1"
                    required
                  />

                </div>


                <div className="trainer-coding-form-group">

                  <label>
                    Status
                  </label>

                  <select
                    name="status"
                    value={form.status}
                    onChange={handleChange}
                  >

                    <option value="draft">
                      Draft
                    </option>

                    <option value="published">
                      Published
                    </option>

                  </select>

                </div>

              </div>


              <div className="trainer-coding-modal-actions">

                <button
                  type="button"
                  className="trainer-coding-secondary-button"
                  onClick={closeModal}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="trainer-coding-primary-button"
                  disabled={saving}
                >
                  {saving
                    ? 'Creating...'
                    : 'Create Coding Exam'}
                </button>

              </div>

            </form>

          </div>

        </div>

      )}


      {/* =================================================
          EDIT MODAL
      ================================================= */}

      {showEditModal && (

        <div
          className="trainer-coding-modal-overlay"
          onMouseDown={event => {

            if (
              event.target ===
              event.currentTarget
            ) {
              closeModal()
            }

          }}
        >

          <div className="trainer-coding-modal">

            <div className="trainer-coding-modal-header">

              <div>

                <h2>
                  Edit Coding Exam
                </h2>

                <p>
                  Update exam details and publishing status.
                </p>

              </div>

              <button
                className="trainer-coding-modal-close"
                onClick={closeModal}
              >
                ×
              </button>

            </div>


            <form
              onSubmit={handleUpdateExam}
              className="trainer-coding-form"
            >

              <div className="trainer-coding-form-group">

                <label>
                  Exam Title
                </label>

                <input
                  type="text"
                  name="title"
                  value={form.title}
                  onChange={handleChange}
                  required
                />

              </div>


              <div className="trainer-coding-form-group">

                <label>
                  Course
                </label>

                <select
                  name="course_id"
                  value={form.course_id}
                  onChange={handleChange}
                  required
                >

                  {courses.map(course => (

                    <option
                      key={course.id}
                      value={course.id}
                    >
                      {course.title ||
                        course.name ||
                        course.id}
                    </option>

                  ))}

                </select>

              </div>


              <div className="trainer-coding-form-group">

                <label>
                  Description
                </label>

                <textarea
                  name="description"
                  value={form.description}
                  onChange={handleChange}
                  rows="4"
                />

              </div>


              <div className="trainer-coding-form-row">

                <div className="trainer-coding-form-group">

                  <label>
                    Duration (minutes)
                  </label>

                  <input
                    type="number"
                    name="duration"
                    value={form.duration}
                    onChange={handleChange}
                    min="1"
                    required
                  />

                </div>


                <div className="trainer-coding-form-group">

                  <label>
                    Status
                  </label>

                  <select
                    name="status"
                    value={form.status}
                    onChange={handleChange}
                  >

                    <option value="draft">
                      Draft
                    </option>

                    <option value="published">
                      Published
                    </option>

                  </select>

                </div>

              </div>


              {/* -----------------------------------------
                  PUBLISHING INFORMATION
              ----------------------------------------- */}

              <div className="trainer-coding-publish-info">

                <strong>
                  Publishing status
                </strong>

                {form.status === 'published' ? (

                  <p>
                    This exam will be visible to
                    enrolled learners.
                  </p>

                ) : (

                  <p>
                    This exam will remain hidden
                    from learners until published.
                  </p>

                )}

              </div>


              <div className="trainer-coding-modal-actions">

                <button
                  type="button"
                  className="trainer-coding-secondary-button"
                  onClick={closeModal}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="trainer-coding-primary-button"
                  disabled={saving}
                >
                  {saving
                    ? 'Saving...'
                    : 'Save Changes'}
                </button>

              </div>

            </form>

          </div>

        </div>

      )}

    </div>
  )
}