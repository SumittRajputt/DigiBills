import {
  Search,
  Receipt,
  CheckCircle,
  Clock,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../api";

type Invoice = {
  id: string;
  invoice_id: string;
  retailer_id: string;
  employee_id: string | null;
  customer_id: string;
  invoice_number: string | null;
  invoice_date: string;
  subtotal: string;
  discount_amount: string;
  tax_amount: string;
  total_amount: string;
  payment_status: string;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export default function AdminInvoices() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [paymentStatus, setPaymentStatus] =
    useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedInvoice, setSelectedInvoice] =
    useState<Invoice | null>(null);

  async function loadInvoices() {
    try {
      setLoading(true);
      setError("");

      const result =
        await apiFetch<Invoice[]>("/invoices");

      setInvoices(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load invoices."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadInvoices();
  }, []);

  const filteredInvoices = useMemo(() => {
    const query = search.toLowerCase().trim();

    return invoices.filter((invoice) => {
      const matchesSearch =
        !query ||
        invoice.invoice_id
          .toLowerCase()
          .includes(query) ||
        (invoice.invoice_number || "")
          .toLowerCase()
          .includes(query) ||
        invoice.retailer_id
          .toLowerCase()
          .includes(query) ||
        invoice.customer_id
          .toLowerCase()
          .includes(query);

      const matchesStatus =
        status === "all" ||
        invoice.status.toLowerCase() === status;

      const matchesPayment =
        paymentStatus === "all" ||
        invoice.payment_status.toLowerCase() ===
          paymentStatus;

      return (
        matchesSearch &&
        matchesStatus &&
        matchesPayment
      );
    });
  }, [
    invoices,
    search,
    status,
    paymentStatus,
  ]);

  const counts = {
    all: invoices.length,
    active: invoices.filter(
      (invoice) => invoice.status === "active"
    ).length,
    paid: invoices.filter(
      (invoice) =>
        invoice.payment_status === "paid"
    ).length,
    unpaid: invoices.filter(
      (invoice) =>
        invoice.payment_status === "unpaid"
    ).length,
  };

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

  function formatMoney(value: string) {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(Number(value));
  }

  return (
    <section className="dashboard admin-invoices-page">
      <div className="admin-invoices-header">
        <div>
          <div className="page-eyebrow">
            <span>ADMINISTRATION</span>
          </div>
          <h1>Invoices</h1>
          <p>
            Manage invoices, payment status and billing records across DigiBills.
          </p>
        </div>
      </div>

      <div className="invoice-stats-grid">
        <MiniStat
          icon={<Receipt />}
          title="Total Invoices"
          value={counts.all}
          tone="blue"
        />

        <MiniStat
          icon={<CheckCircle />}
          title="Active"
          value={counts.active}
          tone="green"
        />

        <MiniStat
          icon={<Clock />}
          title="Paid"
          value={counts.paid}
          tone="purple"
        />

        <MiniStat
          icon={<XCircle />}
          title="Unpaid"
          value={counts.unpaid}
          tone="red"
        />
      </div>

      <div className="invoices-panel">
        <div className="invoices-panel-header">
          <div>
            <h3>Invoice Directory</h3>
            <span>
              {filteredInvoices.length} of {invoices.length} invoices
            </span>
          </div>

          <div className="invoices-toolbar">
            <div className="invoices-search">
              <Search size={16} />

              <input
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search invoices..."
              />
            </div>

            <select
              value={paymentStatus}
              onChange={(event) =>
                setPaymentStatus(
                  event.target.value
                )
              }
            >
              <option value="all">
                All Payments
              </option>
              <option value="paid">Paid</option>
              <option value="partial">
                Partial
              </option>
              <option value="unpaid">
                Unpaid
              </option>
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
              <option value="active">
                Active
              </option>
              <option value="inactive">
                Inactive
              </option>
            </select>
          </div>
        </div>

        {loading && (
          <div className="table-state">
            Loading invoices...
          </div>
        )}

        {!loading && error && (
          <div className="table-state negative">
            {error}
          </div>
        )}

        {!loading &&
          !error &&
          filteredInvoices.length === 0 && (
            <div className="table-state">
              No invoices found.
            </div>
          )}

        {!loading &&
          !error &&
          filteredInvoices.length > 0 && (
            <div className="invoices-table-wrap">
              <table className="invoices-table">
                <thead>
                  <tr>
                    <th>Invoice</th>
                    <th>Retailer</th>
                    <th>Customer</th>
                    <th>Date</th>
                    <th>Total</th>
                    <th>Payment</th>
                    <th>Status</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredInvoices.map(
                    (invoice) => (
                      <tr
                        key={invoice.id}
                        onClick={() =>
                          setSelectedInvoice(
                            invoice
                          )
                        }
                        style={{
                          cursor: "pointer",
                        }}
                      >
                        <td>
                          <div className="invoice-cell">
                            <div className="invoice-avatar">
                              #
                            </div>

                            <div>
                              <strong>
                                {invoice.invoice_number ||
                                  invoice.invoice_id}
                              </strong>

                              <small>
                                {invoice.invoice_id}
                              </small>
                            </div>
                          </div>
                        </td>

                        <td>
                          <small>
                            {invoice.retailer_id}
                          </small>
                        </td>

                        <td>
                          <small>
                            {invoice.customer_id}
                          </small>
                        </td>

                        <td>
                          {formatDate(
                            invoice.invoice_date
                          )}
                        </td>

                        <td>
                          <strong>
                            {formatMoney(
                              invoice.total_amount
                            )}
                          </strong>
                        </td>

                        <td>
                          <span
                            className={`status-badge ${invoice.payment_status}`}
                          >
                            {invoice.payment_status}
                          </span>
                        </td>

                        <td>
                          <span
                            className={`status-badge ${invoice.status}`}
                          >
                            {invoice.status}
                          </span>
                        </td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>
          )}
      </div>

      {selectedInvoice && (
        <div
          className="modal-backdrop"
          onClick={() =>
            setSelectedInvoice(null)
          }
        >
          <div
            className="invoice-details-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="modal-header">
              <div>
                <h2>Invoice Details</h2>
                <p>
                  Invoice information registered
                  on DigiBills.
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() =>
                  setSelectedInvoice(null)
                }
              >
                ×
              </button>
            </div>

            <div className="invoice-details-content">

              <div className="invoice-detail-group">
                <div className="invoice-detail-heading">
                  <span className="section-number">1.</span>
                  <div>
                    <h3>Invoice Information</h3>
                    <p>Core identification and ownership details.</p>
                  </div>
                </div>

                <div className="invoice-detail-grid">
                  <div className="invoice-detail-card">
                    <span>Invoice ID</span>
                    <strong>{selectedInvoice.invoice_id}</strong>
                  </div>

                  <div className="invoice-detail-card">
                    <span>Invoice Number</span>
                    <strong>{selectedInvoice.invoice_number || "—"}</strong>
                  </div>

                  <div className="invoice-detail-card">
                    <span>Retailer</span>
                    <strong>{selectedInvoice.retailer_id}</strong>
                  </div>

                  <div className="invoice-detail-card">
                    <span>Customer</span>
                    <strong>{selectedInvoice.customer_id}</strong>
                  </div>

                  <div className="invoice-detail-card">
                    <span>Invoice Date</span>
                    <strong>{formatDate(selectedInvoice.invoice_date)}</strong>
                  </div>
                </div>
              </div>

              <div className="invoice-detail-group">
                <div className="invoice-detail-heading">
                  <span className="section-number">2.</span>
                  <div>
                    <h3>Financial Summary</h3>
                    <p>Breakdown of the invoice amount.</p>
                  </div>
                </div>

                <div className="invoice-amount-grid">
                  <div className="invoice-detail-card">
                    <span>Subtotal</span>
                    <strong>{formatMoney(selectedInvoice.subtotal)}</strong>
                  </div>

                  <div className="invoice-detail-card">
                    <span>Discount</span>
                    <strong>{formatMoney(selectedInvoice.discount_amount)}</strong>
                  </div>

                  <div className="invoice-detail-card">
                    <span>Tax</span>
                    <strong>{formatMoney(selectedInvoice.tax_amount)}</strong>
                  </div>

                  <div className="invoice-total-card">
                    <span>Total Amount</span>
                    <strong>{formatMoney(selectedInvoice.total_amount)}</strong>
                  </div>
                </div>
              </div>

              <div className="invoice-detail-group">
                <div className="invoice-detail-heading">
                  <span className="section-number">3.</span>
                  <div>
                    <h3>Payment & Status</h3>
                    <p>Current payment and invoice state.</p>
                  </div>
                </div>

                <div className="invoice-detail-grid">
                  <div className="invoice-detail-card">
                    <span>Payment Status</span>
                    <strong className={`invoice-status-value ${selectedInvoice.payment_status}`}>
                      {selectedInvoice.payment_status}
                    </strong>
                  </div>

                  <div className="invoice-detail-card">
                    <span>Invoice Status</span>
                    <strong className={`invoice-status-value ${selectedInvoice.status}`}>
                      {selectedInvoice.status}
                    </strong>
                  </div>
                </div>
              </div>

              <div className="invoice-notes">
                <span>Notes</span>
                <p>
                  {selectedInvoice.notes || "No notes available for this invoice."}
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
