import React, {
  useEffect,
  useMemo,
  useState
} from 'react'

import {
  Link,
  useNavigate,
  useParams
} from 'react-router-dom'

import DashboardLayout from '../components/DashboardLayout'

import {
  apiRequest,
  fetchAuthenticatedBlob
} from '../services/api'

import { useNotification } from '../context/NotificationContext'


export default function LessonPlayer() {
  const { courseId, lessonId } = useParams()
  const navigate = useNavigate()

  const { showNotification } = useNotification()
  const [course, setCourse] = useState(null)
  const [modules, setModules] = useState([])
  const [lesson, setLesson] = useState(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [savingProgress, setSavingProgress] = useState(false)

  // Authenticated media Blob URLs
  const [videoBlobUrl, setVideoBlobUrl] = useState('')
  const [pdfBlobUrl, setPdfBlobUrl] = useState('')

  const [videoLoading, setVideoLoading] = useState(false)
  const [pdfLoading, setPdfLoading] = useState(false)

  const [mediaError, setMediaError] = useState('')


  // =========================================================
  // CONVERT BACKEND RESOURCE URL TO API ENDPOINT
  // =========================================================

  const getResourceEndpoint = (fileUrl) => {
    if (!fileUrl) {
      return ''
    }

    const apiBaseUrl =
      import.meta.env.VITE_API_BASE_URL

    if (fileUrl.startsWith(apiBaseUrl)) {
      return fileUrl.replace(
        apiBaseUrl,
        ''
      )
    }

    if (fileUrl.startsWith('/')) {
      return fileUrl
    }

    return `/${fileUrl}`
  }

    // =========================================================
  // LESSON RESOURCES
  // =========================================================

  const videoResource =
    lesson?.resources?.find(
      (resource) =>
        resource.type === 'video'
    )

  const pdfResource =
    lesson?.resources?.find(
      (resource) =>
        resource.type === 'pdf'
    )

  const videoUrl =
    videoResource?.url ||
    lesson?.video_url ||
    ''

  const pdfUrl =
    pdfResource?.url ||
    lesson?.pdf_url ||
    ''


  // =========================================================
  // LOAD COURSE + LESSON
  // =========================================================

  useEffect(() => {
    let cancelled = false

    async function loadLesson() {
      try {
        setLoading(true)
        setError('')

        const data = await apiRequest(
          `/api/courses/${courseId}`
        )

        console.log(
          'LESSON PLAYER DATA:',
          data
        )

        if (cancelled) {
          return
        }

        setCourse(data.course || null)

        const loadedModules =
          data.modules || []

        setModules(loadedModules)

        const allLoadedLessons =
          loadedModules.flatMap(
            (module) =>
              module.lessons || []
          )

        const foundLesson =
          allLoadedLessons.find(
            (item) =>
              item.id === lessonId
          )

        if (!foundLesson) {
          setError('Lesson not found')
          setLesson(null)
          return
        }

        setLesson(foundLesson)

      } catch (err) {
        console.error(
          'Lesson loading error:',
          err
        )

        if (!cancelled) {
          setError(
            err.message ||
            'Unable to load lesson'
          )
        }

      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadLesson()

    return () => {
      cancelled = true
    }

  }, [courseId, lessonId])


  // =========================================================
  // ALL LESSONS
  // =========================================================

  const allLessons = modules.flatMap(
  (module) =>
    module.lessons || []
)


  // =========================================================
  // CURRENT / NEXT / PREVIOUS LESSON
  // =========================================================

  const currentIndex =
    allLessons.findIndex(
      (item) =>
        item.id === lessonId
    )

  const nextLesson =
    currentIndex >= 0 &&
    currentIndex <
      allLessons.length - 1
      ? allLessons[
          currentIndex + 1
        ]
      : null

  const previousLesson =
    currentIndex > 0
      ? allLessons[
          currentIndex - 1
        ]
      : null


  // =========================================================
  // LOAD AUTHENTICATED VIDEO
  // =========================================================

  useEffect(() => {
    let objectUrl = ''
    let cancelled = false

    async function loadVideo() {
      if (!videoUrl) {
        setVideoBlobUrl('')
        return
      }

      try {
        setVideoLoading(true)
        setMediaError('')

        const endpoint =
          getResourceEndpoint(
            videoUrl
          )

        if (!endpoint) {
          return
        }

        const blob =
          await fetchAuthenticatedBlob(
            endpoint
          )

        if (cancelled) {
          return
        }

        objectUrl =
          URL.createObjectURL(blob)

        setVideoBlobUrl(objectUrl)

      } catch (err) {
        console.error(
          'Video loading error:',
          err
        )

        if (!cancelled) {
          setVideoBlobUrl('')

          setMediaError(
            err.message ||
            'Unable to load video'
          )
        }

      } finally {
        if (!cancelled) {
          setVideoLoading(false)
        }
      }
    }

    loadVideo()

    return () => {
      cancelled = true

      if (objectUrl) {
        URL.revokeObjectURL(
          objectUrl
        )
      }

      setVideoBlobUrl('')
    }

  }, [videoUrl])


  // =========================================================
  // OPEN PDF WITH AUTHENTICATION
  // =========================================================

  const openPdf = async () => {
    if (!pdfUrl) {
      alert(
        'No PDF has been uploaded for this lesson.'
      )
      return
    }

    try {
      setPdfLoading(true)

      const endpoint =
        getResourceEndpoint(
          pdfUrl
        )

      if (!endpoint) {
        throw new Error(
          'PDF URL is not available.'
        )
      }

      const blob =
        await fetchAuthenticatedBlob(
          endpoint
        )

      const objectUrl =
        URL.createObjectURL(blob)

      setPdfBlobUrl(objectUrl)

      const newWindow =
        window.open(
          objectUrl,
          '_blank',
          'noopener,noreferrer'
        )

      if (!newWindow) {
        alert(
          'Your browser blocked the PDF popup. Please allow popups for this site.'
        )
      }

      // Keep the Blob URL alive for the PDF tab.
      setTimeout(() => {
        URL.revokeObjectURL(
          objectUrl
        )

        setPdfBlobUrl(
          (currentUrl) =>
            currentUrl === objectUrl
              ? ''
              : currentUrl
        )
      }, 60000)

    } catch (err) {
      console.error(
        'PDF open error:',
        err
      )

      showNotification(
        err.message ||
        'Unable to open PDF'
      )

    } finally {
      setPdfLoading(false)
    }
  }


  // =========================================================
  // MARK LESSON COMPLETE
  // =========================================================

  const markLessonComplete =
    async () => {

      if (!lesson) {
        return
      }

      try {
        setSavingProgress(true)

        const data =
          await apiRequest(
            `/api/learner/lessons/${lesson.id}/progress`,
            {
              method: 'POST',

              body: JSON.stringify({
                completed: true
              })
            }
          )

        console.log(
          'PROGRESS UPDATED:',
          data
        )

        setLesson(
          (current) => ({
            ...current,
            completed: true
          })
        )

        setModules(
          (currentModules) =>
            currentModules.map(
              (module) => ({
                ...module,

                lessons:
                  (
                    module.lessons ||
                    []
                  ).map(
                    (item) =>
                      item.id ===
                      lesson.id
                        ? {
                            ...item,
                            completed:
                              true
                          }
                        : item
                  )
              })
            )
        )

        setCourse(
          (current) => ({
            ...current,

            progress:
              data.courseProgress ||
              0
          })
        )

      } catch (err) {
        console.error(
          'Progress update error:',
          err
        )

        showNotification(
          err.message ||
          'Unable to save progress'
        )

      } finally {
        setSavingProgress(false)
      }
    }


  // =========================================================
  // LOADING
  // =========================================================

  if (loading) {
    return (
      <DashboardLayout
        role="learner"
      >
        <div
          className="card"
          style={{
            padding: 30,
            textAlign: 'center'
          }}
        >
          Loading lesson...
        </div>
      </DashboardLayout>
    )
  }


  // =========================================================
  // ERROR
  // =========================================================

  if (error || !lesson) {
    return (
      <DashboardLayout
        role="learner"
      >
        <div
          className="card"
          style={{
            padding: 30
          }}
        >

          <h2>
            Unable to load lesson
          </h2>

          <p>
            {error ||
              'Lesson not found'}
          </p>

          <Link
            to={`/learner/course/${courseId}`}
            className="btn btn-primary"
          >
            ← Back to Course
          </Link>

        </div>
      </DashboardLayout>
    )
  }


  // =========================================================
  // PAGE
  // =========================================================

  return (
    <DashboardLayout
      role="learner"
    >

      {/* =====================================================
          TOP HEADER
      ===================================================== */}

      <div
        style={{
          display: 'flex',
          justifyContent:
            'space-between',
          alignItems: 'center',
          marginBottom: 14,
          gap: 15,
          flexWrap: 'wrap'
        }}
      >

        <div>

          <Link
            to={`/learner/course/${courseId}`}
            style={{
              fontSize: 13,
              color:
                'var(--text-500)'
            }}
          >
            ← {course?.title}
          </Link>

          <h1
            style={{
              marginTop: 8,
              marginBottom: 0
            }}
          >
            {lesson.title}
          </h1>

        </div>

        <strong
          style={{
            color: '#2563eb'
          }}
        >
          Course Progress:{' '}
          {course?.progress || 0}%
          {' '}Complete
        </strong>

      </div>


      {/* =====================================================
          MAIN GRID
      ===================================================== */}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns:
            'minmax(0, 1fr) 360px',
          gap: 18,
          alignItems: 'start'
        }}
      >

        {/* ===================================================
            LEFT SIDE
        =================================================== */}

        <div>

          {/* =================================================
              VIDEO
          ================================================= */}

          <div
            style={{
              background:
                '#0b1028',
              borderRadius: 14,
              minHeight: 400,
              display: 'flex',
              alignItems:
                'center',
              justifyContent:
                'center',
              overflow: 'hidden',
              marginBottom: 18
            }}
          >

            {videoLoading ? (

              <div
                style={{
                  color: 'white',
                  textAlign:
                    'center'
                }}
              >

                <div
                  style={{
                    fontSize: 40,
                    marginBottom: 12
                  }}
                >
                  🎥
                </div>

                <h3>
                  Loading video...
                </h3>

              </div>

            ) : videoBlobUrl ? (

              <video
                controls
                preload="metadata"
                style={{
                  width: '100%',
                  maxHeight: 520,
                  display: 'block'
                }}
                src={
                  videoBlobUrl
                }
              >
                Your browser does not
                support video playback.
              </video>

            ) : (

              <div
                style={{
                  textAlign:
                    'center',
                  color: 'white',
                  padding: 30
                }}
              >

                <div
                  style={{
                    fontSize: 52,
                    marginBottom: 15
                  }}
                >
                  ▶
                </div>

                <h3>
                  No video uploaded
                </h3>

                <p
                  style={{
                    color:
                      '#aeb6d1'
                  }}
                >
                  The trainer has not
                  uploaded a video for
                  this lesson yet.
                </p>

                {mediaError && (
                  <p
                    style={{
                      color:
                        '#fca5a5',
                      marginTop: 12,
                      fontSize: 13
                    }}
                  >
                    {mediaError}
                  </p>
                )}

              </div>

            )}

          </div>


          {/* =================================================
              LESSON TITLE + NAVIGATION
          ================================================= */}

          <div
            style={{
              display: 'flex',
              justifyContent:
                'space-between',
              alignItems:
                'center',
              gap: 15,
              marginBottom: 18,
              flexWrap: 'wrap'
            }}
          >

            <div>

              <h2
                style={{
                  margin: 0
                }}
              >
                {lesson.title}
              </h2>

              <div
                style={{
                  marginTop: 5,
                  color:
                    'var(--text-500)'
                }}
              >
                Duration:{' '}
                {lesson.duration ||
                  '00:00'}
              </div>

            </div>


            <div
              style={{
                display: 'flex',
                gap: 8,
                flexWrap:
                  'wrap'
              }}
            >

              {previousLesson && (
                <button
                  className="btn btn-outline"
                  type="button"
                  onClick={() =>
                    navigate(
                      `/learner/course/${courseId}/lesson/${previousLesson.id}`
                    )
                  }
                >
                  ← Previous
                </button>
              )}

              {nextLesson && (
                <button
                  className="btn btn-outline"
                  type="button"
                  onClick={() =>
                    navigate(
                      `/learner/course/${courseId}/lesson/${nextLesson.id}`
                    )
                  }
                >
                  Next Lesson →
                </button>
              )}

            </div>

          </div>


          {/* =================================================
              COMPLETE BUTTON
          ================================================= */}

          <div
            style={{
              display: 'flex',
              justifyContent:
                'flex-end',
              marginBottom: 20
            }}
          >

            <button
              className="btn btn-primary"
              type="button"
              onClick={
                markLessonComplete
              }
              disabled={
                savingProgress ||
                lesson.completed
              }
            >
              {lesson.completed
                ? '✓ Lesson Completed'
                : savingProgress
                ? 'Saving...'
                : 'Mark Lesson Complete'}
            </button>

          </div>


          {/* =================================================
              RESOURCES
          ================================================= */}

          <div
            className="card"
            style={{
              padding: 22,
              marginBottom: 18
            }}
          >

            <h2
              style={{
                marginTop: 0
              }}
            >
              Resources
            </h2>

            <p
              style={{
                color:
                  'var(--text-500)'
              }}
            >
              Resources for this lesson.
            </p>


            {pdfUrl ? (

              <div
                style={{
                  display: 'flex',
                  gap: 10,
                  alignItems:
                    'center',
                  flexWrap:
                    'wrap'
                }}
              >

                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={
                    openPdf
                  }
                  disabled={
                    pdfLoading
                  }
                >
                  {pdfLoading
                    ? 'Opening PDF...'
                    : '📄 Open PDF'}
                </button>

              </div>

            ) : (

              <div
                style={{
                  padding: 14,
                  border:
                    '1px solid var(--border)',
                  borderRadius: 10,
                  color:
                    'var(--text-500)'
                }}
              >
                No PDF has been uploaded
                for this lesson yet.
              </div>

            )}

          </div>


          {/* =================================================
              LESSON CONTENT
          ================================================= */}

          <div
            className="card"
            style={{
              padding: 22
            }}
          >

            <h2
              style={{
                marginTop: 0
              }}
            >
              Lesson Overview
            </h2>

            <p
              style={{
                whiteSpace:
                  'pre-wrap',
                lineHeight: 1.7,
                color:
                  'var(--text-700)'
              }}
            >
              {lesson.content ||
                'No lesson description has been added yet.'}
            </p>

          </div>

        </div>


        {/* ===================================================
            RIGHT SIDE - COURSE CONTENT
        =================================================== */}

        <aside
          className="card"
          style={{
            padding: 18,
            position: 'sticky',
            top: 20
          }}
        >

          <h3
            style={{
              marginTop: 0
            }}
          >
            Course Content
          </h3>


          {modules.length === 0 ? (

            <p
              style={{
                color:
                  'var(--text-500)'
              }}
            >
              No modules have been
              added to this course yet.
            </p>

          ) : (

            modules.map(
              (module) => (

                <div
                  key={module.id}
                  style={{
                    marginBottom: 20
                  }}
                >

                  <div
                    style={{
                      fontSize: 12,
                      fontWeight: 800,
                      color:
                        '#94a3b8',
                      textTransform:
                        'uppercase',
                      marginBottom: 8
                    }}
                  >
                    {module.module ||
                      module.title ||
                      `Module ${module.id}`}
                  </div>


                  {(module.lessons ||
                    []).map(
                    (item) => (

                      <Link
                        key={item.id}
                        to={`/learner/course/${courseId}/lesson/${item.id}`}
                        style={{
                          display:
                            'flex',
                          justifyContent:
                            'space-between',
                          alignItems:
                            'center',
                          gap: 8,
                          padding:
                            '10px 8px',
                          borderRadius: 8,
                          textDecoration:
                            'none',
                          background:
                            item.id ===
                            lesson.id
                              ? '#e8eefc'
                              : 'transparent',
                          color:
                            item.id ===
                            lesson.id
                              ? '#2563eb'
                              : 'var(--text-900)',
                          marginBottom: 3
                        }}
                      >

                        <span
                          style={{
                            display:
                              'flex',
                            gap: 7,
                            alignItems:
                              'center'
                          }}
                        >

                          <span>
                            {item.completed
                              ? '✓'
                              : '○'}
                          </span>

                          <span>
                            {item.title}
                          </span>

                        </span>

                        <span
                          style={{
                            fontSize: 12,
                            color:
                              'var(--text-500)',
                            whiteSpace:
                              'nowrap'
                          }}
                        >
                          {item.duration ||
                            '00:00'}
                        </span>

                      </Link>

                    )
                  )}

                </div>

              )
            )

          )}

        </aside>

      </div>

    </DashboardLayout>
  )
}