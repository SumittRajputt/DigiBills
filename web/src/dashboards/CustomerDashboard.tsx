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

type CustomerBill = {
  source: "retailer" | "uploaded";
  bill_id: string;
  bill_number: string | null;
  bill_date: string | null;
  products: Array<{
    product_name: string | null;
  }>;
  total_amount: number | string;
  payment_status: string;
  status: string;
  retailer_name: string | null;
  uploaded_bill_id: string | null;
  digibill_id: string | null;
  created_at: string;
  updated_at: string;
};

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

  const [customerBills, setCustomerBills] =
    useState<CustomerBill[]>([]);

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

      const [dashboardResult, billsResult] =
        await Promise.all([
          apiFetch<CustomerDashboardData>(
            "/customer/dashboard"
          ),
          apiFetch<CustomerBill[]>(
            "/customer/bills"
          ),
        ]);

      setDashboard(dashboardResult);
      setCustomerBills(
        Array.isArray(billsResult)
          ? billsResult
          : []
      );
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

  const customerName =
    dashboard?.customer?.full_name || "Customer";

  const totalInvoices =
    customerBills.length;

  const recentInvoices =
    customerBills.slice(0, 2).map((bill) => ({
      id: bill.bill_id,
      invoice_id: bill.bill_id,
      invoice_number:
        bill.bill_number || bill.bill_id,
      item_names: bill.products
        .map((product) => product.product_name)
        .filter(
          (name): name is string =>
            Boolean(name)
        ),
      total_amount: Number(
        bill.total_amount || 0
      ),
      payment_status:
        bill.payment_status || bill.status,
      invoice_date:
        bill.bill_date || bill.created_at,
      source: bill.source,
    }));

  async function openInvoicePdf(invoiceId: string) {
    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(
        `/api/customer/invoices/${invoiceId}/pdf`,
        {
          headers: token
            ? { Authorization: `Bearer ${token}` }
            : {},
        }
      );

      if (!response.ok) {
        throw new Error("Unable to open invoice.");
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank");
    } catch (err) {
      console.error("Failed to open invoice PDF:", err);
    }
  }

  const productCount = Number(
    (dashboard as (CustomerDashboardData & { my_products?: number }) | null)?.my_products ?? 0
  );

  if (loading) {
    return (
      <div style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "system-ui, sans-serif",
        color: "#475569"
      }}>
        Loading your DigiBills dashboard...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "12px",
        padding: "24px",
        textAlign: "center",
        fontFamily: "system-ui, sans-serif",
        color: "#334155"
      }}>
        <strong>Unable to load DigiBills</strong>
        <span>{error}</span>
        <button
          type="button"
          onClick={loadDashboard}
          style={{
            padding: "10px 18px",
            border: 0,
            borderRadius: "10px",
            cursor: "pointer"
          }}
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!dashboard) {
    return null;
  }

  return (
    <section className="db-home">
      <header className="db-home-header">
        <div>
          <div className="db-home-brand">
            <span className="db-home-brand-mark">✣</span>
            <span>DigiBills</span>
          </div>

          <div className="db-home-welcome">
            <h1>
              Hi, {customerName.split(" ")[0]} 👋
            </h1>
            <p>
              Your purchases, bills and warranties — all in one place.
            </p>
          </div>
        </div>

        <button
          type="button"
          className="db-home-notification"
          aria-label="Notifications"
          onClick={() => navigate("/customer/notifications")}
        >
          <Bell size={21} />
          {customerUnreadNotifications > 0 && (
            <span>{customerUnreadNotifications}</span>
          )}
        </button>
      </header>

      <div className="db-home-actions">
        <button
          type="button"
          className="db-home-add-bill"
          onClick={() => navigate("/customer/invoices")}
        >
          <span className="db-home-add-icon">+</span>
          <span>
            <strong>Add Bill</strong>
            <small>Scan or upload your purchase bill</small>
          </span>
        </button>

        <button
          type="button"
          className="db-home-secondary-action"
          onClick={() => navigate("/customer/invoices")}
        >
          <Receipt size={19} />
          <span>My Bills</span>
        </button>
      </div>

      <section className="db-home-summary">
        <button
          type="button"
          className="db-home-summary-card"
          onClick={() => navigate("/customer/invoices")}
        >
          <span className="db-home-summary-icon bills">
            <FileText size={20} />
          </span>
          <span>
            <small>My Bills</small>
            <strong>{totalInvoices}</strong>
          </span>
          <ChevronRight size={18} />
        </button>

        <button
          type="button"
          className="db-home-summary-card"
          onClick={() => navigate("/customer/products")}
        >
          <span className="db-home-summary-icon products">
            <Package size={20} />
          </span>
          <span>
            <small>My Products</small>
            <strong>{productCount}</strong>
          </span>
          <ChevronRight size={18} />
        </button>

        <button
          type="button"
          className="db-home-summary-card"
          onClick={() => navigate("/customer/warranty")}
        >
          <span className="db-home-summary-icon warranty">
            <ShieldCheck size={20} />
          </span>
          <span>
            <small>Active Warranty</small>
            <strong>{dashboard.active_warranties}</strong>
          </span>
          <ChevronRight size={18} />
        </button>
      </section>

      <section className="db-home-section">
        <div className="db-home-section-heading">
          <div>
            <h2>Recent Bills</h2>
            <p>Your latest digital purchase records.</p>
          </div>

          <button
            type="button"
            onClick={() => navigate("/customer/invoices")}
          >
            View all
            <ChevronRight size={16} />
          </button>
        </div>

        {recentInvoices.length > 0 ? (
          <div className="db-home-bills">
            {recentInvoices.map((invoice) => (
              <article
                className="db-home-bill-card"
                key={invoice.id || invoice.invoice_id}
              >
                <div className="db-home-bill-icon">
                  <Receipt size={21} />
                </div>

                <div className="db-home-bill-main">
                  <strong>
                    {invoice.item_names?.length
                      ? invoice.item_names.slice(0, 2).join(", ")
                      : "Purchase"}
                  </strong>

                  <span>
                    Bill #{invoice.invoice_number || invoice.invoice_id}
                  </span>

                  <small>{formatDate(invoice.invoice_date)}</small>
                </div>

                <div className="db-home-bill-right">
                  <strong>{formatAmount(invoice.total_amount)}</strong>
                  <span
                    className={`db-home-status ${String(
                      invoice.payment_status || ""
                    ).toLowerCase()}`}
                  >
                    {invoice.payment_status || "Recorded"}
                  </span>
                </div>

                <button
                  type="button"
                  className="db-home-bill-arrow"
                  aria-label="Open bill"
                  onClick={() => {
                    if (invoice.source === "uploaded") {
                      navigate(
                        `/customer/invoices/${encodeURIComponent(
                          invoice.invoice_id
                        )}`
                      );
                    } else {
                      openInvoicePdf(
                        invoice.invoice_id
                      );
                    }
                  }}
                >
                  <ChevronRight size={18} />
                </button>
              </article>
            ))}
          </div>
        ) : (
          <div className="db-home-empty">
            <div className="db-home-empty-icon">
              <FileText size={24} />
            </div>
            <h3>No bills yet</h3>
            <p>
              Add your first bill to start building your digital purchase
              locker.
            </p>
            <button
              type="button"
              onClick={() => navigate("/customer/invoices")}
            >
              Add your first bill
            </button>
          </div>
        )}
      </section>

      <section className="db-home-section">
        <div className="db-home-section-heading">
          <div>
            <h2>Warranty Protection</h2>
            <p>Keep track of the products currently covered.</p>
          </div>

          <button
            type="button"
            onClick={() => navigate("/customer/warranty")}
          >
            View warranties
            <ChevronRight size={16} />
          </button>
        </div>

        {dashboard.active_warranties > 0 ? (
          <div className="db-home-warranty-card">
            <div className="db-home-warranty-icon">
              <ShieldCheck size={25} />
            </div>

            <div>
              <strong>
                {dashboard.active_warranties} active{" "}
                {dashboard.active_warranties === 1
                  ? "warranty"
                  : "warranties"}
              </strong>
              <p>
                Your registered products with active warranty protection are
                available in My Warranty.
              </p>
            </div>

            <button
              type="button"
              onClick={() => navigate("/customer/warranty")}
            >
              View
            </button>
          </div>
        ) : (
          <div className="db-home-empty db-home-empty-small">
            <div className="db-home-empty-icon">
              <ShieldCheck size={24} />
            </div>
            <h3>No active warranties</h3>
            <p>
              Warranty information will appear here when your purchases
              include warranty coverage.
            </p>
          </div>
        )}
      </section>

      <section className="db-home-spending">
        <div>
          <span className="db-home-spending-label">Purchase Summary</span>
          <h2>{formatAmount(dashboard.amount_paid)}</h2>
          <p>Total amount paid across your recorded purchases.</p>
        </div>

        <div className="db-home-spending-stats">
          <div>
            <span>Orders</span>
            <strong>{dashboard.total_orders}</strong>
          </div>
          <div>
            <span>Refunds</span>
            <strong>{formatAmount(dashboard.refunds_received)}</strong>
          </div>
        </div>
      </section>
      </section>
  );

}
