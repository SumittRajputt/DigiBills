import { useEffect, useState } from "react";
import { ArrowLeft, Eye, RefreshCw } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { apiFetch } from "../api";

type CustomerInvoice = {
  id: string;
  invoice_id: string;
  retailer_id: string;
  employee_id: string | null;
  customer_id: string;
  invoice_number: string | null;
  invoice_date: string | null;
  item_names: string[];
  subtotal: string | number;
  discount_amount: string | number;
  tax_amount: string | number;
  total_amount: string | number;
  payment_status: string;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

type InvoiceItem = {
  id: string;
  invoice_id: string;
  product_variant_id: string;
  product_name: string;
  sku: string | null;
  quantity: number;
  unit_price: string | number;
  unit_cost: string | number;
  discount_amount: string | number;
  tax_rate: string | number;
  taxable_amount: string | number;
  tax_amount: string | number;
  line_total: string | number;
  created_at: string;
};

type CustomerInvoiceDetail = CustomerInvoice & {
  items: InvoiceItem[];
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

function statusLabel(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function statusClass(value: string) {
  return `customer-invoice-status customer-invoice-status-${value}`;
}

export default function CustomerInvoices() {
  const navigate = useNavigate();
  const { invoiceId } = useParams();

  const [invoices, setInvoices] = useState<CustomerInvoice[]>([]);
  const [detail, setDetail] =
    useState<CustomerInvoiceDetail | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadInvoices() {
    try {
      setLoading(true);
      setError("");

      const result =
        await apiFetch<CustomerInvoice[]>(
          "/customer/invoices"
        );

      setInvoices(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load your invoices."
      );
    } finally {
      setLoading(false);
    }
  }

  function openInvoicePdf(invoiceId: string) {
    const token = sessionStorage.getItem("digibills_token");

    if (!token) {
      navigate("/login/customer");
      return;
    }

    const apiBase =
      import.meta.env.VITE_API_BASE_URL ??
      "http://localhost:8000";

    const url =
      `${apiBase}/customer/invoices/` +
      `${encodeURIComponent(invoiceId)}/pdf`;

    const pdfWindow = window.open("", "_blank");

    if (!pdfWindow) {
      setError(
        "Unable to open the invoice PDF. Please allow pop-ups for DigiBills."
      );
      return;
    }

    fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then(async (response) => {
        if (!response.ok) {
          const body = await response.text();
          throw new Error(
            body || `Unable to generate invoice PDF (${response.status}).`
          );
        }

        return response.blob();
      })
      .then((blob) => {
        const pdfUrl = URL.createObjectURL(blob);

        pdfWindow.location.href = pdfUrl;

        window.setTimeout(() => {
          URL.revokeObjectURL(pdfUrl);
        }, 60_000);
      })
      .catch((err) => {
        pdfWindow.close();

        setError(
          err instanceof Error
            ? err.message
            : "Unable to open invoice PDF."
        );
      });
  }

  async function loadInvoiceDetail() {
    if (!invoiceId) return;

    try {
      setLoading(true);
      setError("");
      setDetail(null);

      const result =
        await apiFetch<CustomerInvoiceDetail>(
          `/customer/invoices/${encodeURIComponent(invoiceId)}`
        );

      setDetail(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load invoice details."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (invoiceId) {
      loadInvoiceDetail();
    } else {
      loadInvoices();
    }
  }, [invoiceId]);

  if (invoiceId) {
    if (loading) {
      return (
        <section className="dashboard customer-dashboard-page">
          <div className="page-heading">
            <span className="page-eyebrow">
              CUSTOMER ACCOUNT
            </span>
            <h1>Invoice Details</h1>
            <p>Loading invoice...</p>
          </div>
        </section>
      );
    }

    if (error) {
      return (
        <section className="dashboard customer-dashboard-page">
          <div className="page-heading">
            <span className="page-eyebrow">
              CUSTOMER ACCOUNT
            </span>
            <h1>Invoice Details</h1>
            <p>{error}</p>
          </div>

          <div className="panel">
            <div style={{ padding: "32px" }}>
              <button
                className="secondary-button"
                type="button"
                onClick={() =>
                  navigate("/customer/invoices")
                }
              >
                <ArrowLeft size={16} />
                Back to My Invoices
              </button>
            </div>
          </div>
        </section>
      );
    }

    if (!detail) return null;

    return (
      <section className="dashboard customer-dashboard-page">
        <div
          className="page-heading"
          style={{
            display: "flex",
            alignItems: "flex-end",
            justifyContent: "space-between",
            gap: "20px",
          }}
        >
          <div>
            <span className="page-eyebrow">
              CUSTOMER ACCOUNT
            </span>
            <h1>Invoice Details</h1>
            <p>
              View the complete details of your invoice.
            </p>
          </div>

          <button
            className="secondary-button"
            type="button"
            onClick={() =>
              navigate("/customer/invoices")
            }
          >
            <ArrowLeft size={16} />
            Back to My Invoices
          </button>
        </div>

        <div className="panel">
          <div
            style={{
              padding: "24px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              gap: "20px",
              flexWrap: "wrap",
            }}
          >
            <div>
              <div
                style={{
                  fontSize: "12px",
                  fontWeight: 700,
                  color: "#64748b",
                  marginBottom: "6px",
                }}
              >
                INVOICE
              </div>

              <h2
                style={{
                  margin: 0,
                  fontSize: "26px",
                }}
              >
                {detail.invoice_id}
              </h2>

              <div
                style={{
                  marginTop: "8px",
                  color: "#64748b",
                }}
              >
                Invoice date:{" "}
                <strong>
                  {formatDate(detail.invoice_date)}
                </strong>
              </div>
            </div>

            <span className={statusClass(detail.payment_status)}>
              {statusLabel(detail.payment_status)}
            </span>
          </div>

          <div
            style={{
              borderTop: "1px solid #e5e7eb",
              padding: "22px 24px",
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "18px",
            }}
          >
            <div>
              <small>Customer ID</small>
              <strong>{detail.customer_id}</strong>
            </div>

            <div>
              <small>Invoice Number</small>
              <strong>
                {detail.invoice_number || detail.invoice_id}
              </strong>
            </div>

            <div>
              <small>Invoice Status</small>
              <strong>{statusLabel(detail.status)}</strong>
            </div>

            <div>
              <small>Payment Status</small>
              <strong>
                {statusLabel(detail.payment_status)}
              </strong>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>Items</h3>
              <span>
                {detail.items.length} item
                {detail.items.length === 1 ? "" : "s"} on this invoice
              </span>
            </div>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>SKU</th>
                  <th>Qty</th>
                  <th>Unit Price</th>
                  <th>Taxable Value</th>
                  <th>Tax</th>
                  <th>Line Total</th>
                </tr>
              </thead>

              <tbody>
                {detail.items.length === 0 ? (
                  <tr>
                    <td colSpan={7}>
                      No items found for this invoice.
                    </td>
                  </tr>
                ) : (
                  detail.items.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <strong>{item.product_name}</strong>
                      </td>

                      <td>{item.sku || "—"}</td>

                      <td>{item.quantity}</td>

                      <td>{money(item.unit_price)}</td>

                      <td>
                        {money(item.taxable_amount)}
                      </td>

                      <td>
                        {money(item.tax_amount)}
                        <div
                          style={{
                            fontSize: "11px",
                            color: "#64748b",
                          }}
                        >
                          {item.tax_rate}%
                        </div>
                      </td>

                      <td>
                        <strong>
                          {money(item.line_total)}
                        </strong>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "minmax(0, 1fr) minmax(300px, 420px)",
            gap: "20px",
          }}
        >
          <div className="panel">
            <div className="panel-header">
              <div>
                <h3>Notes</h3>
                <span>Invoice information</span>
              </div>
            </div>

            <div style={{ padding: "24px" }}>
              {detail.notes || "No notes were added to this invoice."}
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <div>
                <h3>Invoice Summary</h3>
                <span>Amount breakdown</span>
              </div>
            </div>

            <div style={{ padding: "24px" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "8px 0",
                }}
              >
                <span>Subtotal</span>
                <strong>{money(detail.subtotal)}</strong>
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "8px 0",
                }}
              >
                <span>Discount</span>
                <strong>
                  {money(detail.discount_amount)}
                </strong>
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "8px 0",
                }}
              >
                <span>Tax</span>
                <strong>{money(detail.tax_amount)}</strong>
              </div>

              <div
                style={{
                  marginTop: "12px",
                  paddingTop: "16px",
                  borderTop: "1px solid #e5e7eb",
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: "20px",
                }}
              >
                <strong>Total</strong>
                <strong>{money(detail.total_amount)}</strong>
              </div>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="dashboard customer-dashboard-page">
      <div
        className="page-heading"
        style={{
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
          gap: "20px",
        }}
      >
        <div>
          <span className="page-eyebrow">
            CUSTOMER ACCOUNT
          </span>

          <h1>My Invoices</h1>

          <p>
            View all invoices associated with your DigiBills
            customer account.
          </p>
        </div>

        <button
          className="secondary-button"
          type="button"
          onClick={loadInvoices}
          disabled={loading}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="panel">
          <div style={{ padding: "32px" }}>
            Loading your invoices...
          </div>
        </div>
      ) : error ? (
        <div className="panel">
          <div style={{ padding: "32px" }}>
            <strong>Unable to load invoices</strong>
            <p>{error}</p>
          </div>
        </div>
      ) : (
        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>My Invoices</h3>
              <span>
                {invoices.length} invoice
                {invoices.length === 1 ? "" : "s"} found
              </span>
            </div>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Date</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {invoices.length === 0 ? (
                  <tr>
                    <td colSpan={5}>
                      You do not have any invoices yet.
                    </td>
                  </tr>
                ) : (
                  invoices.map((invoice) => (
                    <tr key={invoice.id}>
                      <td>
                        <strong>
                          {invoice.item_names?.length
                            ? invoice.item_names.join(", ")
                            : "No items"}
                        </strong>
                      </td>

                      <td>
                        {formatDate(invoice.invoice_date)}
                      </td>

                      <td>
                        <strong>
                          {money(invoice.total_amount)}
                        </strong>
                      </td>

                      <td>
                        <span
                          className={statusClass(
                            invoice.payment_status
                          )}
                        >
                          {statusLabel(
                            invoice.payment_status
                          )}
                        </span>
                      </td>

                      <td>
                        <button
                          className="secondary-button"
                          type="button"
                          onClick={() =>
                            openInvoicePdf(
                              invoice.invoice_id
                            )
                          }
                        >
                          <Eye size={15} />
                          View
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
