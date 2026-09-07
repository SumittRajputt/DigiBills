import {
  Search,
  CreditCard,
  CheckCircle,
  XCircle,
  RotateCcw,
  Eye,
  Ban,
  RefreshCw,
  X,
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

export default function RetailerPayments() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [method, setMethod] = useState("all");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedPayment, setSelectedPayment] =
    useState<Payment | null>(null);

  const [showRefund, setShowRefund] = useState(false);
  const [refundAmount, setRefundAmount] = useState("");
  const [refundNotes, setRefundNotes] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState("");

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
        payment.payment_id.toLowerCase().includes(query) ||
        payment.invoice_id.toLowerCase().includes(query) ||
        (payment.transaction_reference || "")
          .toLowerCase()
          .includes(query);

      const matchesStatus =
        status === "all" ||
        payment.payment_status.toLowerCase() === status;

      const matchesMethod =
        method === "all" ||
        payment.payment_method.toLowerCase() === method;

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
        payment.payment_status.toLowerCase() === "completed"
    ).length,
    cancelled: payments.filter(
      (payment) =>
        payment.payment_status.toLowerCase() === "cancelled"
    ).length,
    refunded: payments.filter(
      (payment) =>
        payment.refund_status?.toLowerCase() === "refunded"
    ).length,
  };

  const totalCollected = payments
    .filter(
      (payment) =>
        payment.payment_status.toLowerCase() === "completed"
    )
    .reduce(
      (sum, payment) => sum + Number(payment.amount || 0),
      0
    );

  const methods = Array.from(
    new Set(
      payments.map((payment) =>
        payment.payment_method.toLowerCase()
      )
    )
  );

  function formatDate(value: string) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "—";
    }

    return date.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  function formatDateTime(value: string) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "—";
    }

    return date.toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function formatMoney(value: string | number) {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(Number(value || 0));
  }

  async function cancelSelectedPayment() {
    if (!selectedPayment) return;

    if (
      !window.confirm(
        `Cancel payment ${selectedPayment.payment_id}?`
      )
    ) {
      return;
    }

    try {
      setActionLoading(true);
      setActionError("");

      const updated = await apiFetch<Payment>(
        `/payments/${encodeURIComponent(
          selectedPayment.payment_id
        )}/cancel`,
        {
          method: "POST",
        }
      );

      setPayments((current) =>
        current.map((payment) =>
          payment.id === updated.id ? updated : payment
        )
      );

      setSelectedPayment(updated);
    } catch (err) {
      setActionError(
        err instanceof Error
          ? err.message
          : "Unable to cancel payment."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function submitRefund() {
    if (!selectedPayment) return;

    const amount = Number(refundAmount);

    if (!Number.isFinite(amount) || amount <= 0) {
      setActionError(
        "Refund amount must be greater than 0."
      );
      return;
    }

    if (amount > Number(selectedPayment.amount)) {
      setActionError(
        "Refund amount cannot exceed payment amount."
      );
      return;
    }

    try {
      setActionLoading(true);
      setActionError("");

      const updated = await apiFetch<Payment>(
        `/payments/${encodeURIComponent(
          selectedPayment.payment_id
        )}/refund`,
        {
          method: "POST",
          body: JSON.stringify({
            refund_amount: amount.toFixed(2),
            refund_method: null,
            notes: refundNotes.trim() || null,
          }),
        }
      );

      setPayments((current) =>
        current.map((payment) =>
          payment.id === updated.id ? updated : payment
        )
      );

      setSelectedPayment(updated);
      setShowRefund(false);
      setRefundAmount("");
      setRefundNotes("");
    } catch (err) {
      setActionError(
        err instanceof Error
          ? err.message
          : "Unable to process refund."
      );
    } finally {
      setActionLoading(false);
    }
  }

  function openRefund() {
    if (!selectedPayment) return;

    const remaining =
      Number(selectedPayment.amount) -
      Number(selectedPayment.refund_amount || 0);

    setRefundAmount(
      remaining > 0 ? remaining.toFixed(2) : ""
    );
    setRefundNotes("");
    setActionError("");
    setShowRefund(true);
  }

  return (
    <section className="dashboard admin-payments-page">
      <div className="admin-payments-header">
        <div>
          <div className="page-eyebrow">
            <span>RETAILER MANAGEMENT</span>
          </div>

          <h1>Payments</h1>

          <p>
            Manage your payment transactions, refunds and
            payment records.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={loadPayments}
          disabled={loading}
        >
          <RefreshCw size={14} />
          Refresh
        </button>
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
          title="Collected"
          value={formatMoney(totalCollected)}
          tone="purple"
        />
      </div>

      <div className="payments-panel">
        <div className="payments-panel-header">
          <div>
            <h3>Payment Directory</h3>

            <span>
              {filteredPayments.length} of{" "}
              {payments.length} payments
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
              <option value="all">All Methods</option>

              {methods.map((item) => (
                <option key={item} value={item}>
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
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
              <option value="pending">Pending</option>
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

        {!loading && !error && (
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
                  <th>Paid Date</th>
                </tr>
              </thead>

              <tbody>
                {filteredPayments.length > 0 ? (
                  filteredPayments.map((payment) => (
                    <tr
                      key={payment.id}
                      onClick={() =>
                        setSelectedPayment(payment)
                      }
                    >
                      <td>
                        <div className="payment-cell">
                          <div className="payment-avatar">
                            <CreditCard size={15} />
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
                        {payment.invoice_id}
                      </td>

                      <td>
                        {formatMoney(payment.amount)}
                      </td>

                      <td>
                        {payment.payment_method}
                      </td>

                      <td>
                        <span
                          className={`status-badge ${payment.payment_status}`}
                        >
                          {payment.payment_status}
                        </span>
                      </td>

                      <td>
                        <span className="refund-amount">
                          {formatMoney(
                            payment.refund_amount
                          )}
                        </span>

                        {payment.refund_status && (
                          <span className="refund-status">
                            {payment.refund_status}
                          </span>
                        )}
                      </td>

                      <td>
                        {formatDate(payment.paid_at)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td
                      colSpan={7}
                      style={{
                        textAlign: "center",
                        padding: "48px 20px",
                      }}
                    >
                      No payments found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedPayment && (
        <div
          className="modal-backdrop"
          onClick={() => {
            setSelectedPayment(null);
            setActionError("");
          }}
        >
          <div
            className="user-details-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="modal-header">
              <div>
                <h2>Payment Details</h2>
                <p>
                  {selectedPayment.payment_id}
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() =>
                  setSelectedPayment(null)
                }
              >
                <X size={17} />
              </button>
            </div>

            {actionError && (
              <div className="login-error">
                {actionError}
              </div>
            )}

            <div className="user-details-grid">
              <div className="detail">
                <span className="detail-label">
                  Payment ID
                </span>
                <span className="detail-value">
                  {selectedPayment.payment_id}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Invoice
                </span>
                <span className="detail-value">
                  {selectedPayment.invoice_id}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Amount
                </span>
                <span className="detail-value">
                  {formatMoney(selectedPayment.amount)}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Method
                </span>
                <span className="detail-value">
                  {selectedPayment.payment_method}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Status
                </span>
                <span className="detail-value">
                  {selectedPayment.payment_status}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Paid At
                </span>
                <span className="detail-value">
                  {formatDateTime(
                    selectedPayment.paid_at
                  )}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Transaction Reference
                </span>
                <span className="detail-value">
                  {selectedPayment.transaction_reference ||
                    "—"}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Refund
                </span>
                <span className="detail-value">
                  {formatMoney(
                    selectedPayment.refund_amount
                  )}
                  {selectedPayment.refund_status
                    ? ` · ${selectedPayment.refund_status}`
                    : ""}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Notes
                </span>
                <span className="detail-value">
                  {selectedPayment.notes || "—"}
                </span>
              </div>
            </div>

            <div className="roles-section">
              <h3>Actions</h3>

              <div className="role-add">
                <button
                  type="button"
                  className="primary-button"
                  onClick={openRefund}
                  disabled={
                    actionLoading ||
                    selectedPayment.payment_status !==
                      "completed" ||
                    Number(selectedPayment.refund_amount) >=
                      Number(selectedPayment.amount)
                  }
                >
                  <RotateCcw size={14} />
                  Refund Payment
                </button>

                <button
                  type="button"
                  className="danger-button"
                  onClick={cancelSelectedPayment}
                  disabled={
                    actionLoading ||
                    selectedPayment.payment_status ===
                      "cancelled"
                  }
                >
                  <Ban size={14} />
                  Cancel Payment
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showRefund && selectedPayment && (
        <div
          className="modal-backdrop"
          onClick={() => setShowRefund(false)}
        >
          <div
            className="user-details-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="modal-header">
              <div>
                <h2>Refund Payment</h2>
                <p>
                  {selectedPayment.payment_id}
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() =>
                  setShowRefund(false)
                }
              >
                <X size={17} />
              </button>
            </div>

            <div className="user-details-grid">
              <div className="detail">
                <span className="detail-label">
                  Original Amount
                </span>
                <span className="detail-value">
                  {formatMoney(selectedPayment.amount)}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Already Refunded
                </span>
                <span className="detail-value">
                  {formatMoney(
                    selectedPayment.refund_amount
                  )}
                </span>
              </div>
            </div>

            <div className="form-group">
              <label>
                Refund Amount
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={refundAmount}
                  onChange={(event) =>
                    setRefundAmount(
                      event.target.value
                    )
                  }
                  placeholder="0.00"
                />
              </label>

              <label>
                Notes
                <textarea
                  rows={3}
                  value={refundNotes}
                  onChange={(event) =>
                    setRefundNotes(
                      event.target.value
                    )
                  }
                  placeholder="Optional refund notes"
                />
              </label>
            </div>

            {actionError && (
              <div className="login-error">
                {actionError}
              </div>
            )}

            <div className="modal-footer">
              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  setShowRefund(false)
                }
              >
                Cancel
              </button>

              <button
                type="button"
                className="primary-button"
                onClick={submitRefund}
                disabled={actionLoading}
              >
                <RotateCcw size={14} />
                {actionLoading
                  ? "Processing..."
                  : "Process Refund"}
              </button>
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
  value: string | number;
  tone: "blue" | "green" | "red" | "purple";
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
