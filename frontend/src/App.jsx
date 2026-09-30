import React from 'react'
import {
  Routes,
  Route,
  Navigate,
} from 'react-router-dom'

import {
  AuthProvider,
  useAuth,
} from './context/AuthContext'

import {
  NotificationProvider,
} from './context/NotificationContext'

import ProtectedRoute from './components/ProtectedRoute'


// =========================================================
// ADMIN PAGES
// =========================================================

import AdminUsers from './pages/AdminUsers'
import AdminCatalog from './pages/AdminCatalog'
import AdminDashboard from './pages/AdminDashboard'
import CreateAccounts from './pages/CreateAccounts'
import Leaderboard from './pages/Leaderboard'
import AdminCertificates from './pages/AdminCertificates'


// =========================================================
// TRAINER PAGES
// =========================================================

import TrainerExams from './pages/TrainerExams'
import TrainerDashboard from './pages/TrainerDashboard'
import TrainerCourseDetail from './pages/TrainerCourseDetail'
import CreateCourse from './pages/CreateCourse'

import TrainerCodingExams from './pages/TrainerCodingExams'
import TrainerCodingQuestions from './pages/TrainerCodingQuestions'
import TrainerCodingExamResults from './pages/TrainerCodingExamResults'


// =========================================================
// AUTH PAGES
// =========================================================

import Login from './pages/Login'
import CreateAccount from './pages/CreateAccount'
import ForgotPassword from './pages/ForgotPassword'


// =========================================================
// LEARNER PAGES
// =========================================================

import LearnerDashboard from './pages/LearnerDashboard'
import LearnerExplore from './pages/LearnerExplore'
import MyLearning from './pages/MyLearning'
import CourseDetail from './pages/CourseDetail'
import LessonPlayer from './pages/LessonPlayer'
import Progress from './pages/Progress'
import LearnerCertificates from './pages/LearnerCertificates'
import LearnerAssessments from './pages/LearnerAssessments'
import LearnerCalendar from './pages/LearnerCalendar'
import LearnerCodingExam from './pages/LearnerCodingExam'
import LearnerExamHistory from './pages/LearnerExamHistory'


// =========================================================
// COMMON PAGES
// =========================================================

import AccountSettings from './pages/AccountSettings'
import ComingSoon from './pages/ComingSoon'


// =========================================================
// EXAMS ROUTER
// =========================================================

function ExamsRoute() {

  const { user } = useAuth()


  // -------------------------------------------------------
  // NOT LOGGED IN
  // -------------------------------------------------------

  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
      />
    )
  }


  // -------------------------------------------------------
  // LEARNER
  // -------------------------------------------------------

  if (user.role === 'learner') {
    return (
      <LearnerAssessments />
    )
  }


  // -------------------------------------------------------
  // TRAINER
  // -------------------------------------------------------

  if (user.role === 'trainer') {
    return (
      <TrainerExams />
    )
  }


  // -------------------------------------------------------
  // ADMIN
  // -------------------------------------------------------

  if (user.role === 'admin') {
    return (
      <Navigate
        to="/admin"
        replace
      />
    )
  }


  // -------------------------------------------------------
  // UNKNOWN ROLE
  // -------------------------------------------------------

  return (
    <Navigate
      to="/login"
      replace
    />
  )
}


// =========================================================
// MAIN APP
// =========================================================

export default function App() {

  return (

    <AuthProvider>

      <NotificationProvider>
        
        <Routes>


        {/* =================================================
            ROOT
        ================================================= */}

        <Route
          path="/"
          element={
            <Navigate
              to="/login"
              replace
            />
          }
        />


        {/* =================================================
            AUTHENTICATION
        ================================================= */}

        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/create-account"
          element={<CreateAccount />}
        />

        <Route
          path="/forgot-password"
          element={<ForgotPassword />}
        />


        {/* =================================================
            MAIN EXAMS PAGE
        ================================================= */}

        <Route
          path="/exams"
          element={<ExamsRoute />}
        />


        {/* =================================================
            LEARNER CODING EXAM
        ================================================= */}

        <Route

          path="/coding-exam"
          element={
            <ProtectedRoute allowedRole="learner">
              <LearnerCodingExam />
            </ProtectedRoute>
          }
        />

        <Route

          path="/coding-exam/:examId"
          element={
            <ProtectedRoute allowedRole="learner">
              <LearnerCodingExam />
            </ProtectedRoute>
          }
        />


        {/* =================================================
            ADMIN
        ================================================= */}

        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRole="admin">
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/users"
          element={
            <ProtectedRoute allowedRole="admin">
              <AdminUsers />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/catalog"
          element={
            <ProtectedRoute allowedRole="admin">
              <AdminCatalog />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/create-accounts"
          element={
            <ProtectedRoute allowedRole="admin">
              <CreateAccounts />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/certificates"
          element={
            <ProtectedRoute allowedRole="admin">
              <AdminCertificates />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/leaderboard"
          element={
            <ProtectedRoute allowedRole="admin">
              <Leaderboard role="admin" />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/settings"
          element={
            <ProtectedRoute allowedRole="admin">
              <AccountSettings role="admin" />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/*"
          element={
            <ProtectedRoute allowedRole="admin">
              <ComingSoon role="admin" />
            </ProtectedRoute>
          }
        />


        {/* =================================================
            TRAINER
        ================================================= */}

        <Route
          path="/trainer"
          element={
            <ProtectedRoute allowedRole="trainer">
              <TrainerDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/trainer/courses"
          element={
            <ProtectedRoute allowedRole="trainer">
              <TrainerDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/trainer/course/:courseId"
          element={
            <ProtectedRoute allowedRole="trainer">
              <TrainerCourseDetail />
            </ProtectedRoute>
          }
        />

        <Route
          path="/trainer/create-course"
          element={
            <ProtectedRoute allowedRole="trainer">
              <CreateCourse />
            </ProtectedRoute>
          }
        />


        {/* =================================================
            TRAINER CODING EXAMS
        ================================================= */}

        <Route
          path="/trainer/coding-exams"
          element={
            <ProtectedRoute allowedRole="trainer">
              <TrainerCodingExams />
            </ProtectedRoute>
          }
        />

        <Route
          path="/trainer/coding-exams/:examId/questions"
          element={
            <ProtectedRoute allowedRole="trainer">
              <TrainerCodingQuestions />
            </ProtectedRoute>
          }
        />

        <Route
          path="/trainer/coding-exams/:examId/results"
          element={
            <ProtectedRoute allowedRole="trainer">
              <TrainerCodingExamResults />
            </ProtectedRoute>
          }
        />


        {/* =================================================
            TRAINER LEADERBOARD
        ================================================= */}

        <Route
          path="/trainer/leaderboard"
          element={
            <ProtectedRoute allowedRole="trainer">
              <Leaderboard role="trainer" />
            </ProtectedRoute>
          }
        />


        {/* =================================================
            TRAINER SETTINGS
        ================================================= */}

        <Route
          path="/trainer/settings"
          element={
            <ProtectedRoute allowedRole="trainer">
              <AccountSettings role="trainer" />
            </ProtectedRoute>
          }
        />


        {/* =================================================
            OLD TRAINER EXAM URLS
        ================================================= */}

        <Route
          path="/trainer/exams"
          element={
            <Navigate
              to="/exams"
              replace
            />
          }
        />

        <Route
          path="/trainer/assignments"
          element={
            <Navigate
              to="/exams"
              replace
            />
          }
        />


        {/* =================================================
            OTHER TRAINER PAGES
        ================================================= */}

        <Route
          path="/trainer/*"
          element={
            <ProtectedRoute allowedRole="trainer">
              <ComingSoon role="trainer" />
            </ProtectedRoute>
          }
        />


        {/* =================================================
            LEARNER
        ================================================= */}

        <Route
          path="/learner"
          element={
            <ProtectedRoute allowedRole="learner">
              <LearnerDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/learner/progress"
          element={
            <ProtectedRoute allowedRole="learner">
              <Progress />
            </ProtectedRoute>
          }
        />

        <Route
          path="/learner/certificates"
          element={
            <ProtectedRoute allowedRole="learner">
              <LearnerCertificates />
            </ProtectedRoute>
          }
        />

        <Route
          path="/learner/my-learning"
          element={
            <ProtectedRoute allowedRole="learner">
              <MyLearning />
            </ProtectedRoute>
          }
        />

        <Route
          path="/learner/explore"
          element={
            <ProtectedRoute allowedRole="learner">
              <LearnerExplore />
            </ProtectedRoute>
          }
        />

        <Route
          path="/learner/leaderboard"
          element={
            <ProtectedRoute allowedRole="learner">
              <Leaderboard role="learner" />
            </ProtectedRoute>
          }
        />

        <Route
          path="/learner/course/:courseId/lesson/:lessonId"
          element={
            <ProtectedRoute allowedRole="learner">
              <LessonPlayer />
            </ProtectedRoute>
          }
        />

        <Route
          path="/learner/course/:courseId"
          element={
            <ProtectedRoute allowedRole="learner">
              <CourseDetail />
            </ProtectedRoute>
          }
        />

        <Route
          path="/learner/settings"
          element={
            <ProtectedRoute allowedRole="learner">
              <AccountSettings role="learner" />
            </ProtectedRoute>
          }
        />

        <Route
          path="/learner/calendar"
          element={
            <ProtectedRoute allowedRole="learner">
              <LearnerCalendar />
            </ProtectedRoute>
          }
        />


        {/* =================================================
            LEARNER EXAM HISTORY
        ================================================= */}

        <Route
          path="/exam-history"
          element={
            <ProtectedRoute allowedRole="learner">
              <LearnerExamHistory />
            </ProtectedRoute>
          }
        />


        {/* =================================================
            OLD LEARNER EXAM URLS
        ================================================= */}

        <Route
          path="/learner/exams"
          element={
            <Navigate
              to="/exams"
              replace
            />
          }
        />

        <Route
          path="/learner/assignments"
          element={
            <Navigate
              to="/exams"
              replace
            />
          }
        />

        <Route
          path="/learner/assessments"
          element={
            <Navigate
              to="/exams"
              replace
            />
          }
        />


        {/* =================================================
            OTHER LEARNER PAGES
        ================================================= */}

        <Route
          path="/learner/*"
          element={
            <ComingSoon
              role="learner"
            />
          }
        />


        {/* =================================================
            FALLBACK
        ================================================= */}

        <Route
          path="*"
          element={
            <Navigate
              to="/login"
              replace
            />
          }
        />

        </Routes>
      </NotificationProvider>
    </AuthProvider>
  )
}