import {
  Search,
  CreditCard,
  CheckCircle,
  XCircle,
  RotateCcw,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../api";

type Payment = {
  id: string;
  payment_id: string;
  invoice_id: string;
  amount: string;
  payment_method: string;
  payment_status: string;
  transaction_reference: string | null;
  paid_at: string;
  refund_amount: string;
  refund_status: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export default function AdminPayments() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [method, setMethod] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedPayment, setSelectedPayment] =
    useState<Payment | null>(null);

  async function loadPayments() {
    try {
      setLoading(true);
      setError("");

      const result =
        await apiFetch<Payment[]>("/payments");

      setPayments(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load payments."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPayments();
  }, []);

  const filteredPayments = useMemo(() => {
    const query = search.toLowerCase().trim();

    return payments.filter((payment) => {
      const matchesSearch =
        !query ||
        payment.payment_id
          .toLowerCase()
          .includes(query) ||
        payment.invoice_id
          .toLowerCase()
          .includes(query) ||
        (payment.transaction_reference || "")
          .toLowerCase()
          .includes(query);

      const matchesStatus =
        status === "all" ||
        payment.payment_status.toLowerCase() ===
          status;

      const matchesMethod =
        method === "all" ||
        payment.payment_method.toLowerCase() ===
          method;

      return (
        matchesSearch &&
        matchesStatus &&
        matchesMethod
      );
    });
  }, [payments, search, status, method]);

  const counts = {
    all: payments.length,
    completed: payments.filter(
      (payment) =>
        payment.payment_status === "completed"
    ).length,
    cancelled: payments.filter(
      (payment) =>
        payment.payment_status === "cancelled"
    ).length,
    refunded: payments.filter(
      (payment) =>
        payment.refund_status === "refunded"
    ).length,
  };

  const methods = Array.from(
    new Set(
      payments.map((payment) =>
        payment.payment_method.toLowerCase()
      )
    )
  );

  function formatDate(value: string) {
    return new Date(value).toLocaleDateString(
      "en-IN",
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
      }
    );
  }

  function formatDateTime(value: string) {
    return new Date(value).toLocaleString(
      "en-IN",
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }
    );
  }

  function formatMoney(value: string) {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(Number(value));
  }

  return (
    <section className="dashboard admin-payments-page">
      <div className="admin-payments-header">
        <div>
          <div className="page-eyebrow">
            <span>ADMINISTRATION</span>
          </div>
          <h1>Payments</h1>
          <p>
            Manage payment transactions, refunds and payment records across DigiBills.
          </p>
        </div>
      </div>

      <div className="payment-stats-grid">
        <MiniStat
          icon={<CreditCard />}
          title="Total Payments"
          value={counts.all}
          tone="blue"
        />

        <MiniStat
          icon={<CheckCircle />}
          title="Completed"
          value={counts.completed}
          tone="green"
        />

        <MiniStat
          icon={<XCircle />}
          title="Cancelled"
          value={counts.cancelled}
          tone="red"
        />

        <MiniStat
          icon={<RotateCcw />}
          title="Refunded"
          value={counts.refunded}
          tone="purple"
        />
      </div>

      <div className="payments-panel">
        <div className="payments-panel-header">
          <div>
            <h3>Payment Directory</h3>
            <span>
              {filteredPayments.length} of {payments.length} payments
            </span>
          </div>

          <div className="payments-toolbar">
            <div className="payments-search">
              <Search size={16} />

              <input
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search payments..."
              />
            </div>

            <select
              value={method}
              onChange={(event) =>
                setMethod(event.target.value)
              }
            >
              <option value="all">
                All Methods
              </option>

              {methods.map((item) => (
                <option
                  key={item}
                  value={item}
                >
                  {item.toUpperCase()}
                </option>
              ))}
            </select>

            <select
              value={status}
              onChange={(event) =>
                setStatus(event.target.value)
              }
            >
              <option value="all">
                All Status
              </option>
              <option value="completed">
                Completed
              </option>
              <option value="cancelled">
                Cancelled
              </option>
            </select>
          </div>
        </div>

        {loading && (
          <div className="table-state">
            Loading payments...
          </div>
        )}

        {!loading && error && (
          <div className="table-state negative">
            {error}
          </div>
        )}

        {!loading &&
          !error &&
          filteredPayments.length === 0 && (
            <div className="table-state">
              No payments found.
            </div>
          )}

        {!loading &&
          !error &&
          filteredPayments.length > 0 && (
            <div className="payments-table-wrap">
              <table className="payments-table">
                <thead>
                  <tr>
                    <th>Payment</th>
                    <th>Invoice</th>
                    <th>Amount</th>
                    <th>Method</th>
                    <th>Status</th>
                    <th>Refund</th>
                    <th>Paid</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredPayments.map(
                    (payment) => (
                      <tr
                        key={payment.id}
                        onClick={() =>
                          setSelectedPayment(
                            payment
                          )
                        }
                        style={{
                          cursor: "pointer",
                        }}
                      >
                        <td>
                          <div className="payment-cell">
                            <div className="payment-avatar">
                              ₹
                            </div>

                            <div>
                              <strong>
                                {payment.payment_id}
                              </strong>

                              <small>
                                {payment.transaction_reference ||
                                  "No transaction reference"}
                              </small>
                            </div>
                          </div>
                        </td>

                        <td>
                          <small>
                            {payment.invoice_id}
                          </small>
                        </td>

                        <td>
                          <strong>
                            {formatMoney(
                              payment.amount
                            )}
                          </strong>
                        </td>

                        <td>
                          {payment.payment_method.toUpperCase()}
                        </td>

                        <td>
                          <span
                            className={`status-badge ${payment.payment_status}`}
                          >
                            {payment.payment_status}
                          </span>
                        </td>

                        <td>
                          {Number(
                            payment.refund_amount
                          ) > 0 ? (
                            <div className="contact-cell">
                              <span>
                                {formatMoney(
                                  payment.refund_amount
                                )}
                              </span>

                              <small>
                                {payment.refund_status ||
                                  "Refund"}
                              </small>
                            </div>
                          ) : (
                            "—"
                          )}
                        </td>

                        <td>
                          {formatDate(
                            payment.paid_at
                          )}
                        </td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>
          )}
      </div>

      {selectedPayment && (
        <div
          className="modal-backdrop"
          onClick={() =>
            setSelectedPayment(null)
          }
        >
          <div
            className="payment-details-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="modal-header">
              <div>
                <h2>Payment Details</h2>
                <p>
                  Payment information registered
                  on DigiBills.
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() =>
                  setSelectedPayment(null)
                }
              >
                ×
              </button>
            </div>

            <div className="payment-details-content">

              <div className="payment-detail-group">
                <div className="payment-detail-heading">
                  <span className="section-number">1.</span>
                  <div>
                    <h3>Payment Information</h3>
                    <p>Core payment identification and billing details.</p>
                  </div>
                </div>

                <div className="payment-detail-grid">
                  <div className="payment-detail-card">
                    <span>Payment ID</span>
                    <strong>{selectedPayment.payment_id}</strong>
                  </div>

                  <div className="payment-detail-card">
                    <span>Invoice ID</span>
                    <strong>{selectedPayment.invoice_id}</strong>
                  </div>

                  <div className="payment-detail-card payment-amount-card">
                    <span>Amount</span>
                    <strong>{formatMoney(selectedPayment.amount)}</strong>
                  </div>

                  <div className="payment-detail-card">
                    <span>Payment Method</span>
                    <strong>{selectedPayment.payment_method.toUpperCase()}</strong>
                  </div>

                  <div className="payment-detail-card">
                    <span>Payment Status</span>
                    <strong className={`payment-status-value ${selectedPayment.payment_status}`}>
                      {selectedPayment.payment_status}
                    </strong>
                  </div>
                </div>
              </div>

              <div className="payment-detail-group">
                <div className="payment-detail-heading">
                  <span className="section-number">2.</span>
                  <div>
                    <h3>Transaction Details</h3>
                    <p>Reference information associated with this payment.</p>
                  </div>
                </div>

                <div className="payment-detail-grid">
                  <div className="payment-detail-card payment-detail-wide">
                    <span>Transaction Reference</span>
                    <strong>
                      {selectedPayment.transaction_reference || "No transaction reference"}
                    </strong>
                  </div>
                </div>
              </div>

              <div className="payment-detail-group">
                <div className="payment-detail-heading">
                  <span className="section-number">3.</span>
                  <div>
                    <h3>Refund Information</h3>
                    <p>Refund amount and current refund status.</p>
                  </div>
                </div>

                <div className="payment-detail-grid">
                  <div className="payment-detail-card">
                    <span>Refund Amount</span>
                    <strong>
                      {formatMoney(selectedPayment.refund_amount)}
                    </strong>
                  </div>

                  <div className="payment-detail-card">
                    <span>Refund Status</span>
                    <strong className={`payment-status-value ${selectedPayment.refund_status || "none"}`}>
                      {selectedPayment.refund_status || "No refund"}
                    </strong>
                  </div>
                </div>
              </div>

              <div className="payment-detail-group">
                <div className="payment-detail-heading">
                  <span className="section-number">4.</span>
                  <div>
                    <h3>Timeline</h3>
                    <p>Important payment record timestamps.</p>
                  </div>
                </div>

                <div className="payment-detail-grid">
                  <div className="payment-detail-card">
                    <span>Paid At</span>
                    <strong>{formatDateTime(selectedPayment.paid_at)}</strong>
                  </div>

                  <div className="payment-detail-card">
                    <span>Created</span>
                    <strong>{formatDateTime(selectedPayment.created_at)}</strong>
                  </div>

                  <div className="payment-detail-card">
                    <span>Last Updated</span>
                    <strong>{formatDateTime(selectedPayment.updated_at)}</strong>
                  </div>
                </div>
              </div>

              <div className="payment-notes">
                <span>Notes</span>
                <p>
                  {selectedPayment.notes || "No notes available for this payment."}
                </p>
              </div>

            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function MiniStat({
  icon,
  title,
  value,
  tone,
}: {
  icon: React.ReactNode;
  title: string;
  value: number;
  tone: string;
}) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${tone}`}>
        {icon}
      </div>

      <div>
        <span>{title}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}
