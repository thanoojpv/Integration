import React, { useEffect, useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import { apiRequest } from "../services/api";

export default function AdminReports() {
    const [reports, setReports] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const loadReports = async () => {
        try {
            setLoading(true);
            setError("");

            const data = await apiRequest(
                "/api/admin/reports/overview"
            );

            setReports(data);
        } catch (err) {
            setError(
                err?.message ||
                "Unable to load reports"
            );
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadReports();
    }, []);

    if (loading) {
        return (
            <DashboardLayout role="admin">
                <div style={styles.page}>
                    <div style={styles.stateCard}>
                        Loading reports...
                    </div>
                </div>
            </DashboardLayout>
        );
    }

    if (error) {
        return (
            <DashboardLayout role="admin">
                <div style={styles.page}>
                    <div style={styles.header}>
                        <div>
                            <h1 style={styles.title}>
                                Reports & Analytics
                            </h1>
                            <p style={styles.subtitle}>
                                Overview of your LMS performance
                            </p>
                        </div>

                        <button
                            style={styles.refreshButton}
                            onClick={loadReports}
                        >
                            ↻ Refresh
                        </button>
                    </div>

                    <div style={styles.errorCard}>
                        {error}
                    </div>
                </div>
            </DashboardLayout>
        );
    }

    const users = reports?.users || {};
    const courses = reports?.courses || {};
    const enrollments = reports?.enrollments || {};
    const payments = reports?.payments || {};
    const revenue = reports?.revenue || {};
    const invoices = reports?.invoices || {};
    const certificates = reports?.certificates || {};
    const progress = reports?.progress || {};

    return (
        <DashboardLayout role="admin">
            <div style={styles.page}>

                {/* HEADER */}
                <div style={styles.header}>
                    <div>
                        <h1 style={styles.title}>
                            Reports & Analytics
                        </h1>

                        <p style={styles.subtitle}>
                            Overview of your LMS performance
                        </p>
                    </div>

                    <button
                        style={styles.refreshButton}
                        onClick={loadReports}
                    >
                        ↻ Refresh
                    </button>
                </div>

                {/* TOP STAT CARDS */}
                <div style={styles.grid}>

                    <StatCard
                        icon="👥"
                        title="Total Users"
                        value={users.total ?? 0}
                    />

                    <StatCard
                        icon="🎓"
                        title="Learners"
                        value={users.learners ?? 0}
                    />

                    <StatCard
                        icon="👨‍🏫"
                        title="Trainers"
                        value={users.trainers ?? 0}
                    />

                    <StatCard
                        icon="📚"
                        title="Courses"
                        value={courses.total ?? 0}
                    />

                    <StatCard
                        icon="💰"
                        title="Total Revenue"
                        value={`₹${Number(
                            revenue.total_paid || 0
                        ).toLocaleString("en-IN")}`}
                    />

                    <StatCard
                        icon="🎓"
                        title="Enrollments"
                        value={enrollments.total ?? 0}
                    />

                    <StatCard
                        icon="🏆"
                        title="Certificates"
                        value={certificates.total ?? 0}
                    />

                    <StatCard
                        icon="📈"
                        title="Average Progress"
                        value={`${Number(
                            progress.average || 0
                        ).toFixed(2)}%`}
                    />

                </div>

                {/* USER STATISTICS */}
                <ReportSection
                    title="👥 User Statistics"
                >
                    <div style={styles.detailGrid}>

                        <DetailItem
                            label="Total Users"
                            value={users.total}
                        />

                        <DetailItem
                            label="Active Users"
                            value={users.active}
                        />

                        <DetailItem
                            label="Inactive Users"
                            value={users.inactive}
                        />

                        <DetailItem
                            label="Learners"
                            value={users.learners}
                        />

                        <DetailItem
                            label="Trainers"
                            value={users.trainers}
                        />

                    </div>
                </ReportSection>

                {/* COURSE STATISTICS */}
                <ReportSection
                    title="📚 Course Statistics"
                >
                    <div style={styles.detailGrid}>

                        <DetailItem
                            label="Total Courses"
                            value={courses.total}
                        />

                        <DetailItem
                            label="Published"
                            value={courses.published}
                        />

                        <DetailItem
                            label="Unpublished"
                            value={courses.unpublished}
                        />

                    </div>
                </ReportSection>

                {/* ENROLLMENT STATISTICS */}
                <ReportSection
                    title="🎓 Enrollment Statistics"
                >
                    <div style={styles.detailGrid}>

                        <DetailItem
                            label="Total Enrollments"
                            value={enrollments.total}
                        />

                        <DetailItem
                            label="Active"
                            value={enrollments.active}
                        />

                        <DetailItem
                            label="Payment Pending"
                            value={
                                enrollments.payment_pending
                            }
                        />

                        <DetailItem
                            label="Completed"
                            value={enrollments.completed}
                        />

                    </div>
                </ReportSection>

                {/* PAYMENT STATISTICS */}
                <ReportSection
                    title="💳 Payment Statistics"
                >
                    <div style={styles.detailGrid}>

                        <DetailItem
                            label="Total Payments"
                            value={payments.total}
                        />

                        <DetailItem
                            label="Paid"
                            value={payments.paid}
                        />

                        <DetailItem
                            label="Pending"
                            value={payments.pending}
                        />

                        <DetailItem
                            label="Failed"
                            value={payments.failed}
                        />

                        <DetailItem
                            label="Total Revenue"
                            value={`₹${Number(
                                revenue.total_paid || 0
                            ).toLocaleString("en-IN")}`}
                        />

                        <DetailItem
                            label="Pending Revenue"
                            value={`₹${Number(
                                revenue.pending || 0
                            ).toLocaleString("en-IN")}`}
                        />

                    </div>
                </ReportSection>

                {/* INVOICE STATISTICS */}
                <ReportSection
                    title="🧾 Invoice Statistics"
                >
                    <div style={styles.detailGrid}>

                        <DetailItem
                            label="Total Invoices"
                            value={invoices.total}
                        />

                        <DetailItem
                            label="Paid Invoices"
                            value={invoices.paid}
                        />

                        <DetailItem
                            label="Unpaid Invoices"
                            value={invoices.unpaid}
                        />

                    </div>
                </ReportSection>

                {/* CERTIFICATES */}
                <ReportSection
                    title="🏆 Certificate Statistics"
                >
                    <div style={styles.detailGrid}>

                        <DetailItem
                            label="Total Certificates"
                            value={
                                certificates.total
                            }
                        />

                        <DetailItem
                            label="Valid Certificates"
                            value={
                                certificates.valid
                            }
                        />

                    </div>
                </ReportSection>

                {/* PROGRESS */}
                <ReportSection
                    title="📈 Learning Progress"
                >
                    <div style={styles.progressContainer}>

                        <div style={styles.progressHeader}>
                            <span>
                                Average Course Progress
                            </span>

                            <strong>
                                {Number(
                                    progress.average || 0
                                ).toFixed(2)}%
                            </strong>
                        </div>

                        <div style={styles.progressTrack}>
                            <div
                                style={{
                                    ...styles.progressBar,
                                    width: `${Math.min(
                                        Number(
                                            progress.average || 0
                                        ),
                                        100
                                    )}%`,
                                }}
                            />
                        </div>

                        <p style={styles.progressText}>
                            {progress.completed_enrollments ?? 0}
                            {" "}
                            enrollments have reached
                            100% completion.
                        </p>

                    </div>
                </ReportSection>

            </div>
        </DashboardLayout>
    );
}


/* =========================================================
   STAT CARD
========================================================= */

function StatCard({
    icon,
    title,
    value,
}) {
    return (
        <div style={styles.statCard}>

            <div style={styles.statIcon}>
                {icon}
            </div>

            <div>
                <div style={styles.statTitle}>
                    {title}
                </div>

                <div style={styles.statValue}>
                    {value}
                </div>
            </div>

        </div>
    );
}


/* =========================================================
   REPORT SECTION
========================================================= */

function ReportSection({
    title,
    children,
}) {
    return (
        <section style={styles.section}>

            <h2 style={styles.sectionTitle}>
                {title}
            </h2>

            {children}

        </section>
    );
}


/* =========================================================
   DETAIL ITEM
========================================================= */

function DetailItem({
    label,
    value,
}) {
    return (
        <div style={styles.detailItem}>

            <span style={styles.detailLabel}>
                {label}
            </span>

            <strong style={styles.detailValue}>
                {value ?? 0}
            </strong>

        </div>
    );
}


/* =========================================================
   STYLES
========================================================= */

const styles = {

    page: {
        padding: "28px",
        maxWidth: "1400px",
        margin: "0 auto",
    },

    header: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: "20px",
        marginBottom: "28px",
    },

    title: {
        margin: 0,
        fontSize: "30px",
        fontWeight: 800,
    },

    subtitle: {
        marginTop: "7px",
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

    grid: {
        display: "grid",
        gridTemplateColumns:
            "repeat(auto-fit, minmax(210px, 1fr))",
        gap: "16px",
        marginBottom: "24px",
    },

    statCard: {
        background: "#ffffff",
        border: "1px solid #e5e7eb",
        borderRadius: "16px",
        padding: "20px",
        display: "flex",
        alignItems: "center",
        gap: "15px",
        boxShadow:
            "0 4px 14px rgba(15, 23, 42, 0.05)",
    },

    statIcon: {
        width: "48px",
        height: "48px",
        borderRadius: "12px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#f1f5f9",
        fontSize: "24px",
        flexShrink: 0,
    },

    statTitle: {
        fontSize: "13px",
        color: "#64748b",
        marginBottom: "5px",
    },

    statValue: {
        fontSize: "25px",
        fontWeight: 800,
        color: "#111827",
    },

    section: {
        background: "#ffffff",
        border: "1px solid #e5e7eb",
        borderRadius: "16px",
        padding: "22px",
        marginBottom: "20px",
        boxShadow:
            "0 4px 14px rgba(15, 23, 42, 0.04)",
    },

    sectionTitle: {
        margin: "0 0 18px",
        fontSize: "20px",
        fontWeight: 800,
    },

    detailGrid: {
        display: "grid",
        gridTemplateColumns:
            "repeat(auto-fit, minmax(180px, 1fr))",
        gap: "12px",
    },

    detailItem: {
        background: "#f8fafc",
        borderRadius: "12px",
        padding: "16px",
        display: "flex",
        flexDirection: "column",
        gap: "7px",
    },

    detailLabel: {
        color: "#64748b",
        fontSize: "13px",
    },

    detailValue: {
        fontSize: "21px",
        color: "#111827",
    },

    progressContainer: {
        padding: "5px 0",
    },

    progressHeader: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "10px",
        fontSize: "14px",
    },

    progressTrack: {
        width: "100%",
        height: "14px",
        borderRadius: "999px",
        background: "#e5e7eb",
        overflow: "hidden",
    },

    progressBar: {
        height: "100%",
        borderRadius: "999px",
        background: "#2563eb",
        transition: "width 0.4s ease",
    },

    progressText: {
        color: "#64748b",
        fontSize: "13px",
        marginTop: "10px",
    },

    stateCard: {
        padding: "40px",
        textAlign: "center",
        background: "#ffffff",
        borderRadius: "16px",
        border: "1px solid #e5e7eb",
        color: "#64748b",
    },

    errorCard: {
        padding: "20px",
        background: "#fef2f2",
        border: "1px solid #fecaca",
        borderRadius: "12px",
        color: "#b91c1c",
    },

};