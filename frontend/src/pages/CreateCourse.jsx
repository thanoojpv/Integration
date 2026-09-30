import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import { apiRequest } from '../services/api'
import { useNotification } from '../context/NotificationContext'

const STEPS = [
  'Basic Info',
  'Curriculum Builder',
  'Publish & Preview'
]

export default function CreateCourse() {

  const navigate = useNavigate()
  const { showNotification } = useNotification()

  // =====================================================
  // STEP
  // =====================================================

  const [step, setStep] = useState(0)

  // =====================================================
  // COURSE FORM
  // =====================================================

  const [courseId, setCourseId] = useState('')
  const [courseTitle, setCourseTitle] = useState('')
  const [level, setLevel] = useState('Beginner')
  const [description, setDescription] = useState('')

  // =====================================================
  // CREATED COURSE
  // =====================================================

  const [createdCourse, setCreatedCourse] = useState(null)

  // =====================================================
  // MODULES
  // =====================================================

  const [modules, setModules] = useState([])

  const [newModuleTitle, setNewModuleTitle] = useState('')
  const [addingModule, setAddingModule] = useState(false)

  // =====================================================
  // LESSON FORM
  // =====================================================

  const [activeModuleId, setActiveModuleId] = useState(null)

  const [lessonId, setLessonId] = useState('')
  const [lessonTitle, setLessonTitle] = useState('')
  const [lessonContent, setLessonContent] = useState('')
  const [lessonDuration, setLessonDuration] = useState('00:00')

  const [addingLesson, setAddingLesson] = useState(false)

  // =====================================================
  // GENERAL STATE
  // =====================================================

  const [savingCourse, setSavingCourse] = useState(false)
  const [error, setError] = useState('')

  // =====================================================
  // CREATE COURSE
  // =====================================================

  async function createCourse() {

    setError('')

    if (!courseId.trim()) {
      setError('Please enter a Course ID.')
      return
    }

    if (!courseTitle.trim()) {
      setError('Please enter a Course Title.')
      return
    }

    try {

      setSavingCourse(true)

      const data = await apiRequest(
        '/api/trainer/courses',
        {
          method: 'POST',
          body: JSON.stringify({
            id: courseId.trim(),
            title: courseTitle.trim(),
            level,
            description: description.trim(),
            published: false
          })
        }
      )

      console.log('COURSE CREATED:', data)

      setCreatedCourse(data.course)

      setStep(1)

    } catch (err) {

      console.error(
        'Course creation error:',
        err
      )

      setError(
        err.message ||
        'Unable to create course'
      )

    } finally {

      setSavingCourse(false)

    }
  }

  // =====================================================
  // CREATE MODULE
  // =====================================================

  async function addModule() {

    if (!createdCourse) {
      return
    }

    if (!newModuleTitle.trim()) {
      setError('Please enter a module name.')
      return
    }

    try {

      setAddingModule(true)
      setError('')

      const data = await apiRequest(
        `/api/trainer/courses/${createdCourse.id}/modules`,
        {
          method: 'POST',
          body: JSON.stringify({
            title: newModuleTitle.trim(),
            order_no: modules.length + 1
          })
        }
      )

      console.log(
        'MODULE CREATED:',
        data
      )

      const newModule = {
        id: data.module.id,
        title: data.module.title,
        order_no: data.module.order_no,
        lessons: []
      }

      setModules((currentModules) => [
        ...currentModules,
        newModule
      ])

      setNewModuleTitle('')

    } catch (err) {

      console.error(
        'Module creation error:',
        err
      )

      setError(
        err.message ||
        'Unable to create module'
      )

    } finally {

      setAddingModule(false)

    }
  }

  // =====================================================
  // OPEN LESSON FORM
  // =====================================================

  function openLessonForm(moduleId) {

    setActiveModuleId(moduleId)

    setLessonId('')
    setLessonTitle('')
    setLessonContent('')
    setLessonDuration('00:00')

    setError('')
  }

  // =====================================================
  // CANCEL LESSON FORM
  // =====================================================

  function cancelLessonForm() {

    setActiveModuleId(null)

    setLessonId('')
    setLessonTitle('')
    setLessonContent('')
    setLessonDuration('00:00')
  }

  // =====================================================
  // CREATE LESSON
  // =====================================================

  async function addLesson(moduleId) {

    if (!lessonId.trim()) {
      setError('Please enter a Lesson ID.')
      return
    }

    if (!lessonTitle.trim()) {
      setError('Please enter a Lesson Title.')
      return
    }

    try {

      setAddingLesson(true)
      setError('')

      const data = await apiRequest(
        `/api/trainer/modules/${moduleId}/lessons`,
        {
          method: 'POST',
          body: JSON.stringify({
            id: lessonId.trim(),
            title: lessonTitle.trim(),
            content: lessonContent.trim(),
            duration: lessonDuration.trim() || '00:00',
            order_no:
              (
                modules.find(
                  (module) => module.id === moduleId
                )?.lessons?.length || 0
              ) + 1
          })
        }
      )

      console.log(
        'LESSON CREATED:',
        data
      )

      const createdLesson = data.lesson

      setModules((currentModules) =>
        currentModules.map((module) => {

          if (module.id !== moduleId) {
            return module
          }

          return {
            ...module,
            lessons: [
              ...(module.lessons || []),
              {
                id: createdLesson.id,
                title: createdLesson.title,
                duration: createdLesson.duration
              }
            ]
          }

        })
      )

      cancelLessonForm()

    } catch (err) {

      console.error(
        'Lesson creation error:',
        err
      )

      setError(
        err.message ||
        'Unable to create lesson'
      )

    } finally {

      setAddingLesson(false)

    }
  }

  // =====================================================
  // PUBLISH COURSE
  // =====================================================

  async function publishCourse() {

    if (!createdCourse) {
      return
    }

    try {

      setSavingCourse(true)
      setError('')

      await apiRequest(
        `/api/trainer/courses/${createdCourse.id}`,
        {
          method: 'PUT',
          body: JSON.stringify({
            published: true
          })
        }
      )

      showNotification(
        'Course published successfully!',
        'success'
      )

      navigate(
        `/trainer/course/${createdCourse.id}`
      )

    } catch (err) {

      console.error(
        'Course publishing error:',
        err
      )

      setError(
        err.message ||
        'Unable to publish course'
      )

    } finally {

      setSavingCourse(false)

    }
  }

  // =====================================================
  // RENDER
  // =====================================================

  return (

    <DashboardLayout role="trainer">

      <div
        className="card"
        style={{
          padding: 26
        }}
      >

        {/* =================================================
            HEADER
        ================================================= */}

        <h2
          style={{
            marginTop: 0,
            marginBottom: 4
          }}
        >
          Create New Course
        </h2>

        <p
          className="subtitle"
          style={{
            marginBottom: 24
          }}
        >
          Create your own course, modules and lessons.
        </p>


        {/* =================================================
            WIZARD STEPS
        ================================================= */}

        <div className="wizard-steps">

          {STEPS.map((label, i) => (

            <div
              key={label}
              className={
                'wizard-step' +
                (
                  i === step
                    ? ' active'
                    : i < step
                      ? ' done'
                      : ''
                )
              }
            >

              <span className="num">

                {i < step
                  ? '✓'
                  : i + 1}

              </span>

              {label}

            </div>

          ))}

        </div>


        {/* =================================================
            ERROR
        ================================================= */}

        {error && (

          <div
            style={{
              marginTop: 20,
              padding: 12,
              borderRadius: 8,
              background: '#fff1f1',
              color: '#b42318',
              border: '1px solid #f5c2c0'
            }}
          >
            {error}
          </div>

        )}


        {/* =================================================
            STEP 1
        ================================================= */}

        {step === 0 && (

          <div>

            <h3
              style={{
                fontSize: 15
              }}
            >
              Step 1: Basic Information
            </h3>


            {/* COURSE ID */}

            <div className="field">

              <label>
                Course ID
              </label>

              <input
                value={courseId}
                onChange={(e) =>
                  setCourseId(e.target.value)
                }
                placeholder="e.g. python-course"
              />

              <small
                style={{
                  color: 'var(--text-500)',
                  display: 'block',
                  marginTop: 5
                }}
              >
                Use a unique ID without spaces.
              </small>

            </div>


            {/* COURSE TITLE */}

            <div className="field">

              <label>
                Course Title
              </label>

              <input
                value={courseTitle}
                onChange={(e) =>
                  setCourseTitle(e.target.value)
                }
                placeholder="e.g. Python Programming"
              />

            </div>


            {/* LEVEL */}

            <div className="field">

              <label>
                Difficulty Level
              </label>

              <select
                value={level}
                onChange={(e) =>
                  setLevel(e.target.value)
                }
              >

                <option value="Beginner">
                  Beginner
                </option>

                <option value="Intermediate">
                  Intermediate
                </option>

                <option value="Advanced">
                  Advanced
                </option>

              </select>

            </div>


            {/* DESCRIPTION */}

            <div className="field">

              <label>
                Course Description
              </label>

              <textarea
                rows={4}
                value={description}
                onChange={(e) =>
                  setDescription(e.target.value)
                }
                placeholder="Describe what learners will learn..."
              />

            </div>

          </div>

        )}


        {/* =================================================
            STEP 2
        ================================================= */}

        {step === 1 && (

          <div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: 12,
                flexWrap: 'wrap'
              }}
            >

              <div>

                <h3
                  style={{
                    fontSize: 15,
                    marginBottom: 4
                  }}
                >
                  Step 2: Build Your Curriculum
                </h3>

                <p
                  style={{
                    fontSize: 13,
                    color: 'var(--text-500)'
                  }}
                >
                  Create your own modules and lessons.
                </p>

              </div>

            </div>


            {/* =================================================
                ADD MODULE
            ================================================= */}

            <div
              className="card"
              style={{
                padding: 16,
                marginTop: 18,
                marginBottom: 18
              }}
            >

              <h4
                style={{
                  marginTop: 0
                }}
              >
                Create Module
              </h4>

              <div
                style={{
                  display: 'flex',
                  gap: 10,
                  alignItems: 'end',
                  flexWrap: 'wrap'
                }}
              >

                <div
                  className="field"
                  style={{
                    flex: 1,
                    minWidth: 250,
                    marginBottom: 0
                  }}
                >

                  <label>
                    Module Name
                  </label>

                  <input
                    value={newModuleTitle}
                    onChange={(e) =>
                      setNewModuleTitle(e.target.value)
                    }
                    placeholder="e.g. Python Basics"
                  />

                </div>

                <button
                  className="btn btn-primary"
                  onClick={addModule}
                  disabled={addingModule}
                >
                  {addingModule
                    ? 'Creating...'
                    : '+ Create Module'}
                </button>

              </div>

            </div>


            {/* =================================================
                MODULE LIST
            ================================================= */}

            {modules.length === 0 ? (

              <div
                style={{
                  padding: 25,
                  textAlign: 'center',
                  border: '1px dashed var(--border)',
                  borderRadius: 10,
                  color: 'var(--text-500)'
                }}
              >

                <div
                  style={{
                    fontSize: 30,
                    marginBottom: 8
                  }}
                >
                  📚
                </div>

                <strong>
                  No modules yet
                </strong>

                <p
                  style={{
                    fontSize: 13
                  }}
                >
                  Create your first module above.
                </p>

              </div>

            ) : (

              modules.map((module, index) => (

                <div
                  key={module.id}
                  className="card"
                  style={{
                    padding: 18,
                    marginBottom: 15
                  }}
                >

                  {/* MODULE HEADER */}

                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      gap: 10,
                      flexWrap: 'wrap'
                    }}
                  >

                    <div>

                      <div
                        style={{
                          fontSize: 12,
                          color: 'var(--text-500)',
                          marginBottom: 4
                        }}
                      >
                        Module {index + 1}
                      </div>

                      <h3
                        style={{
                          margin: 0,
                          fontSize: 16
                        }}
                      >
                        {module.title}
                      </h3>

                    </div>


                    <button
                      className="btn btn-outline"
                      onClick={() =>
                        openLessonForm(module.id)
                      }
                    >
                      + Add Lesson
                    </button>

                  </div>


                  {/* =================================================
                      LESSON FORM
                  ================================================= */}

                  {activeModuleId === module.id && (

                    <div
                      style={{
                        marginTop: 16,
                        padding: 16,
                        borderRadius: 10,
                        border: '1px solid var(--border)'
                      }}
                    >

                      <h4
                        style={{
                          marginTop: 0
                        }}
                      >
                        Create Lesson
                      </h4>


                      {/* LESSON ID */}

                      <div className="field">

                        <label>
                          Lesson ID
                        </label>

                        <input
                          value={lessonId}
                          onChange={(e) =>
                            setLessonId(e.target.value)
                          }
                          placeholder="e.g. python-introduction"
                        />

                      </div>


                      {/* LESSON TITLE */}

                      <div className="field">

                        <label>
                          Lesson Title
                        </label>

                        <input
                          value={lessonTitle}
                          onChange={(e) =>
                            setLessonTitle(e.target.value)
                          }
                          placeholder="e.g. Introduction to Python"
                        />

                      </div>


                      {/* LESSON CONTENT */}

                      <div className="field">

                        <label>
                          Lesson Description / Content
                        </label>

                        <textarea
                          rows={3}
                          value={lessonContent}
                          onChange={(e) =>
                            setLessonContent(e.target.value)
                          }
                          placeholder="Explain what this lesson covers..."
                        />

                      </div>


                      {/* DURATION */}

                      <div className="field">

                        <label>
                          Duration
                        </label>

                        <input
                          value={lessonDuration}
                          onChange={(e) =>
                            setLessonDuration(e.target.value)
                          }
                          placeholder="e.g. 12:35"
                        />

                        <small
                          style={{
                            color: 'var(--text-500)',
                            display: 'block',
                            marginTop: 5
                          }}
                        >
                          Enter duration as MM:SS or HH:MM:SS.
                        </small>

                      </div>


                      {/* LESSON BUTTONS */}

                      <div
                        style={{
                          display: 'flex',
                          gap: 8
                        }}
                      >

                        <button
                          className="btn btn-primary"
                          onClick={() =>
                            addLesson(module.id)
                          }
                          disabled={addingLesson}
                        >
                          {addingLesson
                            ? 'Creating...'
                            : 'Create Lesson'}
                        </button>

                        <button
                          className="btn btn-outline"
                          onClick={cancelLessonForm}
                          disabled={addingLesson}
                        >
                          Cancel
                        </button>

                      </div>

                    </div>

                  )}


                  {/* =================================================
                      LESSON LIST
                  ================================================= */}

                  <div
                    style={{
                      marginTop: 15
                    }}
                  >

                    {!module.lessons ||
                    module.lessons.length === 0 ? (

                      <p
                        style={{
                          color: 'var(--text-500)',
                          fontSize: 13
                        }}
                      >
                        No lessons added to this module yet.
                      </p>

                    ) : (

                      module.lessons.map(
                        (lesson, lessonIndex) => (

                          <div
                            key={lesson.id}
                            className="lesson-row"
                          >

                            <span>

                              🎬{' '}

                              {lessonIndex + 1}.{' '}

                              {lesson.title}

                            </span>

                            <span className="dur">

                              {lesson.duration ||
                                '00:00'}

                            </span>

                          </div>

                        )
                      )

                    )}

                  </div>

                </div>

              ))

            )}

          </div>

        )}


        {/* =================================================
            STEP 3
        ================================================= */}

        {step === 2 && (

          <div>

            <h3
              style={{
                fontSize: 15
              }}
            >
              Step 3: Publish & Preview
            </h3>

            <p
              style={{
                color: 'var(--text-600)',
                fontSize: 14
              }}
            >
              Review your course before publishing it.
            </p>


            {/* COURSE SUMMARY */}

            <div
              className="card"
              style={{
                padding: 18,
                marginTop: 18
              }}
            >

              <h2
                style={{
                  marginTop: 0
                }}
              >
                {createdCourse?.title}
              </h2>

              <p>
                {createdCourse?.description ||
                  'No description provided.'}
              </p>

              <div
                style={{
                  display: 'flex',
                  gap: 20,
                  flexWrap: 'wrap',
                  marginTop: 12
                }}
              >

                <span>
                  <strong>
                    Level:
                  </strong>{' '}
                  {createdCourse?.level}
                </span>

                <span>
                  <strong>
                    Modules:
                  </strong>{' '}
                  {modules.length}
                </span>

                <span>
                  <strong>
                    Lessons:
                  </strong>{' '}
                  {modules.reduce(
                    (total, module) =>
                      total +
                      (module.lessons?.length || 0),
                    0
                  )}
                </span>

              </div>

            </div>


            {/* CURRICULUM PREVIEW */}

            <div
              style={{
                marginTop: 18
              }}
            >

              {modules.map(
                (module, index) => (

                  <div
                    key={module.id}
                    className="card"
                    style={{
                      padding: 16,
                      marginBottom: 12
                    }}
                  >

                    <strong>
                      Module {index + 1}: {module.title}
                    </strong>

                    {module.lessons?.map(
                      (lesson, lessonIndex) => (

                        <div
                          key={lesson.id}
                          style={{
                            padding: '8px 0',
                            fontSize: 13
                          }}
                        >

                          🎬 {lessonIndex + 1}.{' '}
                          {lesson.title}

                          <span
                            style={{
                              marginLeft: 10,
                              color: 'var(--text-500)'
                            }}
                          >
                            {lesson.duration}
                          </span>

                        </div>

                      )
                    )}

                  </div>

                )
              )}

            </div>


            <div className="alert-success">

              Your course has been saved as a draft.
              You can publish it when you are ready.

            </div>

          </div>

        )}


        {/* =================================================
            NAVIGATION BUTTONS
        ================================================= */}

        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: 24
          }}
        >

          {/* PREVIOUS */}

          <button
            className="btn btn-outline"
            disabled={step === 0}
            onClick={() =>
              setStep((current) =>
                Math.max(0, current - 1)
              )
            }
          >
            ← Previous
          </button>


          {/* CONTINUE */}

          {step === 0 && (

            <button
              className="btn btn-primary"
              onClick={createCourse}
              disabled={savingCourse}
            >
              {savingCourse
                ? 'Creating Course...'
                : 'Create Course & Continue →'}
            </button>

          )}


          {/* CURRICULUM → PREVIEW */}

          {step === 1 && (

            <button
              className="btn btn-primary"
              onClick={() => {
                setError('')
                setStep(2)
              }}
            >
              Review Course →
            </button>

          )}


          {/* PUBLISH */}

          {step === 2 && (

            <button
              className="btn btn-primary"
              onClick={publishCourse}
              disabled={savingCourse}
            >
              {savingCourse
                ? 'Publishing...'
                : 'Publish Course'}
            </button>

          )}

        </div>

      </div>

    </DashboardLayout>

  )
}