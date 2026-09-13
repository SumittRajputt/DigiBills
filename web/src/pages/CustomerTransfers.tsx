import { useEffect, useState } from "react";
import {
  ArrowLeft,
  Check,
  CreditCard,
  Eye,
  Package,
  RefreshCw,
  Search,
  SlidersHorizontal,
  Send,
  X,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api";

type CustomerProduct = {
  ownership_id: string;
  product_unit_id: string;
  product_variant_id: string;
  product_id: string;
  product_name: string | null;
  product_code: string | null;
  brand: string | null;
  category: string | null;
  variant_name: string | null;
  sku: string | null;
  barcode: string | null;
  serial_number: string | null;
  product_unit_status: string;
  ownership_status: string;
  acquired_at: string;
  released_at: string | null;
  source: string | null;
  invoice_id: string | null;
  invoice_date: string | null;
};

type VerifiedRecipient = {
  id: string;
  customer_id: string;
  full_name: string;
  phone_number: string | null;
  email: string | null;
};

type CurrentCustomer = {
  customer_id: string;
  full_name: string;
};

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
  payment_payer: "sender" | "receiver";
  payment_invoice_id: string | null;
  payment_reference: string | null;
  accepted_at: string | null;

  from_customer?: {
    id: string;
    customer_id: string;
    full_name: string;
    phone_number: string | null;
    email: string | null;
  } | null;

  to_customer?: {
    id: string;
    customer_id: string;
    full_name: string;
    phone_number: string | null;
    email: string | null;
  } | null;

  product?: {
    product_unit_id: string;
    serial_number: string | null;
    product_variant_id: string;
    sku: string | null;
    variant_name: string | null;
    product_name: string | null;
  } | null;
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
  const [currentCustomer, setCurrentCustomer] =
    useState<CurrentCustomer | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [transferFormOpen, setTransferFormOpen] = useState(false);
  const [recipientCustomerId, setRecipientCustomerId] = useState("");
  const [transferReason, setTransferReason] = useState("");
  const [mobileTransferSearch, setMobileTransferSearch] =
    useState("");
  const [mobileTransferStatus, setMobileTransferStatus] =
    useState("all");

  const [customerProducts, setCustomerProducts] = useState<CustomerProduct[]>([]);
  const [selectedProductUnitId, setSelectedProductUnitId] = useState("");
  const [productsLoading, setProductsLoading] = useState(false);
  const [verifiedRecipient, setVerifiedRecipient] =
    useState<VerifiedRecipient | null>(null);
  const [recipientVerifying, setRecipientVerifying] =
    useState(false);
  const [recipientVerificationError, setRecipientVerificationError] =
    useState("");

  async function loadCurrentCustomer() {
    try {
      const result = await apiFetch<CurrentCustomer>(
        "/customers/me"
      );

      setCurrentCustomer(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load customer profile."
      );
    }
  }

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

  async function loadCustomerProducts() {
    try {
      setProductsLoading(true);

      const result = await apiFetch<CustomerProduct[]>(
        "/customer/products"
      );

      setCustomerProducts(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load eligible products."
      );
    } finally {
      setProductsLoading(false);
    }
  }

  async function verifyRecipientCustomerId(
    customerId: string
  ) {
    setVerifiedRecipient(null);
    setRecipientVerificationError("");

    if (customerId.length !== 11) {
      return;
    }

    try {
      setRecipientVerifying(true);

      const result = await apiFetch<{
        verified: boolean;
        customer: VerifiedRecipient;
      }>(
        `/customer/transfers/verify-customer/${customerId}`
      );

      if (result.verified && result.customer) {
        setVerifiedRecipient(result.customer);
      }
    } catch (err) {
      setRecipientVerificationError(
        err instanceof Error
          ? err.message
          : "Unable to verify Customer ID."
      );
    } finally {
      setRecipientVerifying(false);
    }
  }

  useEffect(() => {
    loadCurrentCustomer();
    loadTransfers();
  }, []);

  useEffect(() => {
    if (transferFormOpen) {
      loadCustomerProducts();
    }
  }, [transferFormOpen]);

  const pendingCount = transfers.filter(
    (transfer) => transfer.status === "pending_acceptance"
  ).length;

  const completedCount = transfers.filter(
    (transfer) => transfer.status === "completed"
  ).length;

  const rejectedCount = transfers.filter(
    (transfer) => transfer.status === "rejected"
  ).length;

  async function sendTransferRequest() {
    if (
      !selectedProductUnitId ||
      recipientCustomerId.length !== 11 ||
      !verifiedRecipient
    ) {
      return;
    }

    try {
      setActionLoading(true);
      setError("");

      const createdTransfer = await apiFetch<CustomerTransfer>(
        "/customer/transfers",
        {
          method: "POST",
          body: JSON.stringify({
            product_unit_id: selectedProductUnitId,
            to_customer_identifier: verifiedRecipient.customer_id,
            reason: transferReason.trim() || null,
          }),
        }
      );

      setSelectedTransfer(createdTransfer);
      setTransferFormOpen(false);

      setSelectedProductUnitId("");
      setRecipientCustomerId("");
      setVerifiedRecipient(null);
      setRecipientVerificationError("");
      setTransferReason("");

      await loadTransfers();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to send transfer request."
      );
    } finally {
      setActionLoading(false);
    }
  }

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

  async function cancelTransfer() {
    if (!selectedTransfer) {
      return;
    }

    const confirmed = window.confirm(
      "Are you sure you want to cancel this transfer request?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setActionLoading(true);
      setError("");

      const result = await apiFetch<CustomerTransfer>(
        `/customer/transfers/${selectedTransfer.transfer_id}/cancel`,
        {
          method: "POST",
        }
      );

      setSelectedTransfer(result);
      await loadTransfers();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to cancel this transfer."
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


  const filteredMobileTransfers = transfers.filter((transfer) => {


    const query = mobileTransferSearch.trim().toLowerCase();



    const searchableText = [


      transfer.transfer_id,


      transfer.product?.product_name,


      transfer.product?.variant_name,


      transfer.product?.serial_number,


      transfer.product?.sku,


      transfer.from_customer?.customer_id,


      transfer.from_customer?.full_name,


      transfer.to_customer?.customer_id,


      transfer.to_customer?.full_name,


    ]


      .filter(Boolean)


      .join(" ")


      .toLowerCase();



    const matchesSearch =


      query.length === 0 || searchableText.includes(query);



    const matchesStatus =


      mobileTransferStatus === "all" ||


      (mobileTransferStatus === "rejected"


        ? transfer.status === "rejected" ||


          transfer.status === "cancelled"


        : transfer.status === mobileTransferStatus);



    return matchesSearch && matchesStatus;


  });


  return (
    <section className="dashboard customer-dashboard-page customer-transfers-page">
      <div className="page-heading customer-transfers-heading">
        <div>
          

          <h1>Transfer Bills</h1>
        </div>
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

      <div className="customer-transfer-primary-action">
        <button
          type="button"
          className="primary-button customer-transfer-open-button"
          onClick={() => setTransferFormOpen(true)}
        >
          <Send size={17} />
          Transfer a Bill
        </button>
      </div>

      {transferFormOpen && (
        <div
          className="customer-transfer-form-backdrop"
          onClick={() => setTransferFormOpen(false)}
        >
          <div
            className="customer-transfer-form-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="customer-transfer-form-header">
              <div>
                <span className="page-eyebrow">
                  TRANSFER BILL
                </span>
                <h2>Transfer a Bill</h2>
                <p>
                  Transfer ownership of an eligible bill to
                  another DigiBills customer.
                </p>
              </div>

              <button
                type="button"
                className="table-action-button"
                onClick={() => setTransferFormOpen(false)}
                aria-label="Close transfer form"
              >
                ×
              </button>
            </div>

            <div className="customer-transfer-form-content">
              <div className="customer-transfer-form-section">
                <div className="customer-transfer-section-title">
                  <Package size={18} />
                  <strong>Bill / Product</strong>
                </div>

                {productsLoading ? (
                  <div className="customer-transfer-placeholder">
                    <RefreshCw size={22} className="spin" />
                    <div>
                      <strong>Loading your products...</strong>
                      <span>
                        Checking products available for transfer.
                      </span>
                    </div>
                  </div>
                ) : customerProducts.length === 0 ? (
                  <div className="customer-transfer-placeholder">
                    <Package size={22} />
                    <div>
                      <strong>No eligible products found</strong>
                      <span>
                        Products available for transfer will appear here.
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="customer-transfer-product-list">
                    {customerProducts.map((product) => {
                      const selected =
                        selectedProductUnitId === product.product_unit_id;

                      return (
                        <button
                          key={product.product_unit_id}
                          type="button"
                          className={`customer-transfer-product-option${
                            selected
                              ? " customer-transfer-product-option-selected"
                              : ""
                          }`}
                          onClick={() =>
                            setSelectedProductUnitId(
                              product.product_unit_id
                            )
                          }
                        >
                          <span className="customer-transfer-product-check">
                            {selected && <Check size={15} />}
                          </span>

                          <span className="customer-transfer-product-icon">
                            <Package size={21} />
                          </span>

                          <span className="customer-transfer-product-copy">
                            <strong>
                              {product.product_name || "Purchased Product"}
                            </strong>

                            {product.variant_name && (
                              <small>{product.variant_name}</small>
                            )}

                            <small>
                              {product.sku
                                ? `SKU: ${product.sku}`
                                : product.serial_number
                                  ? `Serial No: ${product.serial_number}`
                                  : "Purchased product"}
                            </small>

                            {product.invoice_id && (
                              <small>
                                Bill: {product.invoice_id}
                              </small>
                            )}

                            {product.invoice_date && (
                              <small>
                                Purchased: {formatDate(product.invoice_date)}
                              </small>
                            )}
                          </span>

                          <span className="customer-transfer-product-action">
                            {selected ? "Selected" : "Select"}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              <div className="customer-transfer-form-section">
                <div className="customer-transfer-section-title">
                  <CreditCard size={18} />
                  <strong>Recipient Customer</strong>
                </div>

                <label className="customer-transfer-field">
                  <span>
                    Customer ID <b>*</b>
                  </span>

                  <input
                    type="text"
                    inputMode="numeric"
                    maxLength={11}
                    value={recipientCustomerId}
                    onChange={(event) => {
                      const value = event.target.value
                        .replace(/\D/g, "")
                        .slice(0, 11);

                      setRecipientCustomerId(value);
                      setVerifiedRecipient(null);
                      setRecipientVerificationError("");

                      if (value.length === 11) {
                        verifyRecipientCustomerId(value);
                      }
                    }}
                    placeholder="Enter 11-digit Customer ID"
                  />

                  <small>
                    Enter the recipient's unique 11-digit
                    DigiBills Customer ID.
                  </small>
                </label>

                <div
                  className={`customer-transfer-recipient-preview${
                    verifiedRecipient
                      ? " customer-transfer-recipient-verified"
                      : recipientVerificationError
                        ? " customer-transfer-recipient-error"
                        : ""
                  }`}
                >
                  <span>Recipient</span>

                  {recipientVerifying ? (
                    <strong>
                      Verifying Customer ID...
                    </strong>
                  ) : verifiedRecipient ? (
                    <>
                      <strong>
                        ✓ {verifiedRecipient.full_name}
                      </strong>
                      <small>
                        Customer ID: {verifiedRecipient.customer_id}
                      </small>
                    </>
                  ) : recipientVerificationError ? (
                    <strong>
                      {recipientVerificationError}
                    </strong>
                  ) : (
                    <strong>
                      Enter a valid Customer ID to verify recipient
                    </strong>
                  )}
                </div>
              </div>

              <div className="customer-transfer-form-section">
                <div className="customer-transfer-section-title">
                  <Send size={18} />
                  <strong>Transfer Details</strong>
                </div>

                <label className="customer-transfer-field">
                  <span>Message / Reason</span>

                  <textarea
                    value={transferReason}
                    onChange={(event) =>
                      setTransferReason(event.target.value)
                    }
                    placeholder="Add an optional message or reason"
                    rows={3}
                  />
                </label>
              </div>
            </div>

            <div className="customer-transfer-form-footer">
              <button
                type="button"
                className="secondary-button"
                onClick={() => setTransferFormOpen(false)}
              >
                Cancel
              </button>

              <button
                type="button"
                className="primary-button"
                onClick={sendTransferRequest}
                disabled={
                  selectedProductUnitId.length === 0 ||
                  recipientCustomerId.length !== 11 ||
                  !verifiedRecipient ||
                  recipientVerifying ||
                  actionLoading
                }
              >
                {actionLoading ? (
                  <RefreshCw size={16} className="spin" />
                ) : (
                  <Send size={16} />
                )}
                {actionLoading
                  ? "Sending..."
                  : "Send Transfer Request"}
              </button>
            </div>
          </div>
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

        
          <div className="customer-transfers-mobile-controls">
            <label className="customer-transfers-mobile-search">
              <Search size={16} />
              <input
                type="search"
                value={mobileTransferSearch}
                onChange={(event) =>
                  setMobileTransferSearch(event.target.value)
                }
                placeholder="Search transfer bills..."
                aria-label="Search transfer bills"
              />
            </label>

            <label className="customer-transfers-mobile-filter">
              <SlidersHorizontal size={16} />
              <select
                value={mobileTransferStatus}
                onChange={(event) =>
                  setMobileTransferStatus(event.target.value)
                }
                aria-label="Filter transfer bills by status"
              >
                <option value="all">All Status</option>
                <option value="pending_acceptance">Pending</option>
                <option value="completed">Completed</option>
                <option value="rejected">Rejected</option>
              </select>
            </label>
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
          <>
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
                      <strong>
                        {transfer.product?.product_name || "—"}
                      </strong>
                      {transfer.product?.serial_number && (
                        <span className="customer-transfer-detail-secondary">
                          Serial: {transfer.product.serial_number}
                        </span>
                      )}
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

            <div className="customer-transfers-mobile-list">
              {filteredMobileTransfers.map((transfer) => (
                <article
                  key={`mobile-${transfer.id}`}
                  className="customer-transfer-mobile-card"
                >
                  <div className="customer-transfer-mobile-card-header">
                    <div>
                      <span className="page-eyebrow">
                        TRANSFER BILL
                      </span>

                      <strong>
                        {transfer.transfer_id}
                      </strong>
                    </div>

                    <span
                      className={statusClass(
                        transfer.status
                      )}
                    >
                      {label(transfer.status)}
                    </span>
                  </div>

                  <div className="customer-transfer-mobile-product">
                    <div className="customer-transfer-mobile-product-icon">
                      <Package size={19} />
                    </div>

                    <div>
                      <strong>
                        {transfer.product?.product_name || "—"}
                      </strong>

                      {transfer.product?.variant_name && (
                        <span>
                          {transfer.product.variant_name}
                        </span>
                      )}

                      {transfer.product?.serial_number && (
                        <span>
                          Serial:{" "}
                          {transfer.product.serial_number}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="customer-transfer-mobile-info-grid">
                    <div>
                      <small>From Customer</small>
                      <strong>
                        {transfer.from_customer?.customer_id ||
                          transfer.from_customer_id}
                      </strong>

                      {transfer.from_customer?.full_name && (
                        <span>
                          {transfer.from_customer.full_name}
                        </span>
                      )}
                    </div>

                    <div>
                      <small>To Customer</small>
                      <strong>
                        {transfer.to_customer?.customer_id ||
                          transfer.to_customer_id}
                      </strong>

                      {transfer.to_customer?.full_name && (
                        <span>
                          {transfer.to_customer.full_name}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="customer-transfer-mobile-payment-row">
                    <div>
                      <small>Transfer Fee</small>
                      <strong>
                        ₹
                        {Number(
                          transfer.transfer_fee || 0
                        ).toFixed(2)}
                      </strong>
                    </div>

                    <div>
                      <small>Payment</small>
                      <strong>
                        {label(
                          transfer.payment_status
                        )}
                      </strong>
                    </div>
                  </div>

                  <div className="customer-transfer-mobile-requested">
                    <small>Requested</small>
                    <strong>
                      {formatDate(
                        transfer.requested_at
                      )}
                    </strong>
                  </div>

                  <div className="customer-transfer-mobile-reason">
                    <small>Reason</small>
                    <p>
                      {transfer.reason ||
                        "No reason provided"}
                    </p>
                  </div>

                  <button
                    className="secondary-button customer-transfer-mobile-view-button"
                    type="button"
                    onClick={() =>
                      setSelectedTransfer(transfer)
                    }
                  >
                    <Eye size={15} />
                    View Details
                  </button>
                </article>
              ))}
            </div>
          </>
        )}
      </div>


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
                <small>Product</small>
                <strong>
                  {selectedTransfer.product?.product_name || "—"}
                </strong>
                {selectedTransfer.product?.variant_name && (
                  <span className="customer-transfer-detail-secondary">
                    {selectedTransfer.product.variant_name}
                  </span>
                )}
                {selectedTransfer.product?.sku && (
                  <span className="customer-transfer-detail-secondary">
                    SKU: {selectedTransfer.product.sku}
                  </span>
                )}
                {selectedTransfer.product?.serial_number && (
                  <span className="customer-transfer-detail-secondary">
                    Serial: {selectedTransfer.product.serial_number}
                  </span>
                )}
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
                  {selectedTransfer.from_customer?.full_name || "—"}
                </strong>
                <span className="customer-transfer-detail-secondary">
                  Customer ID:{" "}
                  {selectedTransfer.from_customer?.customer_id ||
                    selectedTransfer.from_customer_id}
                </span>
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
                  Number(selectedTransfer.transfer_fee || 0) > 0 &&
                  currentCustomer?.customer_id ===
                    (selectedTransfer.payment_payer === "sender"
                      ? selectedTransfer.from_customer_id
                      : selectedTransfer.to_customer_id) && (
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

                {currentCustomer?.customer_id ===
                  selectedTransfer.to_customer_id && (
                  <>
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
                  </>
                )}

                {currentCustomer?.customer_id ===
                  selectedTransfer.from_customer_id && (
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={cancelTransfer}
                    disabled={actionLoading}
                  >
                    <X size={16} />
                    {actionLoading
                      ? "Cancelling..."
                      : "Cancel Transfer"}
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
