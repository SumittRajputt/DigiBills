import { useNavigate } from "react-router-dom";

import {
  ArrowRight,
  BadgeIndianRupee,
  FileText,
  Gift,
  Package,
  RotateCcw,
  ShieldCheck,
  ShoppingBag,
} from "lucide-react";
import { useEffect, useState } from "react";
import { apiFetch } from "../api";

type CustomerDashboardData = {
  customer: {
    customer_id: string;
    full_name: string;
    phone_number: string;
    email: string | null;
    status: string;
  };

  total_purchases: string | number;
  total_invoices: number;
  amount_paid: string | number;
  refunds_received: string | number;
  outstanding_amount: string | number;

  invoice_status: {
    paid: number;
    partial: number;
    unpaid: number;
  };

  spending_trend: Array<{
    date: string;
    invoice_count: number;
    amount: string | number;
  }>;

  recent_invoices: Array<{
    id: string;
    invoice_id: string;
    invoice_number?: string | null;
    item_names: string[];
    total_amount: string | number;
    payment_status: string;
    invoice_date: string | null;
  }>;

  recent_payments: Array<{
    id: string;
    payment_id: string;
    invoice_id: string;
    item_names: string[];
    amount: string | number;
    payment_status: string;
    refund_amount: string | number;
    payment_method: string;
    paid_at: string | null;
  }>;

  active_warranties: number;
  product_transfers: number;

  warranties: Array<{
    id: string;
    warranty_id: string;
    invoice_id: string;
    product_variant_id: string;
    product_name: string;
    start_date: string;
    end_date: string;
    duration_months: number;
    is_transferable: boolean;
    status: string;
  }>;
};

function formatAmount(value: string | number) {
  const amount = Number(value || 0);

  return `₹${amount.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function formatDate(value: string) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function Stat({
  icon,
  title,
  value,
  tone,
}: {
  icon: React.ReactNode;
  title: string;
  value: string;
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

function PanelHeader({
  title,
  count,
}: {
  title: string;
  count?: number;
}) {
  return (
    <div className="panel-header">
      <div>
        <h3>{title}</h3>

        {typeof count === "number" && (
          <span>{count} records</span>
        )}
      </div>

      <button type="button">View All</button>
    </div>
  );
}

function Mini({
  icon,
  title,
  value,
}: {
  icon: React.ReactNode;
  title: string;
  value: string;
}) {
  return (
    <div className="mini-card">
      <div className="mini-icon">{icon}</div>

      <span>{title}</span>

      <strong>{value}</strong>
    </div>
  );
}

export default function CustomerDashboard() {
  const navigate = useNavigate();
  const [dashboard, setDashboard] =
    useState<CustomerDashboardData | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  function openInvoicePdf(invoiceId: string) {
    const token = sessionStorage.getItem("digibills_token");

    if (!token) {
      window.location.href = "/login";
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
            body ||
              `Unable to generate invoice PDF (${response.status}).`
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

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");

      const result =
        await apiFetch<CustomerDashboardData>(
          "/customer/dashboard"
        );

      setDashboard(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load customer dashboard."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  if (loading) {
    return (
      <section className="dashboard customer-dashboard-page">
        <div className="welcome-row">
          <div>
            <h1>Customer Dashboard</h1>
            <p>Loading your account overview...</p>
          </div>
        </div>

        <div className="panel">
          <div className="table-state">
            Loading dashboard...
          </div>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="dashboard customer-dashboard-page">
        <div className="welcome-row">
          <div>
            <h1>Customer Dashboard</h1>
            <p>Unable to load your account overview.</p>
          </div>
        </div>

        <div className="panel">
          <div className="table-state negative">
            {error}
          </div>
        </div>
      </section>
    );
  }

  if (!dashboard) {
    return (
      <section className="dashboard customer-dashboard-page">
        <div className="welcome-row">
          <div>
            <h1>Customer Dashboard</h1>
            <p>No dashboard data is available.</p>
          </div>
        </div>

        <div className="panel">
          <div className="table-state">
            No customer dashboard data found.
          </div>
        </div>
      </section>
    );
  }

  const customerName =
    dashboard.customer?.full_name || "Customer";

  return (
    <section className="dashboard customer-dashboard-page">
      <div className="welcome-row">
        <div>
          <h1>
            Welcome back, {customerName}! 👋
          </h1>

          <p>
            Here's your account overview.
          </p>
        </div>
      </div>

      <div className="stats-grid four">
        <Stat
          icon={<BadgeIndianRupee />}
          title="Total Spent"
          value={formatAmount(dashboard.total_purchases)}
          tone="green"
        />

        <Stat
          icon={<BadgeIndianRupee />}
          title="Paid Amount"
          value={formatAmount(dashboard.amount_paid)}
          tone="blue"
        />

        <Stat
          icon={<Gift />}
          title="Refunds Received"
          value={formatAmount(
            dashboard.refunds_received
          )}
          tone="purple"
        />
      </div>

      <div className="panel-grid customer-grid">
        <div className="panel">
          <PanelHeader
            title="Recent Invoices"
            count={dashboard.recent_invoices.length}
          />

          {dashboard.recent_invoices.length === 0 ? (
            <div className="table-state">
              No invoices found.
            </div>
          ) : (
            dashboard.recent_invoices.map((invoice) => (
              <div
                className="order-row"
                key={invoice.invoice_id}
                role="button"
                tabIndex={0}
                onClick={() =>
                  openInvoicePdf(invoice.invoice_id)
                }
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter" ||
                    event.key === " "
                  ) {
                    event.preventDefault();
                    openInvoicePdf(invoice.invoice_id);
                  }
                }}
                style={{ cursor: "pointer" }}
              >
                <div>
                  <b>
                    {invoice.item_names?.length
                      ? invoice.item_names.join(", ")
                      : "No items"}
                  </b>

                  <small>
                    {formatDate(invoice.invoice_date ?? "")}
                  </small>
                </div>

                <strong>
                  {formatAmount(invoice.total_amount)}
                </strong>

                <span
                  className={`status ${invoice.payment_status}`}
                >
                  {invoice.payment_status}
                </span>
              </div>
            ))
          )}
        </div>

        <div className="panel">
          <PanelHeader
            title="Recent Payments"
            count={dashboard.recent_payments.length}
          />

          {dashboard.recent_payments.length === 0 ? (
            <div className="table-state">
              No payments found.
            </div>
          ) : (
            dashboard.recent_payments.map((payment) => (
              <div
                className="order-row"
                key={payment.payment_id}
                role="button"
                tabIndex={0}
                onClick={() =>
                  openInvoicePdf(payment.invoice_id)
                }
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter" ||
                    event.key === " "
                  ) {
                    event.preventDefault();
                    openInvoicePdf(payment.invoice_id);
                  }
                }}
                style={{ cursor: "pointer" }}
              >
                <div>
                  <b>
                    {payment.item_names?.length
                      ? payment.item_names.join(", ")
                      : "No items"}
                  </b>

                  <small>
                    {formatDate(payment.paid_at ?? "")}
                  </small>
                </div>

                <strong>
                  {formatAmount(payment.amount)}
                </strong>

                <span
                  className={`status ${
                    Number(payment.refund_amount || 0) >=
                    Number(payment.amount || 0)
                      ? "refunded"
                      : payment.payment_status
                  }`}
                >
                  {Number(payment.refund_amount || 0) >=
                  Number(payment.amount || 0)
                    ? "refunded"
                    : payment.payment_status}
                </span>
              </div>
            ))
          )}
        </div>


      </div>

      <div className="panel customer-dashboard-summary">
        <div className="panel-header">
          <div>
            <h3>Account Summary</h3>
            <span>
              Your current billing and account position
            </span>
          </div>
        </div>

        <div className="customer-summary-grid">
          <div>
            <span>Total Invoices</span>
            <strong>
              {dashboard.total_invoices}
            </strong>
          </div>

          <div>
            <span>Paid Invoices</span>
            <strong>
              {dashboard.invoice_status.paid}
            </strong>
          </div>

          <div>
            <span>Partial Invoices</span>
            <strong>
              {dashboard.invoice_status.partial}
            </strong>
          </div>

          <div>
            <span>Unpaid Invoices</span>
            <strong>
              {dashboard.invoice_status.unpaid}
            </strong>
          </div>

          <div>
            <span>Outstanding</span>
            <strong>
              {formatAmount(
                dashboard.outstanding_amount
              )}
            </strong>
          </div>
        </div>
      </div>
    </section>
  );
}
