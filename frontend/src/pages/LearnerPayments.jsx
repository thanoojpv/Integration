import React, { useEffect, useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import { apiRequest } from "../services/api";

export default function LearnerPayments() {
  const [payments, setPayments] = useState([]);
  const [invoices, setInvoices] = useState([]);

  const [summary, setSummary] = useState({
    total_paid: 0,
    payment_count: 0,
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // =====================================================
  // LOAD PAYMENTS + INVOICES
  // =====================================================

  async function loadData() {
    try {
      setLoading(true);
      setError("");

      const [paymentsData, invoicesData] = await Promise.all([
        apiRequest("/api/learner/payments?limit=100"),
        apiRequest("/api/learner/invoices?limit=100"),
      ]);

      setPayments(paymentsData?.payments || []);

      setInvoices(invoicesData?.invoices || []);

      setSummary(
        paymentsData?.summary || {
          total_paid: 0,
          payment_count: 0,
        }
      );
    } catch (err) {
      console.error("Payments page load error:", err);

      setError(
        err?.message ||
          "Failed to load payment information"
      );
    } finally {
      setLoading(false);
    }
  }

  // =====================================================
  // INITIAL LOAD
  // =====================================================

  useEffect(() => {
    loadData();
  }, []);

  // =====================================================
  // DOWNLOAD INVOICE PDF
  // =====================================================

  async function downloadInvoice(
    invoiceId,
    invoiceNumber
  ) {
    try {
      const token =
        localStorage.getItem("access_token");

      if (!token) {
        throw new Error(
          "You are not logged in"
        );
      }

      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/learner/invoices/${invoiceId}/pdf`,
        {
          method: "GET",

          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        let message =
          "Failed to download invoice";

        try {
          const data =
            await response.json();

          message =
            data?.message ||
            data?.error ||
            message;
        } catch {
          // Ignore JSON parsing error
        }

        throw new Error(message);
      }

      const blob =
        await response.blob();

      const url =
        window.URL.createObjectURL(blob);

      const link =
        document.createElement("a");

      link.href = url;

      link.download =
        `${invoiceNumber}.pdf`;

      document.body.appendChild(link);

      link.click();

      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(
        "Invoice download error:",
        err
      );

      alert(
        err?.message ||
          "Failed to download invoice"
      );
    }
  }

  // =====================================================
  // FORMAT CURRENCY
  // =====================================================

  function formatCurrency(amount) {
    return `₹${Number(amount || 0).toLocaleString(
      "en-IN",
      {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }
    )}`;
  }

  // =====================================================
  // FORMAT DATE
  // =====================================================

  function formatDate(date) {
    if (!date) {
      return "-";
    }

    const parsedDate =
      new Date(date);

    if (Number.isNaN(parsedDate.getTime())) {
      return "-";
    }

    return parsedDate.toLocaleDateString(
      "en-IN",
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
      }
    );
  }

  // =====================================================
  // PAGE
  // =====================================================

  return (
    <DashboardLayout role="learner">

      <div className="payments-page">

        {/* =================================================
            HEADER
        ================================================= */}

        <div className="page-header">

          <div>
            <h1>
              Payments & Invoices
            </h1>

            <p>
              View your payment history
              and download your invoices.
            </p>
          </div>

          <button
            className="refresh-button"
            onClick={loadData}
            disabled={loading}
          >
            {loading
              ? "Refreshing..."
              : "Refresh"}
          </button>

        </div>


        {/* =================================================
            ERROR
        ================================================= */}

        {error && (
          <div className="error-card">
            {error}
          </div>
        )}


        {/* =================================================
            LOADING
        ================================================= */}

        {loading ? (

          <div className="state-card">
            Loading payment information...
          </div>

        ) : (

          <>

            {/* =============================================
                SUMMARY
            ============================================= */}

            <div className="summary-grid">

              <div className="summary-card">

                <div className="summary-icon">
                  💰
                </div>

                <div className="summary-label">
                  Total Paid
                </div>

                <div className="summary-value">
                  {formatCurrency(
                    summary.total_paid
                  )}
                </div>

              </div>


              <div className="summary-card">

                <div className="summary-icon">
                  💳
                </div>

                <div className="summary-label">
                  Payments
                </div>

                <div className="summary-value">
                  {summary.payment_count}
                </div>

              </div>


              <div className="summary-card">

                <div className="summary-icon">
                  🧾
                </div>

                <div className="summary-label">
                  Invoices
                </div>

                <div className="summary-value">
                  {invoices.length}
                </div>

              </div>

            </div>


            {/* =============================================
                PAYMENT HISTORY
            ============================================= */}

            <section className="content-card">

              <div className="section-header">

                <div>
                  <h2>
                    Payment History
                  </h2>

                  <p>
                    Your completed and recorded payments.
                  </p>
                </div>

              </div>


              {payments.length === 0 ? (

                <div className="empty-state">

                  <div className="empty-icon">
                    💳
                  </div>

                  <h3>
                    No payments found
                  </h3>

                  <p>
                    Your payment history
                    will appear here.
                  </p>

                </div>

              ) : (

                <div className="table-wrapper">

                  <table>

                    <thead>

                      <tr>
                        <th>
                          Course
                        </th>

                        <th>
                          Amount
                        </th>

                        <th>
                          Method
                        </th>

                        <th>
                          Status
                        </th>

                        <th>
                          Date
                        </th>
                      </tr>

                    </thead>


                    <tbody>

                      {payments.map(
                        (payment) => (

                          <tr
                            key={
                              payment.id
                            }
                          >

                            <td>

                              <div className="course-cell">

                                <strong>
                                  {
                                    payment.course_title ||
                                    "Legacy Payment"
                                  }
                                </strong>

                                {payment.course_id && (
                                  <span>
                                    {
                                      payment.course_id
                                    }
                                  </span>
                                )}

                              </div>

                            </td>


                            <td>

                              <strong className="amount">
                                {formatCurrency(
                                  payment.amount
                                )}
                              </strong>

                            </td>


                            <td>
                              <span className="method">
                                {
                                  payment.payment_method ||
                                  "-"
                                }
                              </span>
                            </td>


                            <td>

                              <span
                                className={`status-badge ${
                                  payment.status ===
                                  "paid"
                                    ? "status-paid"
                                    : "status-other"
                                }`}
                              >
                                {
                                  payment.status ||
                                  "unknown"
                                }
                              </span>

                            </td>


                            <td>
                              {formatDate(
                                payment.payment_date
                              )}
                            </td>

                          </tr>

                        )
                      )}

                    </tbody>

                  </table>

                </div>

              )}

            </section>


            {/* =============================================
                INVOICES
            ============================================= */}

            <section className="content-card">

              <div className="section-header">

                <div>
                  <h2>
                    Invoices
                  </h2>

                  <p>
                    Download your payment invoices as PDF.
                  </p>
                </div>

              </div>


              {invoices.length === 0 ? (

                <div className="empty-state">

                  <div className="empty-icon">
                    🧾
                  </div>

                  <h3>
                    No invoices found
                  </h3>

                  <p>
                    Your invoices will
                    appear here after payments.
                  </p>

                </div>

              ) : (

                <div className="table-wrapper">

                  <table>

                    <thead>

                      <tr>

                        <th>
                          Invoice Number
                        </th>

                        <th>
                          Amount
                        </th>

                        <th>
                          Date
                        </th>

                        <th>
                          Status
                        </th>

                        <th>
                          Action
                        </th>

                      </tr>

                    </thead>


                    <tbody>

                      {invoices.map(
                        (invoice) => (

                          <tr
                            key={
                              invoice.id
                            }
                          >

                            <td>

                              <strong>
                                {
                                  invoice.invoice_number
                                }
                              </strong>

                            </td>


                            <td>

                              <strong className="amount">
                                {formatCurrency(
                                  invoice.amount
                                )}
                              </strong>

                            </td>


                            <td>
                              {formatDate(
                                invoice.invoice_date
                              )}
                            </td>


                            <td>

                              <span
                                className={`status-badge ${
                                  invoice.status ===
                                  "paid"
                                    ? "status-paid"
                                    : "status-other"
                                }`}
                              >
                                {
                                  invoice.status ||
                                  "unknown"
                                }
                              </span>

                            </td>


                            <td>

                              <button
                                className="download-button"
                                onClick={() =>
                                  downloadInvoice(
                                    invoice.id,
                                    invoice.invoice_number
                                  )
                                }
                              >
                                📄 Download PDF
                              </button>

                            </td>

                          </tr>

                        )
                      )}

                    </tbody>

                  </table>

                </div>

              )}

            </section>

          </>

        )}


        {/* =================================================
            STYLES
        ================================================= */}

        <style>{`

          .payments-page {
            padding: 28px;
            max-width: 1400px;
            margin: 0 auto;
          }


          .page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
            margin-bottom: 24px;
          }


          .page-header h1 {
            margin: 0 0 7px;
            font-size: 30px;
            font-weight: 750;
            color: #111827;
          }


          .page-header p {
            margin: 0;
            color: #6b7280;
            font-size: 15px;
          }


          .refresh-button,
          .download-button {
            border: none;
            border-radius: 9px;
            padding: 10px 16px;
            cursor: pointer;
            font-weight: 650;
            transition:
              transform 0.15s ease,
              opacity 0.15s ease;
          }


          .refresh-button {
            background: #111827;
            color: white;
          }


          .refresh-button:hover:not(:disabled) {
            transform: translateY(-1px);
          }


          .refresh-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
          }


          .summary-grid {
            display: grid;
            grid-template-columns:
              repeat(3, 1fr);
            gap: 18px;
            margin-bottom: 24px;
          }


          .summary-card {
            position: relative;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 22px;
            box-shadow:
              0 2px 8px
              rgba(15, 23, 42, 0.04);
          }


          .summary-icon {
            font-size: 24px;
            margin-bottom: 12px;
          }


          .summary-label {
            color: #6b7280;
            font-size: 14px;
            margin-bottom: 7px;
          }


          .summary-value {
            font-size: 27px;
            font-weight: 750;
            color: #111827;
          }


          .content-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 22px;
            margin-bottom: 24px;
            box-shadow:
              0 2px 8px
              rgba(15, 23, 42, 0.03);
          }


          .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
          }


          .section-header h2 {
            margin: 0 0 5px;
            font-size: 20px;
            color: #111827;
          }


          .section-header p {
            margin: 0;
            color: #6b7280;
            font-size: 14px;
          }


          .table-wrapper {
            width: 100%;
            overflow-x: auto;
          }


          table {
            width: 100%;
            border-collapse: collapse;
            min-width: 720px;
          }


          th,
          td {
            padding: 14px 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
            white-space: nowrap;
          }


          th {
            font-size: 12px;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            background: #f9fafb;
          }


          td {
            font-size: 14px;
            color: #374151;
          }


          tbody tr:hover {
            background: #f9fafb;
          }


          .course-cell {
            display: flex;
            flex-direction: column;
            gap: 4px;
          }


          .course-cell strong {
            color: #111827;
          }


          .course-cell span {
            font-size: 12px;
            color: #9ca3af;
          }


          .amount {
            color: #111827;
            font-weight: 700;
          }


          .method {
            text-transform: uppercase;
            font-size: 13px;
            font-weight: 600;
          }


          .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 5px 10px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 750;
            text-transform: uppercase;
            letter-spacing: 0.03em;
          }


          .status-paid {
            background: #dcfce7;
            color: #166534;
          }


          .status-other {
            background: #f3f4f6;
            color: #374151;
          }


          .download-button {
            background: #2563eb;
            color: white;
          }


          .download-button:hover {
            opacity: 0.9;
            transform: translateY(-1px);
          }


          .state-card,
          .empty-state,
          .error-card {
            padding: 28px;
            border-radius: 12px;
            text-align: center;
          }


          .state-card {
            background: #f9fafb;
            color: #6b7280;
          }


          .empty-state {
            background: #f9fafb;
            color: #6b7280;
          }


          .empty-icon {
            font-size: 32px;
            margin-bottom: 10px;
          }


          .empty-state h3 {
            margin: 0 0 6px;
            color: #374151;
            font-size: 17px;
          }


          .empty-state p {
            margin: 0;
            color: #9ca3af;
            font-size: 14px;
          }


          .error-card {
            background: #fee2e2;
            color: #991b1b;
            margin-bottom: 20px;
            font-weight: 600;
          }


          @media (max-width: 800px) {

            .summary-grid {
              grid-template-columns: 1fr;
            }


            .page-header {
              align-items: flex-start;
              flex-direction: column;
            }


            .payments-page {
              padding: 16px;
            }

          }

        `}</style>

      </div>

    </DashboardLayout>
  );
}