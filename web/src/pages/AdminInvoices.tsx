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
    <section className="dashboard">
      <div className="welcome-row">
        <div>
          <h1>Invoices</h1>
          <p>
            Manage all invoices generated on
            DigiBills.
          </p>
        </div>
      </div>

      <div className="stats-grid four">
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

      <div className="panel retailer-table-panel">
        <div className="table-toolbar">
          <div>
            <h3>All Invoices</h3>
            <span>
              {filteredInvoices.length} invoices
            </span>
          </div>

          <div className="table-controls">
            <div className="table-search">
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
            <div className="table-scroll">
              <table className="data-table">
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
                          <div className="retailer-cell">
                            <div className="retailer-avatar">
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
            className="user-details-modal"
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

            <div className="user-details-grid">
              <div>
                <span>Invoice ID</span>
                <strong>
                  {selectedInvoice.invoice_id}
                </strong>
              </div>

              <div>
                <span>Invoice Number</span>
                <strong>
                  {selectedInvoice.invoice_number ||
                    "—"}
                </strong>
              </div>

              <div>
                <span>Retailer</span>
                <strong>
                  {selectedInvoice.retailer_id}
                </strong>
              </div>

              <div>
                <span>Customer</span>
                <strong>
                  {selectedInvoice.customer_id}
                </strong>
              </div>

              <div>
                <span>Invoice Date</span>
                <strong>
                  {formatDate(
                    selectedInvoice.invoice_date
                  )}
                </strong>
              </div>

              <div>
                <span>Subtotal</span>
                <strong>
                  {formatMoney(
                    selectedInvoice.subtotal
                  )}
                </strong>
              </div>

              <div>
                <span>Discount</span>
                <strong>
                  {formatMoney(
                    selectedInvoice.discount_amount
                  )}
                </strong>
              </div>

              <div>
                <span>Tax</span>
                <strong>
                  {formatMoney(
                    selectedInvoice.tax_amount
                  )}
                </strong>
              </div>

              <div>
                <span>Total</span>
                <strong>
                  {formatMoney(
                    selectedInvoice.total_amount
                  )}
                </strong>
              </div>

              <div>
                <span>Payment Status</span>
                <strong>
                  {selectedInvoice.payment_status}
                </strong>
              </div>

              <div>
                <span>Status</span>
                <strong>
                  {selectedInvoice.status}
                </strong>
              </div>

              <div>
                <span>Notes</span>
                <strong>
                  {selectedInvoice.notes ||
                    "No notes"}
                </strong>
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
