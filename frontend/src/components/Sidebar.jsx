import React from 'react'
import { NavLink } from 'react-router-dom'

const NAV = {
  // =========================================================
  // ADMIN
  // =========================================================

  admin: [
    {
      to: '/admin',
      label: 'Dashboard',
      icon: '▦',
      end: true,
    },
    {
      to: '/admin/users',
      label: 'User Management',
      icon: '👥',
    },
    {
      to: '/admin/catalog',
      label: 'Course Catalog',
      icon: '📘',
    },
    {
      to: '/admin/create-accounts',
      label: 'Create Accounts',
      icon: '➕',
    },
    {
      to: '/admin/leaderboard',
      label: 'Leaderboard',
      icon: '🏆',
    },
    {
      to: '/admin/batches',
      label: 'Batches',
      icon: '🗂️',
    },
    {
      to: '/admin/attendance',
      label: 'Attendance',
      icon: '🗓️',
    },
    {
      to: '/admin/csv-import',
      label: 'Bulk CSV Import',
      icon: '📥',
    },
    {
      to: '/admin/certificates',
      label: 'Certificates',
      icon: '🏅',
    },
    {
      to: '/admin/audit-logs',
      label: 'Audit Logs',
      icon: '📝',
    },
    {
      to: '/admin/payments',
      label: 'Payments & Invoices',
      icon: '💳',
    },
    {
      to: '/admin/reports',
      label: 'Reports & Analytics',
      icon: '📄',
    },
    {
      to: '/admin/settings',
      label: 'Settings',
      icon: '⚙️',
    },
  ],

  // =========================================================
  // TRAINER
  // =========================================================

  trainer: [
    {
      to: '/trainer',
      label: 'Dashboard',
      icon: '▦',
      end: true,
    },
    {
      to: '/trainer/courses',
      label: 'My Courses',
      icon: '📘',
    },
    {
      to: '/trainer/create-course',
      label: 'Create Course',
      icon: '➕',
    },
    {
      to: '/trainer/students',
      label: 'Students',
      icon: '👥',
    },
    {
      to: '/exams',
      label: 'Exams',
      icon: '📝',
    },
    {
      to: '/trainer/coding-exams',
      label: 'Coding Exams',
      icon: '💻',
    },
    {
      to: '/trainer/analytics',
      label: 'Analytics',
      icon: '📊',
    },
    {
      to: '/trainer/calendar',
      label: 'Calendar',
      icon: '📅',
    },
    {
      to: '/trainer/question-bank',
      label: 'Question Bank',
      icon: '📚',
    },
    {
      to: '/trainer/mixed-exams',
      label: 'Mixed Exams',
      icon: '📝',
   },
    {
      to: '/trainer/leaderboard',
      label: 'Leaderboard',
      icon: '🏆',
    },
    {
      to: '/trainer/attendance',
      label: 'Attendance',
      icon: '📋',
    },
    

    {
      to: '/trainer/settings',
      label: 'Settings',
      icon: '⚙️',
    },
  ],

  // =========================================================
  // LEARNER
  // =========================================================

  learner: [
    {
      to: '/learner',
      label: 'Dashboard',
      icon: '▦',
      end: true,
    },
    {
      to: '/learner/my-learning',
      label: 'My Learning',
      icon: '📖',
    },
    {
      to: '/learner/explore',
      label: 'Explore Courses',
      icon: '🧭',
    },
    {
      to: '/exams',
      label: 'Exams',
      icon: '📝',
    },
    {
      to: '/coding-exam',
      label: 'Coding Exams',
      icon: '💻',
    },

    // =======================================================
    // EXAM HISTORY
    // =======================================================

    {
      to: '/exam-history',
      label: 'Exam History',
      icon: '📋',
    },

    {
      to: '/learner/calendar',
      label: 'Calendar',
      icon: '🗓️',
    },
    {
      to: '/learner/certificates',
      label: 'Certificates',
      icon: '🏅',
    },
    {
      to: '/learner/progress',
      label: 'Progress',
      icon: '📈',
    },
    {
      to: '/learner/attendance',
      label: 'Attendance',
      icon: '📋',
    },
    {
      to: '/learner/leaderboard',
      label: 'Leaderboard',
      icon: '🏆',
    },
    {
      to: '/learner/payments',
      label: 'Payments & Invoices',
      icon: '💳',
    },
    {
      to: '/learner/community',
      label: 'Community',
      icon: '💬',
    },
    {
      to: '/learner/settings',
      label: 'Settings',
      icon: '⚙️',
    },
  ],
}

export default function Sidebar({ role }) {
  const items = NAV[role] || []

  return (
    <aside className="sidebar">

      {/* =====================================================
          BRAND
      ===================================================== */}

      <div className="brand-badge">

        <span className="brand-mark">
          DS
        </span>

        <div>
          <div
            style={{
              fontSize: 14,
            }}
          >
            DevSprint LMS
          </div>

          <div
            style={{
              fontSize: 10,
              color: '#7280ad',
              fontWeight: 500,
            }}
          >
            SERVICES PVT. LTD.
          </div>
        </div>

      </div>

      {/* =====================================================
          NAVIGATION
      ===================================================== */}

      <nav>

        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `nav-item${isActive ? ' active' : ''}`
            }
          >

            <span className="ic">
              {item.icon}
            </span>

            <span>
              {item.label}
            </span>

          </NavLink>
        ))}

      </nav>

      {/* =====================================================
          SIDEBAR FOOTER
      ===================================================== */}

      <div className="sidebar-footer">

        <div className="ai-title">
          🤖 DevSprint AI
        </div>

        <p>
          Ask AI to summarize lessons or explain code errors!
        </p>

        <button
          type="button"
          className="btn btn-primary btn-full"
          style={{
            fontSize: 13,
            padding: '9px 0',
          }}
        >
          Launch Assistant
        </button>

      </div>

    </aside>
  )
}