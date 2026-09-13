import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  CreditCard,
  Eye,
  Search,
  SlidersHorizontal,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api";

type CustomerPayment = {
  id: string;
  payment_id: string;
  invoice_id: string;
  item_names: string[];
  amount: string | number;
  payment_method: string;
  payment_status: string;
  transaction_reference: string | null;
  paid_at: string | null;
  refund_amount: string | number;
  refund_status: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

function money(value: string | number | null | undefined) {
  const amount = Number(value ?? 0);

  return `₹${amount.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function formatDate(value: string | null | undefined) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function label(value: string | null | undefined) {
  if (!value) return "—";

  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function statusClass(value: string) {
  return `customer-payment-status customer-payment-status-${value}`;
}

export default function CustomerPayments() {
  const navigate = useNavigate();

  const [payments, setPayments] = useState<CustomerPayment[]>([]);
  const [selectedPayment, setSelectedPayment] =
    useState<CustomerPayment | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [mobilePaymentSearch, setMobilePaymentSearch] =
    useState("");
  const [mobilePaymentStatus, setMobilePaymentStatus] =
    useState("all");

  async function loadPayments() {
    try {
      setLoading(true);
      setError("");

      const result =
        await apiFetch<CustomerPayment[]>(
          "/customer/payments"
        );

      setPayments(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load your payments."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPayments();
  }, []);

  const completedAmount = useMemo(
    () =>
      payments
        .filter(
          (payment) =>
            payment.payment_status === "completed"
        )
        .reduce(
          (sum, payment) =>
            sum + Number(payment.amount || 0),
          0
        ),
    [payments]
  );

  const refundedAmount = useMemo(
    () =>
      payments.reduce(
        (sum, payment) =>
          sum + Number(payment.refund_amount || 0),
        0
      ),
    [payments]
  );

  const completedCount = payments.filter(
    (payment) =>
      payment.payment_status === "completed"
  ).length;

  const filteredMobilePayments = useMemo(() => {
    const search =
      mobilePaymentSearch.trim().toLowerCase();

    return payments.filter((payment) => {
      const searchableText = [
        payment.payment_id,
        payment.invoice_id,
        ...(payment.item_names || []),
        payment.payment_method,
        payment.payment_status,
        payment.transaction_reference || "",
      ]
        .join(" ")
        .toLowerCase();

      const matchesSearch =
        !search || searchableText.includes(search);

      const matchesStatus =
        mobilePaymentStatus === "all" ||
        payment.payment_status?.toLowerCase() ===
          mobilePaymentStatus;

      return matchesSearch && matchesStatus;
    });
  }, [
    payments,
    mobilePaymentSearch,
    mobilePaymentStatus,
  ]);

  return (
    <section className="dashboard customer-dashboard-page customer-payments-page">
      <div className="page-heading customer-payments-heading">
        <div>
          

          <h1>My Payments</h1>
        </div>
      </div>

      <div className="stats-grid four customer-payment-stats">
        <div className="stat-card">
          <div className="stat-icon blue">
            <CreditCard size={18} />
          </div>

          <div>
            <span>Total Payments</span>
            <strong>{payments.length}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">
            <CreditCard size={18} />
          </div>

          <div>
            <span>Completed Amount</span>
            <strong>{money(completedAmount)}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon purple">
          </div>

          <div>
            <span>Refunds</span>
            <strong>{money(refundedAmount)}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon cyan">
            <CreditCard size={18} />
          </div>

          <div>
            <span>Completed Transactions</span>
            <strong>{completedCount}</strong>
          </div>
        </div>
      </div>

      <div className="panel customer-payments-panel">
        <div className="panel-header">
          <div>
            <h3>Payment History</h3>
            <span>
              {payments.length} payment
              {payments.length === 1 ? "" : "s"} found
            </span>
          </div>
        </div>

        {loading ? (
          <div className="table-state">
            Loading your payments...
          </div>
        ) : error ? (
          <div className="table-state negative">
            {error}
          </div>
        ) : payments.length === 0 ? (
          <div className="table-state">
            No payments found.
          </div>
        ) : (
            <>
          <div className="customer-payments-table-wrap">
            <table className="data-table customer-payments-table">
              <thead>
                <tr>
                  <th>Payment ID</th>
                  <th>Item</th>
                  <th>Date</th>
                  <th>Method</th>
                  <th>Amount</th>
                  <th>Refund</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>

              <tbody>
                {payments.map((payment) => (
                  <tr key={payment.payment_id}>
                    <td>
                      <strong>
                        {payment.payment_id}
                      </strong>
                    </td>

                    <td>
                      <span>
                        {payment.item_names?.length
                          ? payment.item_names.join(", ")
                          : "No items"}
                      </span>
                    </td>

                    <td>
                      {formatDate(payment.paid_at)}
                    </td>

                    <td>
                      {label(payment.payment_method)}
                    </td>

                    <td>
                      <strong>
                        {money(payment.amount)}
                      </strong>
                    </td>

                    <td>
                      {Number(
                        payment.refund_amount || 0
                      ) > 0
                        ? money(payment.refund_amount)
                        : "—"}
                    </td>

                    <td>
                      <span
                        className={statusClass(
                          payment.payment_status
                        )}
                      >
                        {label(
                          payment.payment_status
                        )}
                      </span>
                    </td>

                    <td>
                      <button
                        className="table-action-button"
                        type="button"
                        title="View payment"
                        onClick={() =>
                          setSelectedPayment(payment)
                        }
                      >
                        <Eye size={15} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="customer-payments-mobile-content">
            <div className="customer-payments-mobile-controls">
              <label className="customer-payments-mobile-search">
                <Search size={17} />
                <input
                  type="search"
                  placeholder="Search payments..."
                  value={mobilePaymentSearch}
                  onChange={(event) =>
                    setMobilePaymentSearch(
                      event.target.value
                    )
                  }
                />
              </label>

              <label className="customer-payments-mobile-filter">
                <SlidersHorizontal size={16} />
                <select
                  value={mobilePaymentStatus}
                  onChange={(event) =>
                    setMobilePaymentStatus(
                      event.target.value
                    )
                  }
                  aria-label="Filter payments by status"
                >
                  <option value="all">
                    All Status
                  </option>
                  <option value="completed">
                    Completed
                  </option>
                  <option value="pending">
                    Pending
                  </option>
                  <option value="failed">
                    Failed
                  </option>
                  <option value="refunded">
                    Refunded
                  </option>
                </select>
              </label>
            </div>

            {filteredMobilePayments.length === 0 ? (
              <div className="customer-payments-mobile-empty">
                No payments found.
              </div>
            ) : (
              <div className="customer-payments-mobile-list">
                {filteredMobilePayments.map((payment) => (
                  <article
                    className="customer-payment-mobile-card"
                    key={payment.payment_id}
                  >
                    <div className="customer-payment-mobile-top">
                      <div className="customer-payment-mobile-icon">
                        <CreditCard size={18} />
                      </div>

                      <div className="customer-payment-mobile-main">
                        <strong>
                          {payment.payment_id}
                        </strong>

                        <small>
                          {formatDate(payment.paid_at)}
                        </small>
                      </div>

                      <span
                        className={`customer-payment-mobile-status ${
                          payment.payment_status
                            ?.toLowerCase() || ""
                        }`}
                      >
                        {label(
                          payment.payment_status
                        )}
                      </span>
                    </div>

                    <div className="customer-payment-mobile-divider" />

                    <div className="customer-payment-mobile-row">
                      <div>
                        <small>ITEM</small>
                        <strong>
                          {payment.item_names?.length
                            ? payment.item_names.join(", ")
                            : "No items"}
                        </strong>
                      </div>

                      <div>
                        <small>AMOUNT</small>
                        <strong>
                          {money(payment.amount)}
                        </strong>
                      </div>
                    </div>

                    <div className="customer-payment-mobile-row">
                      <div>
                        <small>METHOD</small>
                        <strong>
                          {label(
                            payment.payment_method
                          )}
                        </strong>
                      </div>

                      <div>
                        <small>REFUND</small>
                        <strong>
                          {Number(
                            payment.refund_amount || 0
                          ) > 0
                            ? money(
                                payment.refund_amount
                              )
                            : "—"}
                        </strong>
                      </div>
                    </div>

                    <button
                      type="button"
                      className="customer-payment-mobile-view"
                      onClick={() =>
                        setSelectedPayment(payment)
                      }
                    >
                      <Eye size={15} />
                      View Payment
                    </button>
                  </article>
                ))}
              </div>
            )}
          </div>
          </>
        )}
      </div>


      {selectedPayment && (
        <div
          className="customer-payment-modal-backdrop"
          onClick={() =>
            setSelectedPayment(null)
          }
        >
          <div
            className="customer-payment-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="customer-payment-modal-header">
              <div>
                <span className="page-eyebrow">
                  PAYMENT DETAILS
                </span>

                <h2>
                  {selectedPayment.payment_id}
                </h2>
              </div>

              <button
                className="table-action-button"
                type="button"
                onClick={() =>
                  setSelectedPayment(null)
                }
              >
                ×
              </button>
            </div>

            <div className="customer-payment-detail-grid">
              <div>
                <small>Payment ID</small>
                <strong>
                  {selectedPayment.payment_id}
                </strong>
              </div>

              <div>
                <small>Invoice</small>
                <strong>
                  {selectedPayment.invoice_id}
                </strong>
              </div>

              <div>
                <small>Amount</small>
                <strong>
                  {money(selectedPayment.amount)}
                </strong>
              </div>

              <div>
                <small>Payment Method</small>
                <strong>
                  {label(
                    selectedPayment.payment_method
                  )}
                </strong>
              </div>

              <div>
                <small>Status</small>
                <span
                  className={statusClass(
                    selectedPayment.payment_status
                  )}
                >
                  {label(
                    selectedPayment.payment_status
                  )}
                </span>
              </div>

              <div>
                <small>Paid At</small>
                <strong>
                  {formatDateTime(
                    selectedPayment.paid_at
                  )}
                </strong>
              </div>

              <div>
                <small>Refund Amount</small>
                <strong>
                  {money(
                    selectedPayment.refund_amount
                  )}
                </strong>
              </div>

              <div>
                <small>Refund Status</small>
                <strong>
                  {label(
                    selectedPayment.refund_status
                  )}
                </strong>
              </div>

              <div>
                <small>Transaction Reference</small>
                <strong>
                  {selectedPayment.transaction_reference ||
                    "—"}
                </strong>
              </div>

              <div>
                <small>Notes</small>
                <strong>
                  {selectedPayment.notes || "—"}
                </strong>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
