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
  ShieldCheck,
  UserRound,
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
    profile_image_url: string | null;
    status: string;
  };

  total_purchases: number;
  total_orders: number;
  amount_paid: number;
  refunds_received: number;
  active_warranties: number;
  product_transfers: number;

  invoice_status: {
    paid: number;
    partial: number;
    unpaid: number;
  };

  spending_trend: Array<{
    date: string;
    invoice_count: number;
    amount: number;
  }>;

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
  const [customerUnreadNotifications, setCustomerUnreadNotifications] =
    useState(0);

  const [spendingPeriod, setSpendingPeriod] =
    useState("this_month");

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

  useEffect(() => {
    let cancelled = false;

    async function loadCustomerUnreadNotifications() {
      try {
        const payload = await apiFetch<
          Array<{ is_read: boolean }>
        >("/customer/notifications");

        if (cancelled) {
          return;
        }

        const unreadCount = Array.isArray(payload)
          ? payload.filter(
              (notification) => !notification.is_read
            ).length
          : 0;

        setCustomerUnreadNotifications(unreadCount);
      } catch (err) {
        if (!cancelled) {
          console.error(
            "Failed to load customer notification count:",
            err
          );
          setCustomerUnreadNotifications(0);
        }
      }
    }

    loadCustomerUnreadNotifications();

    return () => {
      cancelled = true;
    };
  }, []);

  async function openInvoicePdf(invoiceId: string) {
    const token = sessionStorage.getItem("digibills_token");

    if (!token) {
      navigate("/login/customer");
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

  const apiBase =
    import.meta.env.VITE_API_BASE_URL ||
    "http://localhost:8000";

  const profileImageUrl = dashboard.customer?.profile_image_url
    ? dashboard.customer.profile_image_url.startsWith("http")
      ? dashboard.customer.profile_image_url
      : `${apiBase}${dashboard.customer.profile_image_url}`
    : "";

  const totalInvoices =
    dashboard.recent_invoices.length;

  const recentInvoices =
    dashboard.recent_invoices.slice(0, 2);

  const spendingTrend =
    dashboard.spending_trend || [];

  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth();

  const periodStart = (() => {
    switch (spendingPeriod) {
      case "last_month":
        return new Date(currentYear, currentMonth - 1, 1);

      case "last_3_months":
        return new Date(currentYear, currentMonth - 2, 1);

      case "last_6_months":
        return new Date(currentYear, currentMonth - 5, 1);

      case "this_year":
        return new Date(currentYear, 0, 1);

      case "all_time":
        return null;

      case "this_month":
      default:
        return new Date(currentYear, currentMonth, 1);
    }
  })();

  const filteredSpendingTrend = spendingTrend.filter((item) => {
    if (!periodStart) return true;

    const itemDate = new Date(`${item.date}T00:00:00`);

    if (Number.isNaN(itemDate.getTime())) {
      return false;
    }

    if (spendingPeriod === "last_month") {
      const lastMonth = new Date(
        currentYear,
        currentMonth - 1,
        1
      );

      const nextMonth = new Date(
        currentYear,
        currentMonth,
        1
      );

      return itemDate >= lastMonth && itemDate < nextMonth;
    }

    if (spendingPeriod === "last_3_months") {
      return itemDate >= periodStart && itemDate <= now;
    }

    if (spendingPeriod === "last_6_months") {
      return itemDate >= periodStart && itemDate <= now;
    }

    if (spendingPeriod === "this_year") {
      return itemDate >= periodStart && itemDate <= now;
    }

    return itemDate >= periodStart && itemDate <= now;
  });

  const filteredSpendingTotal =
    filteredSpendingTrend.reduce(
      (total, item) =>
        total + Number(item.amount || 0),
      0
    );

  const maxSpendingAmount = Math.max(
    ...filteredSpendingTrend.map((item) =>
      Number(item.amount || 0)
    ),
    1
  );

  const purchaseStatus = dashboard.invoice_status || {
    paid: 0,
    partial: 0,
    unpaid: 0,
  };

  const purchaseStatusTotal =
    purchaseStatus.paid +
    purchaseStatus.partial +
    purchaseStatus.unpaid;

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
            onClick={() => navigate("/customer/notifications")}
          >
            <Bell size={21} />
            {customerUnreadNotifications > 0 && (
              <span className="customer-reference-notification">
                {customerUnreadNotifications}
              </span>
            )}
          </button>

          <button
            type="button"
            className="customer-reference-avatar"
            aria-label="Open profile"
            onClick={() => navigate("/customer/profile")}
          >
            {profileImageUrl ? (
              <img
                src={profileImageUrl}
                alt={customerName}
              />
            ) : (
              initials
            )}
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

          <label className="customer-dashboard-spending-period">
            <select
              value={spendingPeriod}
              onChange={(event) =>
                setSpendingPeriod(event.target.value)
              }
              aria-label="Spending period"
            >
              <option value="this_month">This Month</option>
              <option value="last_month">Last Month</option>
              <option value="last_3_months">Last 3 Months</option>
              <option value="last_6_months">Last 6 Months</option>
              <option value="this_year">This Year</option>
              <option value="all_time">All Time</option>
            </select>
            <ChevronDown size={14} />
          </label>
        </div>

        <strong>
          {formatAmount(filteredSpendingTotal)}
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
          onClick={() => navigate("/customer/orders")}
          className="customer-reference-kpi"
        >
          <span className="customer-reference-kpi-icon purple">
            <Gift size={18} />
          </span>

          <span className="customer-reference-kpi-content">
            <small>Total Orders</small>
            <strong>{dashboard.total_orders}</strong>
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

      {/* Spending Overview */}
      <section className="customer-dashboard-spending-overview">
        <div className="customer-dashboard-spending-header">
          <div>
            <h2>Spending Overview</h2>
            <p>Your spending trend across purchase records.</p>
          </div>

          <span>
            {filteredSpendingTrend.length} record
            {filteredSpendingTrend.length === 1 ? "" : "s"}
          </span>
        </div>

        {filteredSpendingTrend.length === 0 ? (
          <div className="customer-dashboard-spending-empty">
            No spending data available yet.
          </div>
        ) : (
          <div className="customer-dashboard-spending-chart">
            {filteredSpendingTrend.map((item) => {
              const amount = Number(item.amount || 0);

              const height = Math.max(
                12,
                Math.round(
                  (amount / maxSpendingAmount) * 100
                )
              );

              return (
                <div
                  className="customer-dashboard-spending-column"
                  key={item.date}
                  title={`${formatDate(item.date)} — ${formatAmount(item.amount)}`}
                >
                  <div className="customer-dashboard-spending-value">
                    {formatAmount(item.amount)}
                  </div>

                  <div className="customer-dashboard-spending-bar-wrap">
                    <div
                      className="customer-dashboard-spending-bar"
                      style={{ height: `${height}%` }}
                    />
                  </div>

                  <small>
                    {formatDate(item.date)}
                  </small>

                  <span>
                    {item.invoice_count} invoice
                    {item.invoice_count === 1 ? "" : "s"}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Purchase Status */}
      <section className="customer-dashboard-purchase-status">
        <div className="customer-dashboard-purchase-status-header">
          <div>
            <h2>Purchase Status</h2>
            <p>Payment status across your purchase records.</p>
          </div>

          <strong>
            {purchaseStatusTotal} total
          </strong>
        </div>

        <div className="customer-dashboard-purchase-status-grid">

          <button
            type="button"
            className="customer-dashboard-purchase-status-card paid"
            onClick={() => navigate("/customer/invoices")}
          >
            <span className="customer-dashboard-purchase-status-dot" />

            <span>
              <small>Paid</small>
              <strong>{purchaseStatus.paid}</strong>
            </span>
          </button>

          <button
            type="button"
            className="customer-dashboard-purchase-status-card partial"
            onClick={() => navigate("/customer/invoices")}
          >
            <span className="customer-dashboard-purchase-status-dot" />

            <span>
              <small>Partial</small>
              <strong>{purchaseStatus.partial}</strong>
            </span>
          </button>

          <button
            type="button"
            className="customer-dashboard-purchase-status-card unpaid"
            onClick={() => navigate("/customer/invoices")}
          >
            <span className="customer-dashboard-purchase-status-dot" />

            <span>
              <small>Unpaid</small>
              <strong>{purchaseStatus.unpaid}</strong>
            </span>
          </button>

        </div>
      </section>

      {/* Quick Actions */}
      <section className="customer-dashboard-quick-actions">
        <div className="customer-dashboard-quick-actions-header">
          <div>
            <h2>Quick Actions</h2>
            <p>Access your most-used customer services.</p>
          </div>
        </div>

        <div className="customer-dashboard-quick-actions-grid">

          <button
            type="button"
            onClick={() => navigate("/customer/invoices")}
          >
            <span className="customer-dashboard-quick-action-icon blue">
              <Receipt size={19} />
            </span>
            <span>
              <strong>View Invoices</strong>
              <small>Manage your bills</small>
            </span>
            <ChevronRight size={17} />
          </button>

          <button
            type="button"
            onClick={() => navigate("/customer/payments")}
          >
            <span className="customer-dashboard-quick-action-icon green">
              <WalletCards size={19} />
            </span>
            <span>
              <strong>View Payments</strong>
              <small>Check payment records</small>
            </span>
            <ChevronRight size={17} />
          </button>

          <button
            type="button"
            onClick={() => navigate("/customer/bills")}
          >
            <span className="customer-dashboard-quick-action-icon blue">
              <Receipt size={19} />
            </span>
            <span>
              <strong>Upload Your Bill</strong>
              <small>Save a PDF bill to your locker</small>
            </span>
            <ChevronRight size={17} />
          </button>

          <button
            type="button"
            onClick={() => navigate("/customer/warranty")}
          >
            <span className="customer-dashboard-quick-action-icon purple">
              <ShieldCheck size={19} />
            </span>
            <span>
              <strong>My Warranty</strong>
              <small>View digital warranties</small>
            </span>
            <ChevronRight size={17} />
          </button>

          <button
            type="button"
            onClick={() => navigate("/customer/transfers")}
          >
            <span className="customer-dashboard-quick-action-icon violet">
              <Package size={19} />
            </span>
            <span>
              <strong>Transfer Bills</strong>
              <small>Transfer a bill</small>
            </span>
            <ChevronRight size={17} />
          </button>

          <button
            type="button"
            onClick={() => navigate("/customer/orders")}
          >
            <span className="customer-dashboard-quick-action-icon orange">
              <Gift size={19} />
            </span>
            <span>
              <strong>My Orders</strong>
              <small>View purchase records</small>
            </span>
            <ChevronRight size={17} />
          </button>

          <button
            type="button"
            onClick={() => navigate("/customer/support")}
          >
            <span className="customer-dashboard-quick-action-icon teal">
              <Headphones size={19} />
            </span>
            <span>
              <strong>Support</strong>
              <small>Get help with your account</small>
            </span>
            <ChevronRight size={17} />
          </button>

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
          onClick={() => navigate("/customer/profile")}
        >
          <UserRound size={19} />
          <span>My Profile</span>
        </button>

        <button
          type="button"
          onClick={() => navigate("/customer/warranty")}
        >
          <ShieldCheck size={19} />
          <span>My Warranty</span>
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
