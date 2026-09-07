import { useEffect, useState } from "react";
import {
  ArrowLeft,
  Check,
  CreditCard,
  Eye,
  Package,
  RefreshCw,
  Send,
  X,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api";

type CustomerTransfer = {
  id: string;
  transfer_id: string;
  product_unit_id: string;
  from_customer_id: string;
  to_customer_id: string;
  requested_by_user_id: string;
  approved_by_user_id: string | null;
  status: string;
  reason: string | null;
  rejection_reason: string | null;
  requested_at: string;
  approved_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  transfer_fee: string | number;
  payment_status: string;
  payment_invoice_id: string | null;
  payment_reference: string | null;
  accepted_at: string | null;
};

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

function label(value: string | null | undefined) {
  if (!value) return "—";

  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function statusClass(value: string) {
  return `customer-transfer-status customer-transfer-status-${value}`;
}

export default function CustomerTransfers() {
  const navigate = useNavigate();

  const [transfers, setTransfers] = useState<CustomerTransfer[]>([]);
  const [selectedTransfer, setSelectedTransfer] =
    useState<CustomerTransfer | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  async function loadTransfers() {
    try {
      setLoading(true);
      setError("");

      const result = await apiFetch<CustomerTransfer[]>(
        "/customer/transfers"
      );

      setTransfers(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load transfer bills."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTransfers();
  }, []);

  const pendingCount = transfers.filter(
    (transfer) => transfer.status === "pending_acceptance"
  ).length;

  const completedCount = transfers.filter(
    (transfer) => transfer.status === "completed"
  ).length;

  const rejectedCount = transfers.filter(
    (transfer) => transfer.status === "rejected"
  ).length;

  async function payTransfer() {
    if (!selectedTransfer) return;

    const paymentMethod = window.prompt(
      "Enter payment method (UPI / Card / Cash):",
      "UPI"
    );

    if (!paymentMethod) return;

    try {
      setActionLoading(true);
      setError("");

      const updated = await apiFetch<CustomerTransfer>(
        `/customer/transfers/${selectedTransfer.transfer_id}/pay`,
        {
          method: "POST",
          body: JSON.stringify({
            payment_method: paymentMethod,
            transaction_reference: `TRF-PAY-${Date.now()}`,
          }),
        }
      );

      setSelectedTransfer(updated);
      await loadTransfers();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to complete payment."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function acceptTransfer() {
    if (!selectedTransfer) return;

    try {
      setActionLoading(true);
      setError("");

      const updated = await apiFetch<CustomerTransfer>(
        `/customer/transfers/${selectedTransfer.transfer_id}/accept`,
        {
          method: "POST",
          body: JSON.stringify({
            confirmation: true,
          }),
        }
      );

      setSelectedTransfer(updated);
      await loadTransfers();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to accept transfer."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function rejectTransfer() {
    if (!selectedTransfer) return;

    const rejectionReason = window.prompt(
      "Enter rejection reason:",
      "Transfer rejected by customer"
    );

    if (!rejectionReason?.trim()) return;

    try {
      setActionLoading(true);
      setError("");

      const updated = await apiFetch<CustomerTransfer>(
        `/customer/transfers/${selectedTransfer.transfer_id}/reject`,
        {
          method: "POST",
          body: JSON.stringify({
            rejection_reason: rejectionReason.trim(),
          }),
        }
      );

      setSelectedTransfer(updated);
      await loadTransfers();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to reject transfer."
      );
    } finally {
      setActionLoading(false);
    }
  }

  return (
    <section className="dashboard customer-dashboard-page customer-transfers-page">
      <div className="page-heading customer-transfers-heading">
        <div>
          <span className="page-eyebrow">CUSTOMER ACCOUNT</span>

          <h1>Transfer Bills</h1>

          <p>
            View product ownership transfer requests associated
            with your account.
          </p>
        </div>

        <button
          className="secondary-button"
          type="button"
          onClick={loadTransfers}
          disabled={loading}
        >
          <RefreshCw
            size={15}
            className={loading ? "spin" : ""}
          />
          Refresh
        </button>
      </div>

      <div className="stats-grid four customer-transfer-stats">
        <div className="stat-card">
          <div className="stat-icon blue">
            <Send size={18} />
          </div>

          <div>
            <span>Total Transfers</span>
            <strong>{transfers.length}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon purple">
            <Package size={18} />
          </div>

          <div>
            <span>Pending</span>
            <strong>{pendingCount}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">
            <Package size={18} />
          </div>

          <div>
            <span>Completed</span>
            <strong>{completedCount}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon cyan">
            <Package size={18} />
          </div>

          <div>
            <span>Rejected</span>
            <strong>{rejectedCount}</strong>
          </div>
        </div>
      </div>

      {error && (
        <div className="table-state negative">
          {error}
        </div>
      )}

      <div className="panel customer-transfers-panel">
        <div className="panel-header">
          <div>
            <h3>Transfer Bills</h3>

            <span>
              {transfers.length} transfer
              {transfers.length === 1 ? "" : "s"} found
            </span>
          </div>
        </div>

        {loading ? (
          <div className="table-state">
            Loading transfer bills...
          </div>
        ) : transfers.length === 0 ? (
          <div className="table-state">
            <Send size={22} />

            <div>
              <strong>No transfer bills found</strong>

              <p>
                Product ownership transfers associated with
                your account will appear here.
              </p>
            </div>
          </div>
        ) : (
          <div className="customer-transfers-table-wrap">
            <table className="data-table customer-transfers-table">
              <thead>
                <tr>
                  <th>Transfer ID</th>
                  <th>Product Unit</th>
                  <th>Direction</th>
                  <th>Requested</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>

              <tbody>
                {transfers.map((transfer) => (
                  <tr key={transfer.id}>
                    <td>
                      <strong>{transfer.transfer_id}</strong>
                    </td>

                    <td>
                      <strong>{transfer.product_unit_id}</strong>
                    </td>

                    <td>
                      {transfer.status === "completed"
                        ? "Ownership transferred"
                        : "Transfer request"}
                    </td>

                    <td>
                      {formatDate(transfer.requested_at)}
                    </td>

                    <td>
                      <span
                        className={statusClass(
                          transfer.status
                        )}
                      >
                        {label(transfer.status)}
                      </span>
                    </td>

                    <td>
                      <button
                        className="table-action-button"
                        type="button"
                        title="View transfer"
                        onClick={() =>
                          setSelectedTransfer(transfer)
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
        )}
      </div>

      <button
        className="secondary-button customer-transfers-back"
        type="button"
        onClick={() => navigate("/customer")}
      >
        <ArrowLeft size={15} />
        Back to Dashboard
      </button>

      {selectedTransfer && (
        <div
          className="customer-transfer-modal-backdrop"
          onClick={() => setSelectedTransfer(null)}
        >
          <div
            className="customer-transfer-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="customer-transfer-modal-header">
              <div>
                <span className="page-eyebrow">
                  TRANSFER BILL
                </span>

                <h2>{selectedTransfer.transfer_id}</h2>
              </div>

              <button
                className="table-action-button"
                type="button"
                onClick={() => setSelectedTransfer(null)}
              >
                ×
              </button>
            </div>

            <div className="customer-transfer-detail-grid">
              <div>
                <small>Transfer ID</small>
                <strong>{selectedTransfer.transfer_id}</strong>
              </div>

              <div>
                <small>Status</small>
                <strong>{label(selectedTransfer.status)}</strong>
              </div>

              <div>
                <small>Product Unit</small>
                <strong>{selectedTransfer.product_unit_id}</strong>
              </div>

              <div>
                <small>From Customer</small>
                <strong>{selectedTransfer.from_customer_id}</strong>
              </div>

              <div>
                <small>To Customer</small>
                <strong>{selectedTransfer.to_customer_id}</strong>
              </div>

              <div>
                <small>Transfer Fee</small>
                <strong>
                  ₹{Number(
                    selectedTransfer.transfer_fee || 0
                  ).toFixed(2)}
                </strong>
              </div>

              <div>
                <small>Payment Status</small>
                <strong>
                  {label(selectedTransfer.payment_status)}
                </strong>
              </div>

              <div>
                <small>Payment Invoice</small>
                <strong>
                  {selectedTransfer.payment_invoice_id || "—"}
                </strong>
              </div>

              <div>
                <small>Payment Reference</small>
                <strong>
                  {selectedTransfer.payment_reference || "—"}
                </strong>
              </div>

              <div>
                <small>Requested By</small>
                <strong>
                  {selectedTransfer.requested_by_user_id}
                </strong>
              </div>

              <div>
                <small>Requested At</small>
                <strong>
                  {formatDate(selectedTransfer.requested_at)}
                </strong>
              </div>

              <div>
                <small>Accepted At</small>
                <strong>
                  {formatDate(selectedTransfer.accepted_at)}
                </strong>
              </div>

              <div>
                <small>Completed At</small>
                <strong>
                  {formatDate(selectedTransfer.completed_at)}
                </strong>
              </div>

              <div>
                <small>Reason</small>
                <strong>
                  {selectedTransfer.reason || "—"}
                </strong>
              </div>

              <div>
                <small>Rejection Reason</small>
                <strong>
                  {selectedTransfer.rejection_reason || "—"}
                </strong>
              </div>
            </div>

            {selectedTransfer.status === "pending_acceptance" && (
              <div className="customer-transfer-actions">
                {selectedTransfer.payment_status === "unpaid" &&
                  Number(selectedTransfer.transfer_fee || 0) > 0 && (
                    <button
                      className="primary-button"
                      type="button"
                      onClick={payTransfer}
                      disabled={actionLoading}
                    >
                      <CreditCard size={16} />
                      {actionLoading
                        ? "Processing..."
                        : `Pay ₹${Number(
                            selectedTransfer.transfer_fee
                          ).toFixed(2)}`}
                    </button>
                  )}

                {(selectedTransfer.payment_status === "paid" ||
                  selectedTransfer.payment_status === "not_required") && (
                  <button
                    className="primary-button"
                    type="button"
                    onClick={acceptTransfer}
                    disabled={actionLoading}
                  >
                    <Check size={16} />
                    {actionLoading
                      ? "Processing..."
                      : "Accept Transfer"}
                  </button>
                )}

                <button
                  className="secondary-button"
                  type="button"
                  onClick={rejectTransfer}
                  disabled={actionLoading}
                >
                  <X size={16} />
                  Reject
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
