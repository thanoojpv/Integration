import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import { apiRequest } from '../services/api'
import { useNotification } from '../context/NotificationContext'

const WISHLIST_KEY = 'devsprint_wishlist'

// =========================================================
// WISHLIST HELPERS
// =========================================================

function readWishlist() {
  try {
    return JSON.parse(
      localStorage.getItem(WISHLIST_KEY) || '[]'
    )
  } catch {
    return []
  }
}

// =========================================================
// LOAD RAZORPAY CHECKOUT SCRIPT
// =========================================================

function loadRazorpayScript() {
  return new Promise((resolve, reject) => {
    if (window.Razorpay) {
      resolve(true)
      return
    }

    const existingScript = document.querySelector(
      'script[src="https://checkout.razorpay.com/v1/checkout.js"]'
    )

    if (existingScript) {
      existingScript.addEventListener(
        'load',
        () => resolve(Boolean(window.Razorpay)),
        { once: true }
      )

      existingScript.addEventListener(
        'error',
        () => reject(
          new Error('Unable to load Razorpay Checkout')
        ),
        { once: true }
      )

      return
    }

    const script = document.createElement('script')

    script.src =
      'https://checkout.razorpay.com/v1/checkout.js'

    script.async = true

    script.onload = () => {
      if (window.Razorpay) {
        resolve(true)
      } else {
        reject(
          new Error('Razorpay Checkout failed to initialize')
        )
      }
    }

    script.onerror = () => {
      script.remove()

      reject(
        new Error('Unable to load Razorpay Checkout')
      )
    }

    document.body.appendChild(script)
  })
}

// =========================================================
// COURSE DETAIL COMPONENT
// =========================================================

export default function CourseDetail() {
  const { courseId } = useParams()
  const navigate = useNavigate()

  // -------------------------------------------------------
  // STATE
  // -------------------------------------------------------

  const [course, setCourse] = useState(null)
  const [modules, setModules] = useState([])
  const [wishlisted, setWishlisted] = useState(false)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [starting, setStarting] = useState(false)
  const [purchasing, setPurchasing] = useState(false)

  const [accessGranted, setAccessGranted] = useState(false)
  const [paymentRequired, setPaymentRequired] = useState(false)
  const [enrollmentStatus, setEnrollmentStatus] = useState(null)
  const [pendingAmount, setPendingAmount] = useState(0)

  const { showNotification } = useNotification()

  // =========================================================
  // LOAD COURSE
  // =========================================================

  useEffect(() => {
    let cancelled = false

    async function loadCourse() {
      try {
        setLoading(true)
        setError('')

        const data = await apiRequest(
          `/api/courses/${courseId}`
        )

        console.log(
          'COURSE DETAIL API:',
          data
        )

        if (cancelled) return

        setCourse(data.course)
        setModules(data.modules || [])

        setWishlisted(
          Boolean(data.wishlisted)
        )

        setAccessGranted(
          Boolean(data.access_granted)
        )

        setPaymentRequired(
          Boolean(data.payment_required)
        )

        setEnrollmentStatus(
          data.enrollment_status || null
        )

        setPendingAmount(
          Number(data.pending_amount || 0)
        )
      } catch (err) {
        if (cancelled) return

        console.error(
          'Course detail error:',
          err
        )

        setError(
          err.message || 'Unable to load course'
        )
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadCourse()

    return () => {
      cancelled = true
    }
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
          method: 'PUT',
        }
      )

      console.log(
        'WISHLIST API:',
        data
      )

      setWishlisted(
        Boolean(data.wishlisted)
      )
    } catch (err) {
      console.error(
        'Wishlist error:',
        err
      )

      showNotification(
        err.message || 'Unable to update wishlist'
      )
    }
  }

  // =========================================================
  // REFRESH COURSE AFTER PURCHASE
  // =========================================================

  const loadCourseAfterPurchase = async () => {
    const data = await apiRequest(
      `/api/courses/${courseId}`
    )

    console.log(
      'COURSE AFTER PURCHASE:',
      data
    )

    setCourse(data.course)

    setModules(
      data.modules || []
    )

    setWishlisted(
      Boolean(data.wishlisted)
    )

    setAccessGranted(
      Boolean(data.access_granted)
    )

    setPaymentRequired(
      Boolean(data.payment_required)
    )

    setEnrollmentStatus(
      data.enrollment_status || null
    )

    setPendingAmount(
      Number(data.pending_amount || 0)
    )

    return data
  }

  // =========================================================
  // START LEARNING
  // =========================================================

  const startLearning = async () => {
    try {
      setStarting(true)

      // -----------------------------------------------------
      // Security check
      // -----------------------------------------------------

      if (
        Number(course.course_fee || 0) > 0 &&
        !accessGranted
      ) {
        showNotification(
          'Please purchase this course before starting.'
        )

        return
      }

      // -----------------------------------------------------
      // Enroll / verify enrollment
      // -----------------------------------------------------

      const data = await apiRequest(
        `/api/courses/${course.id}/enroll`,
        {
          method: 'POST',
        }
      )

      console.log(
        'ENROLLMENT API:',
        data
      )

      const enrollment = data.enrollment

      // -----------------------------------------------------
      // Paid course not active
      // -----------------------------------------------------

      if (enrollment?.status !== 'active') {
        showNotification(
          'Payment is required before you can access this course.'
        )

        return
      }

      // -----------------------------------------------------
      // Refresh course details
      // -----------------------------------------------------

      const refreshed = await apiRequest(
        `/api/courses/${course.id}`
      )

      setCourse(refreshed.course)

      setModules(
        refreshed.modules || []
      )

      setAccessGranted(
        Boolean(refreshed.access_granted)
      )

      setPaymentRequired(
        Boolean(refreshed.payment_required)
      )

      setEnrollmentStatus(
        refreshed.enrollment_status || null
      )

      setPendingAmount(
        Number(refreshed.pending_amount || 0)
      )

      // -----------------------------------------------------
      // Find first lesson
      // -----------------------------------------------------

      const firstLesson =
        refreshed.modules?.[0]?.lessons?.[0]

      if (firstLesson) {
        navigate(
          `/learner/course/${course.id}/lesson/${firstLesson.id}`
        )
      } else {
        navigate('/learner/my-learning')
      }
    } catch (err) {
      console.error(
        'Enrollment error:',
        err
      )

      showNotification(
        err.message || 'Unable to start course'
      )
    } finally {
      setStarting(false)
    }
  }

  // =========================================================
  // PURCHASE COURSE - RAZORPAY CHECKOUT
  // =========================================================

  const purchaseCourse = async () => {
    if (purchasing) {
      return
    }

    try {
      setPurchasing(true)

      // -----------------------------------------------------
      // STEP 1: Create or retrieve enrollment
      // -----------------------------------------------------

      const enrollmentData = await apiRequest(
        `/api/courses/${course.id}/enroll`,
        {
          method: 'POST',
        }
      )

      console.log(
        'PURCHASE ENROLLMENT API:',
        enrollmentData
      )

      const enrollment = enrollmentData.enrollment

      if (!enrollment?.id) {
        throw new Error(
          'Unable to create course enrollment'
        )
      }

      // -----------------------------------------------------
      // STEP 2: Free course
      // -----------------------------------------------------

      const courseFee = Number(
        enrollment.course_fee ??
        course.course_fee ??
        0
      )

      if (courseFee <= 0) {
        await loadCourseAfterPurchase()

        showNotification(
          'Course enrolled successfully.'
        )

        return
      }

      // -----------------------------------------------------
      // STEP 3: Already paid
      // -----------------------------------------------------

      if (enrollment.status === 'active') {
        await loadCourseAfterPurchase()

        showNotification(
          'Course is already purchased.'
        )

        return
      }

      // -----------------------------------------------------
      // STEP 4: Load Razorpay Checkout
      // -----------------------------------------------------

      await loadRazorpayScript()

      // -----------------------------------------------------
      // STEP 5: Create order through Flask backend
      // -----------------------------------------------------

      // The backend calculates the outstanding balance.
      // Never trust a payment amount supplied by the browser.

      const order = await apiRequest(
        '/api/learner/payments/razorpay/order',
        {
          method: 'POST',
          body: JSON.stringify({
            enrollment_id: enrollment.id,
          }),
        }
      )

      console.log(
        'RAZORPAY ORDER API:',
        order
      )

      if (
        !order?.order_id ||
        !order?.key_id ||
        !Number.isFinite(Number(order.amount)) ||
        Number(order.amount) <= 0
      ) {
        throw new Error(
          'The server did not return a valid Razorpay order.'
        )
      }

      if (order.currency !== 'INR') {
        throw new Error(
          'Unexpected payment currency.'
        )
      }

      // -----------------------------------------------------
      // STEP 6: Open Razorpay Checkout
      // -----------------------------------------------------

      const options = {
        key: order.key_id,

        amount: order.amount,

        currency: order.currency,

        name: 'DevSprint LMS',

        description: `Course: ${
          order.course_name || course.title
        }`,

        order_id: order.order_id,

        // ---------------------------------------------------
        // STEP 7: Razorpay returns payment information
        // ---------------------------------------------------

        handler: async function (response) {
          try {
            setPurchasing(true)

            console.log(
              'RAZORPAY CHECKOUT RESPONSE:',
              {
                order_id: response.razorpay_order_id,
                payment_id: response.razorpay_payment_id,
              }
            )

            // -------------------------------------------------
            // STEP 8: Verify payment through Flask
            // -------------------------------------------------

            const verification = await apiRequest(
              '/api/learner/payments/razorpay/verify',
              {
                method: 'POST',

                body: JSON.stringify({
                  razorpay_order_id:
                    response.razorpay_order_id,

                  razorpay_payment_id:
                    response.razorpay_payment_id,

                  razorpay_signature:
                    response.razorpay_signature,
                }),
              }
            )

            console.log(
              'RAZORPAY VERIFICATION RESPONSE:',
              verification
            )

            // The backend must confirm that payment is paid.
            // Do not unlock the course based only on Checkout's
            // browser-side success callback.

            const verified =
              verification?.payment?.status === 'paid' ||
              verification?.status === 'paid'

            if (!verified) {
              throw new Error(
                'Payment verification was not confirmed. Please contact support before attempting another payment.'
              )
            }

            // -------------------------------------------------
            // STEP 9: Refresh course access
            // -------------------------------------------------

            const refreshed =
              await loadCourseAfterPurchase()

            // -------------------------------------------------
            // STEP 10: Show the correct result
            // -------------------------------------------------

            if (refreshed.access_granted) {
              showNotification(
                'Payment successful! Course unlocked.'
              )
            } else {
              showNotification(
                'Payment verified. Course access is still pending. Please refresh or contact support.'
              )
            }
          } catch (err) {
            console.error(
              'Razorpay verification error:',
              err
            )

            showNotification(
              err.message ||
              'Unable to verify payment. Please contact support before attempting another payment.'
            )
          } finally {
            setPurchasing(false)
          }
        },

        // ---------------------------------------------------
        // Checkout closed by learner
        // ---------------------------------------------------

        modal: {
          ondismiss: function () {
            setPurchasing(false)

            showNotification(
              'Payment window closed. Your course remains locked until payment is verified.'
            )
          },
        },

        // ---------------------------------------------------
        // Checkout appearance
        // ---------------------------------------------------

        theme: {
          color: '#2563eb',
        },
      }

      const checkout = new window.Razorpay(options)

      // -----------------------------------------------------
      // Payment failure
      // -----------------------------------------------------

      checkout.on(
        'payment.failed',
        function (response) {
          console.error(
            'RAZORPAY PAYMENT FAILED:',
            response.error
          )

          setPurchasing(false)

          showNotification(
            response.error?.description ||
            'Payment failed. Please try again.'
          )
        }
      )

      checkout.open()
    } catch (err) {
      console.error(
        'Purchase error:',
        err
      )

      showNotification(
        err.message ||
        'Unable to start the payment process.'
      )

      setPurchasing(false)
    }
  }

  // =========================================================
  // DOWNLOAD SYLLABUS
  // =========================================================

  const downloadSyllabus = () => {
    const syllabusModules = modules
      .map((module) => {
        const lessons = (module.lessons || [])
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
Price: ${
      Number(course.course_fee || 0) > 0
        ? `₹${Number(course.course_fee).toFixed(2)}`
        : 'Free'
    }
Progress: ${course.progress || 0}%

DESCRIPTION
${course.description || ''}

CURRICULUM
${syllabusModules}
`

    const blob = new Blob(
      [syllabus],
      {
        type: 'text/plain;charset=utf-8',
      }
    )

    const url = URL.createObjectURL(blob)

    const link = document.createElement('a')

    link.href = url

    link.download = `${course.id}-syllabus.txt`

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
            {error || 'Course not found.'}
          </p>
        </div>
      </DashboardLayout>
    )
  }

  // =========================================================
  // COURSE PAGE
  // =========================================================

  const coursePrice = Number(
    course.course_fee || 0
  )

  const isPaidCourse = coursePrice > 0

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
              : 'linear-gradient(135deg,#071d3b 0%,#123f67 45%,#08152c 100%)',
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

        {/* ===================================================
            LEFT CARD
        ==================================================== */}

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
              lineHeight: 1.9,
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

        {/* ===================================================
            RIGHT CARD
        ==================================================== */}

        <div
          className="card"
          style={{ padding: 22 }}
        >

          {/* RATING */}

          <div
            style={{
              fontWeight: 700,
              marginBottom: 4,
            }}
          >
            ★ 4.7 · 1,560 learners
          </div>

          {/* INSTRUCTOR */}

          <div
            style={{
              fontSize: 13,
              color: 'var(--text-600)',
              marginBottom: 16,
            }}
          >
            Instructor:{' '}
            {course.trainer ||
              course.instructor ||
              'DevSprint Trainer'}
          </div>

          {/* =================================================
              PRICE
          ================================================== */}

          <div
            style={{
              marginBottom: 16,
              padding: 14,
              borderRadius: 10,
              background: 'var(--surface-2)',
              border: '1px solid var(--border)',
            }}
          >
            <div
              style={{
                fontSize: 13,
                color: 'var(--text-600)',
                marginBottom: 4,
              }}
            >
              Course Price
            </div>

            <div
              style={{
                fontSize: 24,
                fontWeight: 800,
              }}
            >
              {isPaidCourse
                ? `₹${coursePrice.toFixed(2)}`
                : 'Free'}
            </div>

            {/* LOCKED */}

            {isPaidCourse &&
              paymentRequired &&
              !accessGranted && (
                <div
                  style={{
                    marginTop: 6,
                    fontSize: 13,
                    color: 'var(--text-600)',
                  }}
                >
                  🔒 Payment required
                  to access course content
                </div>
              )}

            {/* PURCHASED */}

            {isPaidCourse &&
              accessGranted && (
                <div
                  style={{
                    marginTop: 6,
                    fontSize: 13,
                  }}
                >
                  ✅ Purchased
                </div>
              )}
          </div>

          {/* =================================================
              PURCHASE / START BUTTON
          ================================================== */}

          {isPaidCourse && !accessGranted ? (
            <button
              className="btn btn-primary btn-full"
              style={{
                marginBottom: 10,
              }}
              onClick={purchaseCourse}
              type="button"
              disabled={purchasing}
            >
              {purchasing
                ? 'Processing Payment...'
                : `💳 Purchase Course — ₹${(
                    pendingAmount ||
                    coursePrice
                  ).toFixed(2)}`}
            </button>
          ) : (
            <button
              className="btn btn-primary btn-full"
              style={{
                marginBottom: 10,
              }}
              onClick={startLearning}
              type="button"
              disabled={starting}
            >
              {starting
                ? 'Starting...'
                : accessGranted
                ? '▶ Start Learning Now'
                : '▶ Enroll & Start Learning'}
            </button>
          )}

          {/* =================================================
              WISHLIST
          ================================================== */}

          <button
            className="btn btn-outline btn-full"
            style={{
              marginBottom: 10,
            }}
            onClick={toggleWishlist}
            type="button"
          >
            {wishlisted
              ? '♥ Remove from Wishlist'
              : '♡ Add to Wishlist'}
          </button>

          {/* =================================================
              DOWNLOAD SYLLABUS
          ================================================== */}

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