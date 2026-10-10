import React, { useEffect, useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import { apiRequest } from "../services/api";

export default function AdminPayments() {
  const [payments, setPayments] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [totalMoneyCollected, setTotalMoneyCollected] = useState(0);

  const [paymentPagination, setPaymentPagination] = useState({
    page: 1,
    pages: 1,
    total: 0,
  });

  const [invoicePagination, setInvoicePagination] = useState({
    page: 1,
    pages: 1,
    total: 0,
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [paymentPage, setPaymentPage] = useState(1);
  const [invoicePage, setInvoicePage] = useState(1);

  async function loadPayments(page = paymentPage) {
    const data = await apiRequest(
      `/api/admin/payments?page=${page}&limit=20`
    );

    setPayments(data.payments || []);
    setTotalMoneyCollected(
      Number(data.total_money_collected || 0)
    );
    setPaymentPagination(
      data.pagination || {
        page,
        pages: 1,
        total: 0,
      }
    );
  }

  async function loadInvoices(page = invoicePage) {
    const data = await apiRequest(
      `/api/admin/invoices?page=${page}&limit=20`
    );

    setInvoices(data.invoices || []);
    setInvoicePagination(
      data.pagination || {
        page,
        pages: 1,
        total: 0,
      }
    );
  }

  async function loadData() {
    try {
      setLoading(true);
      setError("");

      await Promise.all([
        loadPayments(paymentPage),
        loadInvoices(invoicePage),
      ]);
    } catch (err) {
      setError(
        err.message ||
        "Failed to load payment information"
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [paymentPage, invoicePage]);

  function formatCurrency(amount) {
    return `₹${Number(amount || 0).toLocaleString("en-IN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }

  function formatDate(date) {
    if (!date) {
      return "-";
    }

    return new Date(date).toLocaleDateString(
      "en-IN",
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
      }
    );
  }

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

      const response =
        await fetch(
          `${import.meta.env.VITE_API_BASE_URL}/api/admin/invoices/${invoiceId}/pdf`,
          {
            method: "GET",
            headers: {
              Authorization:
                `Bearer ${token}`,
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

      alert(
        err.message ||
        "Failed to download invoice"
      );

    }
  }

  return (
    <DashboardLayout role="admin">

      <div className="admin-payments-page">

        {/* =================================================
            HEADER
        ================================================= */}

        <div className="page-header">

          <div>
            <h1>
              Payments & Invoices
            </h1>

            <p>
              Manage learner payments and invoices.
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
            SUMMARY
        ================================================= */}

        {!loading && (
          <div className="summary-grid">

            <div className="summary-card">

              <div className="summary-icon">
                💳
              </div>

              <div className="summary-label">
                Total Payments
              </div>

              <div className="summary-value">
                {paymentPagination.total}
              </div>

            </div>


            <div className="summary-card">

              <div className="summary-icon">
                🧾
              </div>

              <div className="summary-label">
                Total Invoices
              </div>

              <div className="summary-value">
                {invoicePagination.total}
              </div>

            </div>


            <div className="summary-card">

              <div className="summary-icon">
                💰
              </div>

              <div className="summary-label">
                Total Money Collected
              </div>

              <div className="summary-value">
                {formatCurrency(totalMoneyCollected)}
              </div>

            </div>

          </div>
        )}


        {/* =================================================
            LOADING
        ================================================= */}

        {loading ? (

          <div className="state-card">
            Loading payments and invoices...
          </div>

        ) : (

          <>

            {/* =================================================
                PAYMENTS
            ================================================= */}

            <section className="content-card">

              <div className="section-header">

                <div>
                  <h2>
                    Payment History
                  </h2>

                  <p>
                    View all learner payment transactions.
                  </p>
                </div>

              </div>


              {payments.length === 0 ? (

                <div className="empty-state">
                  No payments found.
                </div>

              ) : (

                <div className="table-wrapper">

                  <table>

                    <thead>

                      <tr>
                        <th>Learner</th>
                        <th>Course</th>
                        <th>Amount</th>
                        <th>Method</th>
                        <th>Status</th>
                        <th>Date</th>
                      </tr>

                    </thead>


                    <tbody>

                      {payments.map(
                        (payment) => (

                          <tr
                            key={payment.id}
                          >

                            <td>

                              <div className="learner-name">
                                {payment.learner_name ||
                                  "Unknown Learner"}
                              </div>

                              <div className="learner-email">
                                {payment.learner_email ||
                                  "-"}
                              </div>

                            </td>


                            <td>

                              <div className="course-title">
                                {payment.course_title ||
                                  "Legacy Payment"}
                              </div>

                              {payment.course_id && (
                                <div className="course-id">
                                  {payment.course_id}
                                </div>
                              )}

                            </td>


                            <td>

                              <strong>
                                {formatCurrency(
                                  payment.amount
                                )}
                              </strong>

                            </td>


                            <td>
                              {payment.payment_method ||
                                "-"}
                            </td>


                            <td>

                              <span
                                className={`status-badge ${
                                  payment.status ===
                                  "paid"
                                    ? "status-paid"
                                    : payment.status ===
                                      "pending"
                                    ? "status-pending"
                                    : "status-failed"
                                }`}
                              >
                                {payment.status}
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


              {/* PAYMENT PAGINATION */}

              {paymentPagination.pages > 1 && (

                <div className="pagination">

                  <button
                    disabled={
                      paymentPage <= 1
                    }
                    onClick={() =>
                      setPaymentPage(
                        (page) =>
                          Math.max(
                            page - 1,
                            1
                          )
                      )
                    }
                  >
                    ← Previous
                  </button>

                  <span>
                    Page {paymentPagination.page}{" "}
                    of{" "}
                    {paymentPagination.pages}
                  </span>

                  <button
                    disabled={
                      paymentPage >=
                      paymentPagination.pages
                    }
                    onClick={() =>
                      setPaymentPage(
                        (page) =>
                          Math.min(
                            page + 1,
                            paymentPagination.pages
                          )
                      )
                    }
                  >
                    Next →
                  </button>

                </div>

              )}

            </section>


            {/* =================================================
                INVOICES
            ================================================= */}

            <section className="content-card">

              <div className="section-header">

                <div>
                  <h2>
                    Invoices
                  </h2>

                  <p>
                    View and download learner invoices.
                  </p>
                </div>

              </div>


              {invoices.length === 0 ? (

                <div className="empty-state">
                  No invoices found.
                </div>

              ) : (

                <div className="table-wrapper">

                  <table>

                    <thead>

                      <tr>
                        <th>Invoice Number</th>
                        <th>Learner</th>
                        <th>Amount</th>
                        <th>Date</th>
                        <th>Status</th>
                        <th>Action</th>
                      </tr>

                    </thead>


                    <tbody>

                      {invoices.map(
                        (invoice) => (

                          <tr
                            key={invoice.id}
                          >

                            <td>

                              <strong>
                                {invoice.invoice_number}
                              </strong>

                            </td>


                            <td>

                              <div className="learner-name">
                                {invoice.learner_name ||
                                  "Unknown Learner"}
                              </div>

                              <div className="learner-email">
                                {invoice.learner_email ||
                                  "-"}
                              </div>

                            </td>


                            <td>

                              <strong>
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
                                    : "status-pending"
                                }`}
                              >
                                {invoice.status}
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
                                Download PDF
                              </button>

                            </td>

                          </tr>

                        )
                      )}

                    </tbody>

                  </table>

                </div>

              )}


              {/* INVOICE PAGINATION */}

              {invoicePagination.pages > 1 && (

                <div className="pagination">

                  <button
                    disabled={
                      invoicePage <= 1
                    }
                    onClick={() =>
                      setInvoicePage(
                        (page) =>
                          Math.max(
                            page - 1,
                            1
                          )
                      )
                    }
                  >
                    ← Previous
                  </button>

                  <span>
                    Page {invoicePagination.page}{" "}
                    of{" "}
                    {invoicePagination.pages}
                  </span>

                  <button
                    disabled={
                      invoicePage >=
                      invoicePagination.pages
                    }
                    onClick={() =>
                      setInvoicePage(
                        (page) =>
                          Math.min(
                            page + 1,
                            invoicePagination.pages
                          )
                      )
                    }
                  >
                    Next →
                  </button>

                </div>

              )}

            </section>

          </>

        )}


        {/* =================================================
            STYLES
        ================================================= */}

        <style>{`

          .admin-payments-page {
            padding: 24px;
            max-width: 1500px;
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
            margin: 0 0 6px;
            font-size: 30px;
            color: #111827;
          }


          .page-header p {
            margin: 0;
            color: #6b7280;
          }


          .refresh-button {
            border: none;
            border-radius: 9px;
            padding: 11px 18px;
            background: #111827;
            color: white;
            font-weight: 700;
            cursor: pointer;
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
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 22px;
          }


          .summary-icon {
            font-size: 25px;
            margin-bottom: 10px;
          }


          .summary-label {
            color: #6b7280;
            font-size: 14px;
            margin-bottom: 7px;
          }


          .summary-value {
            font-size: 28px;
            font-weight: 800;
            color: #111827;
          }


          .content-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 22px;
            margin-bottom: 24px;
          }


          .section-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 18px;
          }


          .section-header h2 {
            margin: 0 0 5px;
            font-size: 21px;
            color: #111827;
          }


          .section-header p {
            margin: 0;
            color: #6b7280;
            font-size: 14px;
          }


          .table-wrapper {
            overflow-x: auto;
          }


          table {
            width: 100%;
            border-collapse: collapse;
          }


          th,
          td {
            padding: 14px 12px;
            text-align: left;
            border-bottom:
              1px solid #e5e7eb;
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


          .learner-name {
            font-weight: 700;
            color: #111827;
          }


          .learner-email {
            margin-top: 3px;
            font-size: 12px;
            color: #9ca3af;
          }


          .course-title {
            font-weight: 600;
            color: #111827;
          }


          .course-id {
            margin-top: 3px;
            font-size: 12px;
            color: #9ca3af;
          }


          .status-badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
          }


          .status-paid {
            background: #dcfce7;
            color: #166534;
          }


          .status-pending {
            background: #fef3c7;
            color: #92400e;
          }


          .status-failed {
            background: #fee2e2;
            color: #991b1b;
          }


          .download-button {
            border: none;
            border-radius: 8px;
            padding: 9px 13px;
            background: #2563eb;
            color: white;
            font-weight: 700;
            cursor: pointer;
          }


          .download-button:hover {
            opacity: 0.9;
          }


          .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 16px;
            margin-top: 20px;
          }


          .pagination button {
            border: 1px solid #d1d5db;
            background: white;
            border-radius: 8px;
            padding: 8px 14px;
            font-weight: 600;
            cursor: pointer;
          }


          .pagination button:disabled {
            opacity: 0.4;
            cursor: not-allowed;
          }


          .pagination span {
            font-size: 14px;
            color: #6b7280;
          }


          .state-card,
          .empty-state {
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            background: #f9fafb;
            color: #6b7280;
          }


          .error-card {
            padding: 16px 20px;
            border-radius: 10px;
            background: #fee2e2;
            color: #991b1b;
            margin-bottom: 20px;
          }


          @media (max-width: 900px) {

            .summary-grid {
              grid-template-columns: 1fr;
            }


            .page-header {
              flex-direction: column;
              align-items: flex-start;
            }

          }


          @media (max-width: 600px) {

            .admin-payments-page {
              padding: 16px;
            }

          }

        `}</style>

      </div>

    </DashboardLayout>
  );
}