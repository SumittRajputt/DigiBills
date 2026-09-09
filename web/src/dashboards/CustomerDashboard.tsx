import { useEffect, useState } from "react";
import {
  Bell,
  ChevronDown,
  ChevronRight,
  FileText,
  Gift,
  Headphones,
  Home,
  MoreHorizontal,
  Package,
  Receipt,
  ShoppingBag,
  WalletCards,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api";

type CustomerDashboardData = {
  customer?: {
    customer_id: string;
    full_name: string;
    phone_number: string;
    email: string | null;
    status: string;
  };

  total_purchases: number;
  amount_paid: number;
  refunds_received: number;
  active_warranties: number;
  product_transfers: number;

  recent_invoices: Array<{
    id: string;
    invoice_id: string;
    invoice_number: string;
    item_names: string[];
    total_amount: number;
    payment_status: string;
    invoice_date: string;
  }>;

  recent_payments: Array<{
    id: string;
    payment_id: string;
    invoice_id: string;
    item_names: string[];
    amount: number;
    payment_status: string;
    refund_amount: number;
    payment_method: string | null;
    paid_at: string;
  }>;

  warranties: Array<unknown>;
};

function formatAmount(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
}

function formatDate(value: string) {
  if (!value) return "";

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

function getInitials(value: string) {
  const parts = value
    .trim()
    .split(/[\s@._-]+/)
    .filter(Boolean);

  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }

  return value.slice(0, 2).toUpperCase();
}

export default function CustomerDashboard() {
  const navigate = useNavigate();

  const [dashboard, setDashboard] =
    useState<CustomerDashboardData | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
          : "Unable to load your dashboard."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  async function openInvoicePdf(invoiceId: string) {
    const token = sessionStorage.getItem("digibills_token");

    if (!token) {
      navigate("/login");
      return;
    }

    const apiBase =
      import.meta.env.VITE_API_BASE_URL ||
      "http://localhost:8000";

    const pdfWindow = window.open("", "_blank");

    if (!pdfWindow) {
      setError(
        "Unable to open the invoice PDF. Please allow pop-ups for DigiBills."
      );
      return;
    }

    try {
      const response = await fetch(
        `${apiBase}/customer/invoices/${invoiceId}/pdf`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        const body = await response.text();

        throw new Error(
          body ||
            `Unable to generate invoice PDF (${response.status}).`
        );
      }

      const blob = await response.blob();
      const pdfUrl = URL.createObjectURL(blob);

      pdfWindow.location.href = pdfUrl;

      window.setTimeout(() => {
        URL.revokeObjectURL(pdfUrl);
      }, 60_000);
    } catch (err) {
      pdfWindow.close();

      setError(
        err instanceof Error
          ? err.message
          : "Unable to open invoice PDF."
      );
    }
  }

  if (loading) {
    return (
      <section className="customer-dashboard-reference">
        <div className="customer-dashboard-loading">
          Loading your dashboard...
        </div>
      </section>
    );
  }

  if (error || !dashboard) {
    return (
      <section className="customer-dashboard-reference">
        <div className="customer-dashboard-error">
          <strong>Unable to load your dashboard</strong>
          <span>
            {error || "No dashboard data is available."}
          </span>

          <button
            type="button"
            onClick={loadDashboard}
          >
            Try Again
          </button>
        </div>
      </section>
    );
  }

  const customerName =
    dashboard.customer?.full_name || "Customer";

  const initials = getInitials(customerName);

  const totalInvoices =
    dashboard.recent_invoices.length;

  const recentInvoices =
    dashboard.recent_invoices.slice(0, 2);

  return (
    <section className="customer-dashboard-reference">

      {/* Mobile reference header */}
      <header className="customer-reference-header">
        <div className="customer-reference-brand">
          <span className="customer-reference-brand-icon">
            ✣
          </span>

          <span>DigiBills</span>
        </div>

        <div className="customer-reference-header-actions">
          <button
            type="button"
            className="customer-reference-bell"
            aria-label="Notifications"
            onClick={() => navigate("/customer/settings")}
          >
            <Bell size={21} />
            <span className="customer-reference-notification">
              1
            </span>
          </button>

          <button
            type="button"
            className="customer-reference-avatar"
            aria-label="Open profile"
            onClick={() => navigate("/customer/profile")}
          >
            {initials}
          </button>
        </div>
      </header>

      {/* Greeting */}
      <div className="customer-reference-greeting">
        <h1>Hello, {customerName}! <span>👋</span></h1>
        <p>Welcome back 👋</p>
      </div>

      {/* Total spent hero card */}
      <div className="customer-reference-total-card">
        <div className="customer-reference-total-top">
          <span>Total Spent</span>

          <button type="button">
            This Month
            <ChevronDown size={14} />
          </button>
        </div>

        <strong>
          {formatAmount(dashboard.total_purchases)}
        </strong>

        <div className="customer-reference-bars">
          <i />
          <i />
          <i />
          <i />
          <i />
          <i />
          <i />
        </div>
      </div>

      {/* Four KPI cards */}
      <div className="customer-reference-kpis">

        <button
          type="button"
          onClick={() => navigate("/customer/invoices")}
          className="customer-reference-kpi"
        >
          <span className="customer-reference-kpi-icon blue">
            <Receipt size={18} />
          </span>

          <span className="customer-reference-kpi-content">
            <small>Total Invoices</small>
            <strong>{totalInvoices}</strong>
          </span>
        </button>

        <button
          type="button"
          onClick={() => navigate("/customer/products")}
          className="customer-reference-kpi"
        >
          <span className="customer-reference-kpi-icon purple">
            <Gift size={18} />
          </span>

          <span className="customer-reference-kpi-content">
            <small>Total Orders</small>
            <strong>—</strong>
          </span>
        </button>

        <button
          type="button"
          onClick={() => navigate("/customer/payments")}
          className="customer-reference-kpi"
        >
          <span className="customer-reference-kpi-icon green">
            <WalletCards size={18} />
          </span>

          <span className="customer-reference-kpi-content">
            <small>Paid Amount</small>
            <strong>
              {formatAmount(dashboard.amount_paid)}
            </strong>
          </span>
        </button>

        <button
          type="button"
          onClick={() => navigate("/customer/payments")}
          className="customer-reference-kpi"
        >
          <span className="customer-reference-kpi-icon red">
            <Gift size={18} />
          </span>

          <span className="customer-reference-kpi-content">
            <small>Refunds</small>
            <strong>
              {formatAmount(dashboard.refunds_received)}
            </strong>
          </span>
        </button>

      </div>

      {/* Recent invoices */}
      <section className="customer-reference-section">
        <div className="customer-reference-section-header">
          <h2>Recent Invoices</h2>

          <button
            type="button"
            onClick={() => navigate("/customer/invoices")}
          >
            View All
          </button>
        </div>

        <div className="customer-reference-invoices">

          {recentInvoices.length === 0 ? (
            <div className="customer-reference-empty">
              No invoices found.
            </div>
          ) : (
            recentInvoices.map((invoice) => (
              <button
                type="button"
                className="customer-reference-invoice"
                key={invoice.invoice_id}
                onClick={() =>
                  openInvoicePdf(invoice.invoice_id)
                }
              >
                <span className="customer-reference-invoice-icon">
                  <FileText size={19} />
                </span>

                <span className="customer-reference-invoice-info">
                  <strong>
                    #{invoice.invoice_number || invoice.invoice_id}
                  </strong>

                  <small>
                    {formatDate(invoice.invoice_date)}
                  </small>
                </span>

                <span className="customer-reference-invoice-right">
                  <strong>
                    {formatAmount(invoice.total_amount)}
                  </strong>

                  <span
                    className={`customer-reference-status ${
                      invoice.payment_status
                        ?.toLowerCase()
                        .includes("paid")
                        ? "paid"
                        : ""
                    }`}
                  >
                    {invoice.payment_status || "Pending"}
                  </span>
                </span>

                <ChevronRight size={18} />
              </button>
            ))
          )}

        </div>
      </section>

      {/* Mobile bottom navigation */}
      <nav className="customer-reference-bottom-nav">

        <button
          type="button"
          className="active"
          onClick={() => navigate("/customer")}
        >
          <Home size={19} />
          <span>Home</span>
        </button>

        <button
          type="button"
          onClick={() => navigate("/customer/invoices")}
        >
          <FileText size={19} />
          <span>Invoices</span>
        </button>

        <button
          type="button"
          onClick={() => navigate("/customer/products")}
        >
          <ShoppingBag size={19} />
          <span>Orders</span>
        </button>

        <button
          type="button"
          onClick={() => navigate("/customer/support")}
        >
          <Headphones size={19} />
          <span>Support</span>
        </button>

        <button
          type="button"
          className="more"
          onClick={() =>
            window.dispatchEvent(
              new CustomEvent("digibills:open-mobile-menu")
            )
          }
        >
          <MoreHorizontal size={20} />
          <span>More</span>
        </button>

      </nav>

    </section>
  );
}
