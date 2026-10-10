import React, { useEffect, useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import { apiRequest } from "../services/api";

export default function TrainerStudents() {
    const [students, setStudents] = useState([]);
    const [search, setSearch] = useState("");
    const [needsAttention, setNeedsAttention] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const loadStudents = async () => {
        try {
            setLoading(true);
            setError("");

            const params = new URLSearchParams();

            if (search.trim()) {
                params.set("search", search.trim());
            }

            if (needsAttention) {
                params.set(
                    "needs_attention",
                    "true"
                );
            }

            const query = params.toString();

            const data = await apiRequest(
                `/api/trainer/students${
                    query ? `?${query}` : ""
                }`
            );

            setStudents(
                Array.isArray(data?.students)
                    ? data.students
                    : []
            );
        } catch (err) {
            setError(
                err?.message ||
                "Unable to load students"
            );
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const timer = setTimeout(() => {
            loadStudents();
        }, 300);

        return () => clearTimeout(timer);
    }, [search, needsAttention]);

    const formatDate = (value) => {
        if (!value) {
            return "Never";
        }

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return "Unknown";
        }

        return date.toLocaleDateString(
            "en-IN",
            {
                day: "2-digit",
                month: "short",
                year: "numeric",
            }
        );
    };

    const getProgressClass = (progress) => {
        if (progress >= 80) {
            return styles.progressGood;
        }

        if (progress >= 40) {
            return styles.progressMedium;
        }

        return styles.progressLow;
    };

    return (
        <DashboardLayout role="trainer">
            <div style={styles.page}>

                {/* HEADER */}
                <div style={styles.header}>
                    <div>
                        <h1 style={styles.title}>
                            Students
                        </h1>

                        <p style={styles.subtitle}>
                            View and manage learners
                            across your courses
                        </p>
                    </div>

                    <button
                        style={styles.refreshButton}
                        onClick={loadStudents}
                    >
                        ↻ Refresh
                    </button>
                </div>

                {/* FILTERS */}
                <div style={styles.filterCard}>

                    <div style={styles.searchWrapper}>
                        <span style={styles.searchIcon}>
                            🔍
                        </span>

                        <input
                            type="text"
                            placeholder="Search by name or email..."
                            value={search}
                            onChange={(event) =>
                                setSearch(
                                    event.target.value
                                )
                            }
                            style={styles.searchInput}
                        />
                    </div>

                    <label style={styles.checkboxLabel}>

                        <input
                            type="checkbox"
                            checked={needsAttention}
                            onChange={(event) =>
                                setNeedsAttention(
                                    event.target.checked
                                )
                            }
                        />

                        <span>
                            ⚠️ Needs attention
                        </span>

                    </label>

                </div>

                {/* ERROR */}
                {error && (
                    <div style={styles.errorCard}>
                        {error}
                    </div>
                )}

                {/* LOADING */}
                {loading && (
                    <div style={styles.stateCard}>
                        Loading students...
                    </div>
                )}

                {/* EMPTY */}
                {!loading &&
                    !error &&
                    students.length === 0 && (
                        <div style={styles.stateCard}>

                            <div style={styles.emptyIcon}>
                                👥
                            </div>

                            <h3>
                                No students found
                            </h3>

                            <p>
                                Try changing your
                                search or filters.
                            </p>

                        </div>
                    )}

                {/* TABLE */}
                {!loading &&
                    !error &&
                    students.length > 0 && (

                    <div style={styles.tableCard}>

                        <div style={styles.tableHeader}>
                            <strong>
                                Students
                            </strong>

                            <span>
                                {students.length}{" "}
                                student
                                {students.length !== 1
                                    ? "s"
                                    : ""}
                            </span>
                        </div>

                        <div style={styles.tableWrapper}>

                            <table
                                style={styles.table}
                            >

                                <thead>
                                    <tr>

                                        <th style={styles.th}>
                                            Student
                                        </th>

                                        <th style={styles.th}>
                                            Course
                                        </th>

                                        <th style={styles.th}>
                                            Progress
                                        </th>

                                        <th style={styles.th}>
                                            Score
                                        </th>

                                        <th style={styles.th}>
                                            Last Active
                                        </th>

                                        <th style={styles.th}>
                                            Status
                                        </th>

                                    </tr>
                                </thead>

                                <tbody>

                                    {students.map(
                                        (student) => {

                                            const progress =
                                                Number(
                                                    student.progress ||
                                                    0
                                                );

                                            return (
                                                <tr
                                                    key={
                                                        student.enrollment_id
                                                    }
                                                    style={
                                                        styles.tr
                                                    }
                                                >

                                                    {/* STUDENT */}
                                                    <td
                                                        style={
                                                            styles.td
                                                        }
                                                    >

                                                        <div
                                                            style={
                                                                styles.studentCell
                                                            }
                                                        >

                                                            <div
                                                                style={
                                                                    styles.avatar
                                                                }
                                                            >
                                                                {(
                                                                    student.name ||
                                                                    "S"
                                                                )
                                                                    .charAt(0)
                                                                    .toUpperCase()}
                                                            </div>

                                                            <div>

                                                                <div
                                                                    style={
                                                                        styles.studentName
                                                                    }
                                                                >
                                                                    {
                                                                        student.name ||
                                                                        "Learner"
                                                                    }
                                                                </div>

                                                                <div
                                                                    style={
                                                                        styles.studentEmail
                                                                    }
                                                                >
                                                                    {
                                                                        student.email
                                                                    }
                                                                </div>

                                                            </div>

                                                        </div>

                                                    </td>

                                                    {/* COURSE */}
                                                    <td
                                                        style={
                                                            styles.td
                                                        }
                                                    >
                                                        <span
                                                            style={
                                                                styles.courseName
                                                            }
                                                        >
                                                            {
                                                                student.course_title ||
                                                                "Unknown course"
                                                            }
                                                        </span>
                                                    </td>

                                                    {/* PROGRESS */}
                                                    <td
                                                        style={
                                                            styles.td
                                                        }
                                                    >

                                                        <div
                                                            style={
                                                                styles.progressCell
                                                            }
                                                        >

                                                            <div
                                                                style={
                                                                    styles.progressRow
                                                                }
                                                            >

                                                                <span>
                                                                    {
                                                                        progress
                                                                    }%
                                                                </span>

                                                            </div>

                                                            <div
                                                                style={
                                                                    styles.progressTrack
                                                                }
                                                            >

                                                                <div
                                                                    style={{
                                                                        ...styles.progressBar,
                                                                        ...getProgressClass(
                                                                            progress
                                                                        ),
                                                                        width: `${Math.min(
                                                                            progress,
                                                                            100
                                                                        )}%`,
                                                                    }}
                                                                />

                                                            </div>

                                                        </div>

                                                    </td>

                                                    {/* SCORE */}
                                                    <td
                                                        style={
                                                            styles.td
                                                        }
                                                    >

                                                        {student.score ===
                                                        null ||
                                                        student.score ===
                                                        undefined ? (
                                                            <span
                                                                style={
                                                                    styles.muted
                                                                }
                                                            >
                                                                —
                                                            </span>
                                                        ) : (
                                                            <strong>
                                                                {
                                                                    student.score
                                                                }%
                                                            </strong>
                                                        )}

                                                    </td>

                                                    {/* LAST ACTIVE */}
                                                    <td
                                                        style={
                                                            styles.td
                                                        }
                                                    >
                                                        <span
                                                            style={
                                                                student.last_active
                                                                    ? styles.date
                                                                    : styles.muted
                                                            }
                                                        >
                                                            {formatDate(
                                                                student.last_active
                                                            )}
                                                        </span>
                                                    </td>

                                                    {/* STATUS */}
                                                    <td
                                                        style={
                                                            styles.td
                                                        }
                                                    >

                                                        {student.needs_attention ? (
                                                            <span
                                                                style={
                                                                    styles.attentionBadge
                                                                }
                                                            >
                                                                ⚠️ Needs attention
                                                            </span>
                                                        ) : (
                                                            <span
                                                                style={
                                                                    styles.goodBadge
                                                                }
                                                            >
                                                                ✓ On track
                                                            </span>
                                                        )}

                                                    </td>

                                                </tr>
                                            );
                                        }
                                    )}

                                </tbody>

                            </table>

                        </div>

                    </div>
                )}

            </div>
        </DashboardLayout>
    );
}


/* =========================================================
   STYLES
========================================================= */

const styles = {

    page: {
        padding: "28px",
        maxWidth: "1500px",
        margin: "0 auto",
    },

    header: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: "20px",
        marginBottom: "24px",
    },

    title: {
        margin: 0,
        fontSize: "30px",
        fontWeight: 800,
        color: "#111827",
    },

    subtitle: {
        margin: "7px 0 0",
        color: "#64748b",
        fontSize: "15px",
    },

    refreshButton: {
        border: "none",
        borderRadius: "10px",
        padding: "11px 18px",
        background: "#111827",
        color: "#ffffff",
        fontWeight: 700,
        cursor: "pointer",
        fontSize: "14px",
    },

    filterCard: {
        background: "#ffffff",
        border: "1px solid #e5e7eb",
        borderRadius: "14px",
        padding: "16px",
        display: "flex",
        alignItems: "center",
        gap: "18px",
        marginBottom: "20px",
        boxShadow:
            "0 4px 14px rgba(15, 23, 42, 0.04)",
    },

    searchWrapper: {
        flex: 1,
        position: "relative",
        minWidth: 0,
    },

    searchIcon: {
        position: "absolute",
        left: "13px",
        top: "50%",
        transform: "translateY(-50%)",
        fontSize: "16px",
    },

    searchInput: {
        width: "100%",
        boxSizing: "border-box",
        border: "1px solid #d1d5db",
        borderRadius: "10px",
        padding: "12px 14px 12px 40px",
        outline: "none",
        fontSize: "14px",
    },

    checkboxLabel: {
        display: "flex",
        alignItems: "center",
        gap: "8px",
        whiteSpace: "nowrap",
        fontSize: "14px",
        fontWeight: 600,
        color: "#374151",
        cursor: "pointer",
    },

    errorCard: {
        background: "#fef2f2",
        border: "1px solid #fecaca",
        color: "#b91c1c",
        padding: "15px 18px",
        borderRadius: "12px",
        marginBottom: "20px",
    },

    stateCard: {
        background: "#ffffff",
        border: "1px solid #e5e7eb",
        borderRadius: "14px",
        padding: "50px",
        textAlign: "center",
        color: "#64748b",
    },

    emptyIcon: {
        fontSize: "42px",
        marginBottom: "10px",
    },

    tableCard: {
        background: "#ffffff",
        border: "1px solid #e5e7eb",
        borderRadius: "14px",
        overflow: "hidden",
        boxShadow:
            "0 4px 14px rgba(15, 23, 42, 0.04)",
    },

    tableHeader: {
        padding: "18px 20px",
        borderBottom: "1px solid #e5e7eb",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
    },

    tableWrapper: {
        overflowX: "auto",
    },

    table: {
        width: "100%",
        borderCollapse: "collapse",
        minWidth: "950px",
    },

    th: {
        textAlign: "left",
        padding: "14px 16px",
        background: "#f8fafc",
        color: "#64748b",
        fontSize: "12px",
        textTransform: "uppercase",
        letterSpacing: "0.04em",
        whiteSpace: "nowrap",
    },

    tr: {
        borderBottom: "1px solid #f1f5f9",
    },

    td: {
        padding: "15px 16px",
        verticalAlign: "middle",
        fontSize: "14px",
        color: "#334155",
    },

    studentCell: {
        display: "flex",
        alignItems: "center",
        gap: "11px",
        minWidth: "190px",
    },

    avatar: {
        width: "38px",
        height: "38px",
        borderRadius: "50%",
        background: "#e2e8f0",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontWeight: 800,
        color: "#334155",
        flexShrink: 0,
    },

    studentName: {
        fontWeight: 700,
        color: "#111827",
    },

    studentEmail: {
        marginTop: "3px",
        fontSize: "12px",
        color: "#64748b",
    },

    courseName: {
        fontWeight: 600,
        color: "#334155",
    },

    progressCell: {
        width: "130px",
    },

    progressRow: {
        display: "flex",
        justifyContent: "space-between",
        marginBottom: "5px",
        fontSize: "12px",
        fontWeight: 700,
    },

    progressTrack: {
        width: "100%",
        height: "7px",
        background: "#e5e7eb",
        borderRadius: "999px",
        overflow: "hidden",
    },

    progressBar: {
        height: "100%",
        borderRadius: "999px",
    },

    progressGood: {
        background: "#16a34a",
    },

    progressMedium: {
        background: "#f59e0b",
    },

    progressLow: {
        background: "#dc2626",
    },

    date: {
        whiteSpace: "nowrap",
    },

    muted: {
        color: "#94a3b8",
    },

    goodBadge: {
        display: "inline-block",
        padding: "5px 9px",
        borderRadius: "999px",
        background: "#dcfce7",
        color: "#166534",
        fontSize: "12px",
        fontWeight: 700,
        whiteSpace: "nowrap",
    },

    attentionBadge: {
        display: "inline-block",
        padding: "5px 9px",
        borderRadius: "999px",
        background: "#fef3c7",
        color: "#92400e",
        fontSize: "12px",
        fontWeight: 700,
        whiteSpace: "nowrap",
    },

};