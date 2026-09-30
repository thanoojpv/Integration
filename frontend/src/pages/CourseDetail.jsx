import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import { apiRequest } from '../services/api'
import { useNotification } from '../context/NotificationContext'

const WISHLIST_KEY = 'devsprint_wishlist'

function readWishlist() {
  try {
    return JSON.parse(localStorage.getItem(WISHLIST_KEY) || '[]')
  } catch {
    return []
  }
}

export default function CourseDetail() {
  const { courseId } = useParams()
  const navigate = useNavigate()

  const [course, setCourse] = useState(null)
  const [modules, setModules] = useState([])
  const [wishlisted, setWishlisted] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [starting, setStarting] = useState(false)
const { showNotification } = useNotification()
  // =========================================================
  // LOAD COURSE
  // =========================================================

  useEffect(() => {
    async function loadCourse() {
      try {
        setLoading(true)
        setError('')

        const data = await apiRequest(
          `/api/courses/${courseId}`
        )

        console.log('COURSE DETAIL API:', data)

        setCourse(data.course)
        setModules(data.modules || [])
        setWishlisted(Boolean(data.wishlisted))
      } catch (err) {
        console.error('Course detail error:', err)

        setError(
          err.message || 'Unable to load course'
        )
      } finally {
        setLoading(false)
      }
    }

    loadCourse()
  }, [courseId])

  // =========================================================
  // WISHLIST
  // =========================================================

  useEffect(() => {
    if (!course?.id) {
      return
    }

    const localWishlist = readWishlist()

    if (localWishlist.includes(course.id)) {
      setWishlisted(true)
    }
  }, [course?.id])

  const toggleWishlist = async () => {
    try {
      const data = await apiRequest(
        `/api/courses/${course.id}/wishlist`,
        {
          method: 'PUT'
        }
      )

      console.log('WISHLIST API:', data)

      setWishlisted(
        Boolean(data.wishlisted)
      )
    } catch (err) {
      console.error('Wishlist error:', err)

      showNotification(
        err.message ||
        'Unable to update wishlist'
      )
    }
  }

  // =========================================================
  // START LEARNING
  // =========================================================

  const startLearning = async () => {
    try {
      setStarting(true)

      // First enroll the learner in this course
      const data = await apiRequest(
        `/api/courses/${course.id}/enroll`,
        {
          method: 'POST'
        }
      )

      console.log(
        'ENROLLMENT API:',
        data
      )

      // Find the first lesson of the current course
      const firstLesson =
        modules?.[0]?.lessons?.[0]

      // If the course has lessons,
      // open the first lesson
      if (firstLesson) {

        navigate(
          `/learner/course/${course.id}/lesson/${firstLesson.id}`
        )

      } else {

        // If there are no lessons,
        // go to My Learning
        navigate(
          '/learner/my-learning'
        )
      }

    } catch (err) {

      console.error(
        'Enrollment error:',
        err
      )

      showNotification(
        err.message ||
        'Unable to update wishlist'
      )

    } finally {
      setStarting(false)
    }
  }

  // =========================================================
  // DOWNLOAD SYLLABUS
  // =========================================================

  const downloadSyllabus = () => {

    const syllabusModules =
      modules
        .map((module) => {

          const lessons =
            (module.lessons || [])
              .map(
                (lesson) =>
                  `  - ${lesson.title}${
                    lesson.duration
                      ? ` (${lesson.duration})`
                      : ''
                  }`
              )
              .join('\n')

          return `${
            module.module ||
            module.title ||
            'Module'
          }\n${lessons}`

        })
        .join('\n\n')

    const syllabus = `DEVSPRINT LMS
COURSE SYLLABUS

Course: ${course.title}
Instructor: ${
      course.trainer ||
      course.instructor ||
      'DevSprint Trainer'
    }
Level: ${course.level}
Progress: ${course.progress || 0}%

DESCRIPTION
${course.description || ''}

CURRICULUM
${syllabusModules}
`

    const blob = new Blob(
      [syllabus],
      {
        type: 'text/plain;charset=utf-8'
      }
    )

    const url =
      URL.createObjectURL(blob)

    const link =
      document.createElement('a')

    link.href = url

    link.download =
      `${course.id}-syllabus.txt`

    document.body.appendChild(link)

    link.click()

    link.remove()

    URL.revokeObjectURL(url)
  }

  // =========================================================
  // LOADING
  // =========================================================

  if (loading) {
    return (
      <DashboardLayout role="learner">

        <div
          className="card"
          style={{ padding: 30 }}
        >
          Loading course...
        </div>

      </DashboardLayout>
    )
  }

  // =========================================================
  // ERROR
  // =========================================================

  if (error || !course) {
    return (
      <DashboardLayout role="learner">

        <div
          className="card"
          style={{ padding: 30 }}
        >

          <h2>
            Unable to load course
          </h2>

          <p>
            {error ||
              'Course not found.'}
          </p>

        </div>

      </DashboardLayout>
    )
  }

  // =========================================================
  // COURSE PAGE
  // =========================================================

  return (
    <DashboardLayout role="learner">

      {/* =====================================================
          COURSE HERO
      ====================================================== */}

      <div
        className="hero-banner blue"
        style={{
          background:
            course.id === 'course-python'
              ? 'linear-gradient(135deg,#042611 0%,#0b5b2c 45%,#01150a 100%)'
              : course.id === 'course-node'
              ? 'linear-gradient(135deg,#07113b 0%,#1a286b 48%,#050b24 100%)'
              : 'linear-gradient(135deg,#071d3b 0%,#123f67 45%,#08152c 100%)'
        }}
      >

        <div className="hero-eyebrow">

          {course.title.toUpperCase()}

          {' · '}

          {course.level.toUpperCase()}

        </div>

        <h2>
          {course.title}
        </h2>

        <p>
          Learn the full toolkit with
          hands-on projects, quizzes,
          and instructor-reviewed
          assignments.
        </p>

      </div>


      {/* =====================================================
          COURSE INFORMATION
      ====================================================== */}

      <div className="two-col">

        {/* LEFT CARD */}

        <div
          className="card"
          style={{ padding: 22 }}
        >

          <div className="section-title">
            What you'll learn
          </div>

          <ul
            style={{
              paddingLeft: 18,
              fontSize: 14,
              color: 'var(--text-900)',
              lineHeight: 1.9
            }}
          >

            <li>
              Learn the core concepts
              and fundamentals of this
              course
            </li>

            <li>
              Practice concepts through
              hands-on examples and
              exercises
            </li>

            <li>
              Build practical projects
              using the skills you learn
            </li>

            <li>
              Complete lessons and track
              your learning progress
            </li>

          </ul>

        </div>


        {/* RIGHT CARD */}

        <div
          className="card"
          style={{ padding: 22 }}
        >

          <div
            style={{
              fontWeight: 700,
              marginBottom: 4
            }}
          >
            ★ 4.7 · 1,560 learners
          </div>


          <div
            style={{
              fontSize: 13,
              color: 'var(--text-600)',
              marginBottom: 16
            }}
          >
            Instructor:{' '}

            {course.trainer ||
              course.instructor ||
              'DevSprint Trainer'}

          </div>


          {/* START LEARNING */}

          <button
            className="btn btn-primary btn-full"
            style={{
              marginBottom: 10
            }}
            onClick={startLearning}
            type="button"
            disabled={starting}
          >

            {starting
              ? 'Starting...'
              : '▶ Start Learning Now'}

          </button>


          {/* WISHLIST */}

          <button
            className="btn btn-outline btn-full"
            style={{
              marginBottom: 10
            }}
            onClick={toggleWishlist}
            type="button"
          >

            {wishlisted
              ? '♥ Remove from Wishlist'
              : '♡ Add to Wishlist'}

          </button>


          {/* DOWNLOAD SYLLABUS */}

          <button
            className="btn btn-outline btn-full"
            onClick={downloadSyllabus}
            type="button"
          >

            ⬇ Download Syllabus

          </button>

        </div>

      </div>

    </DashboardLayout>
  )
}