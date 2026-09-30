import React, {
  useEffect,
  useMemo,
  useState
} from 'react'

import DashboardLayout from '../components/DashboardLayout'
import { apiRequest } from '../services/api'

export default function AdminCatalog() {

  const [courses, setCourses] =
    useState([])

  const [loading, setLoading] =
    useState(true)

  const [error, setError] =
    useState('')

  const [search, setSearch] =
    useState('')

  const [expanded, setExpanded] =
    useState({})

  async function loadCatalog() {

    try {

      setLoading(true)
      setError('')

      const data =
        await apiRequest(
          '/api/admin/courses'
        )

      setCourses(
        data.courses || []
      )

    } catch (err) {

      console.error(
        'Admin catalog error:',
        err
      )

      setError(
        err.message ||
        'Unable to load course catalog'
      )

    } finally {

      setLoading(false)

    }
  }

  useEffect(() => {

    loadCatalog()

  }, [])

  const filteredCourses =
    useMemo(() => {

      const term =
        search
          .trim()
          .toLowerCase()

      if (!term) {
        return courses
      }

      return courses.filter(
        (course) => {

          const text = [
            course.id,
            course.title,
            course.level,
            course.trainer
          ]
            .filter(Boolean)
            .join(' ')
            .toLowerCase()

          return text.includes(term)
        }
      )

    }, [courses, search])

  function toggleCourse(
    courseId
  ) {

    setExpanded(
      (previous) => ({
        ...previous,
        [courseId]:
          !previous[courseId]
      })
    )
  }

  async function handleToggleStatus(course) {

  const nextStatus = !course.published

  try {

    setError('')

    await apiRequest(
      `/api/admin/courses/${encodeURIComponent(course.id)}/status`,
      {
        method: 'PATCH',
        body: JSON.stringify({
          published: nextStatus
        })
      }
    )

    setCourses((previous) =>
      previous.map((item) =>
        item.id === course.id
          ? {
              ...item,
              published: nextStatus
            }
          : item
      )
    )

  } catch (err) {

    console.error(
      'Course status update error:',
      err
    )

    setError(
      err.message ||
      'Unable to update course status'
    )
  }
}


async function handleDeleteCourse(course) {

  const confirmed =
    window.confirm(
      `Delete "${course.title}" permanently?\n\n` +
      `This will delete the course and its modules, lessons, ` +
      `quizzes, assignments, enrollments, certificates, ` +
      `coding exam data, learning-time records and uploaded files.\n\n` +
      `This action cannot be undone.`
    )

  if (!confirmed) {
    return
  }

  try {

    setError('')

    await apiRequest(
      `/api/admin/courses/${encodeURIComponent(course.id)}`,
      {
        method: 'DELETE'
      }
    )

    setCourses((previous) =>
      previous.filter(
        (item) =>
          item.id !== course.id
      )
    )

    setExpanded((previous) => {

      const updated = {
        ...previous
      }

      delete updated[course.id]

      return updated
    })

  } catch (err) {

    console.error(
      'Course deletion error:',
      err
    )

    setError(
      err.message ||
      'Unable to delete course'
    )
  }
}

  return (

    <DashboardLayout role="admin">

      <div
        className="page-heading-row"
      >

        <div>

          <h1>
            Course Catalog
          </h1>

          <p>
            View all courses, modules
            and lessons.
          </p>

        </div>

        <button
          className="btn btn-outline"
          onClick={loadCatalog}
          disabled={loading}
        >
          {loading
            ? 'Loading...'
            : '↻ Refresh'}
        </button>

      </div>

      <div
        className="card"
        style={{
          padding: 18,
          marginBottom: 20
        }}
      >

        <input
          type="text"
          value={search}
          onChange={(e) =>
            setSearch(e.target.value)
          }
          placeholder="Search course, trainer, level or course ID..."
          style={{
            width: '100%',
            padding: '11px 12px',
            border:
              '1px solid var(--border)',
            borderRadius: 8,
            boxSizing: 'border-box'
          }}
        />

      </div>

      {error ? (

        <div
          className="card"
          style={{
            padding: 24
          }}
        >

          <h2>
            Unable to load catalog
          </h2>

          <p>
            {error}
          </p>

          <button
            className="btn btn-primary"
            onClick={loadCatalog}
          >
            Try Again
          </button>

        </div>

      ) : loading ? (

        <div
          className="card"
          style={{
            padding: 30,
            textAlign: 'center'
          }}
        >
          Loading course catalog...
        </div>

      ) : filteredCourses.length === 0 ? (

        <div
          className="card"
          style={{
            padding: 30,
            textAlign: 'center'
          }}
        >
          No courses found.
        </div>

      ) : (

        <div
          style={{
            display: 'grid',
            gap: 14
          }}
        >

          {filteredCourses.map(
            (course) => {

              const isOpen =
                !!expanded[
                  course.id
                ]

              return (

                <div
                  className="card"
                  key={course.id}
                  style={{
                    padding: 20
                  }}
                >

                  <div
                    style={{
                      display: 'flex',
                      justifyContent:
                        'space-between',
                      alignItems:
                        'flex-start',
                      gap: 16,
                      flexWrap:
                        'wrap'
                    }}
                  >

                    <div>

                      <h2
                        style={{
                          margin:
                            '0 0 8px'
                        }}
                      >
                        {course.title}
                      </h2>

                      <div
                        style={{
                          display:
                            'flex',
                          gap: 18,
                          flexWrap:
                            'wrap',
                          fontSize: 14
                        }}
                      >

                        <span>
                          <strong>
                            ID:
                          </strong>{' '}
                          {course.id}
                        </span>

                        <span>
                          <strong>
                            Trainer:
                          </strong>{' '}
                          {course.trainer ||
                            'Not assigned'}
                        </span>

                        <span>
                          <strong>
                            Level:
                          </strong>{' '}
                          {course.level ||
                            '—'}
                        </span>

                        <span>
                          <strong>
                            Status:
                          </strong>{' '}
                          <span
                            style={{
                              fontWeight: 600,
                              color: course.published
                                ? '#15803d'
                                : '#b45309'
                            }}
                          >
                            {course.published
                              ? 'Active'
                              : 'Inactive'}
                          </span>
                        </span>

                      </div>

                    </div>

                    <div
                      style={{
                        display: 'flex',
                        gap: 8,
                        flexWrap: 'wrap',
                        alignItems: 'center'
                      }}
                    >

                      <button
                        className="btn btn-primary"
                        onClick={() =>
                          toggleCourse(course.id)
                        }
                      >
                        {isOpen
                          ? 'Hide Content'
                          : 'View Content'}
                      </button>

                      <button
                        className="btn btn-outline"
                        onClick={() =>
                          handleToggleStatus(course)
                        }
                      >
                        {course.published
                          ? 'Deactivate'
                          : 'Activate'}
                      </button>

                      <button
                        className="btn"
                        onClick={() =>
                          handleDeleteCourse(course)
                        }
                        style={{
                          border: '1px solid #dc2626',
                          color: '#dc2626',
                          background: 'transparent'
                        }}
                      >
                        Delete
                      </button>

                    </div>

                  </div>

                  {isOpen && (

                    <div
                      style={{
                        marginTop: 18,
                        paddingTop: 18,
                        borderTop:
                          '1px solid var(--border)'
                      }}
                    >

                      {course.modules
                        ?.length ? (

                        course.modules.map(
                          (
                            module,
                            moduleIndex
                          ) => (

                            <div
                              key={
                                module.id
                              }
                              style={{
                                border:
                                  '1px solid var(--border)',
                                borderRadius: 8,
                                padding: 14,
                                marginBottom:
                                  10
                              }}
                            >

                              <h3
                                style={{
                                  margin:
                                    '0 0 10px'
                                }}
                              >
                                Module{' '}
                                {moduleIndex +
                                  1}
                                :{' '}
                                {module.title}
                              </h3>

                              {module
                                .lessons
                                ?.length ? (

                                <div
                                  style={{
                                    display:
                                      'grid',
                                    gap: 8
                                  }}
                                >

                                  {module.lessons.map(
                                    (
                                      lesson,
                                      lessonIndex
                                    ) => (

                                      <div
                                        key={
                                          lesson.id
                                        }
                                        style={{
                                          padding:
                                            '9px 10px',
                                          background:
                                            'var(--surface-2)',
                                          borderRadius:
                                            6
                                        }}
                                      >

                                        <strong>
                                          {lessonIndex +
                                            1}
                                          .{' '}
                                          {
                                            lesson.title
                                          }
                                        </strong>

                                        <div
                                          style={{
                                            fontSize:
                                              13,
                                            marginTop:
                                              4,
                                            color:
                                              'var(--text-500)'
                                          }}
                                        >

                                          ID:{' '}
                                          {
                                            lesson.id
                                          }

                                          {' · '}

                                          Duration:{' '}
                                          {
                                            lesson.duration ||
                                            '00:00'
                                          }

                                          {' · '}

                                          Videos:{' '}
                                          {
                                            lesson.video_count ||
                                            0
                                          }

                                          {' · '}

                                          PDFs:{' '}
                                          {
                                            lesson.pdf_count ||
                                            0
                                          }

                                        </div>

                                      </div>

                                    )
                                  )}

                                </div>

                              ) : (

                                <p>
                                  No lessons
                                  in this
                                  module.
                                </p>

                              )}

                            </div>

                          )
                        )

                      ) : (

                        <p>
                          No modules have
                          been added to this
                          course.
                        </p>

                      )}

                    </div>

                  )}

                </div>

              )
            }
          )}

        </div>

      )}

    </DashboardLayout>

  )
}
