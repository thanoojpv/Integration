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
import AdminBatches from './pages/AdminBatches'



// =========================================================
// TRAINER PAGES
// =========================================================

import TrainerExams from './pages/TrainerExams'
import TrainerDashboard from './pages/TrainerDashboard'
import TrainerCourseDetail from './pages/TrainerCourseDetail'
import TrainerAttendance from './pages/TrainerAttendance'
import AdminAttendance from './pages/AdminAttendance'
import AdminCsvImport from './pages/AdminCsvImport'
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
import CertificateVerification from './pages/CertificateVerification'
import LearnerAssessments from './pages/LearnerAssessments'
import LearnerCalendar from './pages/LearnerCalendar'
import TrainerCalendar from "./pages/TrainerCalendar";
import LearnerCodingExam from './pages/LearnerCodingExam'
import LearnerExamHistory from './pages/LearnerExamHistory'
import LearnerPayments from "./pages/LearnerPayments";


// =========================================================
// COMMON PAGES
// =========================================================

import AccountSettings from './pages/AccountSettings'
import ComingSoon from './pages/ComingSoon'
import AdminAuditLogs from './pages/AdminAuditLogs'
import AdminPayments from './pages/AdminPayments'
import LearnerAttendance from './pages/LearnerAttendance'
import AdminReports from "./pages/AdminReports";
import TrainerStudents from "./pages/TrainerStudents";
import TrainerAnalytics from "./pages/TrainerAnalytics";
import TrainerQuestionBank from "./pages/TrainerQuestionBank";
import TrainerMixedExams from "./pages/TrainerMixedExams";
import TrainerMixedExamManage from "./pages/TrainerMixedExamManage";
import MixedExamCandidate from "./pages/MixedExamCandidate";
import Community from "./pages/Community";


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
            PUBLIC CERTIFICATE VERIFICATION
        ================================================= */}
        <Route
          path="/verify/:certificateNumber"
          element={<CertificateVerification />}
        />

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
          path="/admin/batches"
          element={
            <ProtectedRoute allowedRole="admin">
              <AdminBatches />
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
          path="/admin/attendance"
          element={
            <ProtectedRoute allowedRole="admin">
              <AdminAttendance />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/csv-import"
          element={
            <ProtectedRoute allowedRole="admin">
              <AdminCsvImport />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/audit-logs"
          element={
            <ProtectedRoute allowedRole="admin">
              <AdminAuditLogs />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/payments"
          element={
            <ProtectedRoute allowedRole="admin">
              <AdminPayments />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/reports"
          element={
            <ProtectedRoute allowedRole="admin">
              <AdminReports />
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
          path="/trainer/attendance"
          element={
            <ProtectedRoute allowedRole="trainer">
              <TrainerAttendance />
            </ProtectedRoute>
          }
        />
        <Route
          path="/trainer/students"
          element={
            <ProtectedRoute allowedRole="trainer">
              <TrainerStudents />
            </ProtectedRoute>
          }
        />
        <Route
          path="/trainer/analytics"
          element={
            <ProtectedRoute allowedRole="trainer">
              <TrainerAnalytics />
            </ProtectedRoute>
          }
        />
        <Route
          path="/trainer/calendar"
          element={
            <ProtectedRoute allowedRole="trainer">
              <TrainerCalendar />
            </ProtectedRoute>
          }
        />

        <Route
          path="/trainer/question-bank"
          element={
            <TrainerQuestionBank />
          }
        />
        <Route
          path="/trainer/mixed-exams"
          element={
            <TrainerMixedExams />
          }
        />

        <Route
          path="/trainer/mixed-exams/:examId"
          element={
            <TrainerMixedExamManage />
          }
        />
        <Route
          path="/mixed-exam/invite/:inviteCode"
          element={
            <MixedExamCandidate />
          }
        />

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
          path="/learner/attendance"
          element={
            <ProtectedRoute allowedRole="learner">
              <LearnerAttendance />
            </ProtectedRoute>
          }
        />

        <Route
          path="/learner/payments"
          element={
            <ProtectedRoute allowedRole="learner">
              <LearnerPayments />
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

        <Route
          path="/learner/community"
          element={
            <ProtectedRoute allowedRole="learner">
              <Community />
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