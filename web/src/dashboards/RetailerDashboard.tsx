import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock3,
  FileText,
  IndianRupee,
  Package,
  Users,
  Wallet,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../api";
import "../index.css";

type SalesOverviewItem = {
  date: string;
  amount: string;
};

type PaymentMethodItem = {
  method: string;
  amount: string;
  percentage: string;
};

type RecentInvoiceItem = {
  invoice_id: string;
  customer_id: string;
  invoice_number: string | null;
  total_amount: string;
  payment_status: string;
  status: string;
  invoice_date: string;
};

type RecentPaymentItem = {
  payment_id: string;
  invoice_id: string;
  amount: string;
  payment_method: string;
  payment_status: string;
  paid_at: string;
};

type LowStockItem = {
  product_variant_id: string;
  sku: string;
  variant_name: string;
  quantity_on_hand: number;
  quantity_reserved: number;
  quantity_available: number;
  reorder_level: number;
};

type RetailerDashboardResponse = {
  total_customers: number;
  total_invoices: number;
  total_sales: string;
  payments_collected: string;
  outstanding_amount: string;
  paid_invoices: number;
  partial_invoices: number;
  unpaid_invoices: number;
  sales_overview: SalesOverviewItem[];
  payment_methods: PaymentMethodItem[];
  recent_invoices: RecentInvoiceItem[];
  recent_payments: RecentPaymentItem[];
  low_stock_items: LowStockItem[];
};

function formatMoney(value: string | number) {
  const amount = Number(value || 0);

  return amount.toLocaleString("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  });
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatMethod(value: string) {
  return value
    .replace(/[_-]/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function getInitials(value: string) {
  const words = value.trim().split(/\s+/);

  if (words.length === 1) {
    return words[0].slice(0, 2).toUpperCase();
  }

  return `${words[0][0]}${words[1][0]}`.toUpperCase();
}

function Stat({
  icon,
  title,
  value,
  subtitle,
  tone,
}: {
  icon: React.ReactNode;
  title: string;
  value: string;
  subtitle: string;
  tone: string;
}) {
  return (
    <div className="retailer-stat-card">
      <div className={`retailer-stat-icon ${tone}`}>
        {icon}
      </div>

      <div className="retailer-stat-content">
        <span>{title}</span>
        <strong>{value}</strong>
        <small>{subtitle}</small>
      </div>
    </div>
  );
}

function PanelHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: string;
}) {
  return (
    <div className="retailer-panel-header">
      <div>
        <h3>{title}</h3>
        {subtitle && <span>{subtitle}</span>}
      </div>

      {action && (
        <button type="button" className="retailer-panel-action">
          {action}
        </button>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();

  return (
    <span className={`retailer-status ${normalized}`}>
      {normalized}
    </span>
  );
}

export default function RetailerDashboard() {
  const [data, setData] =
    useState<RetailerDashboardResponse | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadDashboard() {
      try {
        setLoading(true);
        setError("");

        const result =
          await apiFetch<RetailerDashboardResponse>(
            "/retailer/dashboard"
          );

        if (mounted) {
          setData(result);
        }
      } catch (err) {
        if (mounted) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load retailer dashboard."
          );
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      mounted = false;
    };
  }, []);

  const chartData = useMemo(() => {
    if (!data) {
      return [];
    }

    return data.sales_overview.map((item) => ({
      date: new Date(item.date).toLocaleDateString(
        "en-IN",
        {
          day: "2-digit",
          month: "short",
        }
      ),
      amount: Number(item.amount || 0),
    }));
  }, [data]);

  if (loading) {
    return (
      <section className="dashboard retailer-dashboard-page">
        <div className="dashboard-state">
          <div className="dashboard-state-card">
            <div className="dashboard-state-icon">
              <BarChart3 size={20} />
            </div>

            <h2>Loading dashboard...</h2>

            <p>
              Fetching your latest business information.
            </p>
          </div>
        </div>
      </section>
    );
  }

  if (error || !data) {
    return (
      <section className="dashboard retailer-dashboard-page">
        <div className="dashboard-state">
          <div className="dashboard-state-card negative">
            <div className="dashboard-state-icon">
              <AlertTriangle size={20} />
            </div>

            <h2>Unable to load dashboard</h2>

            <p>
              {error || "Dashboard data is unavailable."}
            </p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="dashboard retailer-dashboard-page">
      <div className="retailer-dashboard-header">
        <div>
          <div className="retailer-eyebrow">
            RETAILER OVERVIEW
          </div>

          <h1>Welcome back! 👋</h1>

          <p>
            Here's your latest business performance at a glance.
          </p>
        </div>

        <div className="retailer-dashboard-date">
          <span>Dashboard</span>
          <strong>Live business overview</strong>
        </div>
      </div>

      <div className="retailer-stats-grid">
        <Stat
          icon={<IndianRupee size={18} />}
          title="Total Sales"
          value={formatMoney(data.total_sales)}
          subtitle={`${data.total_invoices} total invoices`}
          tone="green"
        />

        <Stat
          icon={<Wallet size={18} />}
          title="Payments Collected"
          value={formatMoney(data.payments_collected)}
          subtitle={`${data.paid_invoices} invoices paid`}
          tone="blue"
        />

        <Stat
          icon={<FileText size={18} />}
          title="Outstanding Amount"
          value={formatMoney(data.outstanding_amount)}
          subtitle={`${data.partial_invoices} partial · ${data.unpaid_invoices} unpaid`}
          tone="orange"
        />

        <Stat
          icon={<Users size={18} />}
          title="Total Customers"
          value={data.total_customers.toLocaleString("en-IN")}
          subtitle="Active customer base"
          tone="purple"
        />
      </div>

      <div className="retailer-status-grid">
        <div className="retailer-status-card paid">
          <div className="retailer-status-icon">
            <CheckCircle2 size={17} />
          </div>

          <div>
            <span>Paid Invoices</span>
            <strong>{data.paid_invoices}</strong>
          </div>
        </div>

        <div className="retailer-status-card partial">
          <div className="retailer-status-icon">
            <Clock3 size={17} />
          </div>

          <div>
            <span>Partial Invoices</span>
            <strong>{data.partial_invoices}</strong>
          </div>
        </div>

        <div className="retailer-status-card unpaid">
          <div className="retailer-status-icon">
            <FileText size={17} />
          </div>

          <div>
            <span>Unpaid Invoices</span>
            <strong>{data.unpaid_invoices}</strong>
          </div>
        </div>
      </div>

      <div className="retailer-dashboard-grid">
        <div className="retailer-panel retailer-sales-panel">
          <PanelHeader
            title="Sales Overview"
            subtitle="Invoice sales over time"
          />

          <div className="retailer-chart">
            {chartData.length > 0 ? (
              <ResponsiveContainer
                width="100%"
                height={260}
              >
                <AreaChart
                  data={chartData}
                  margin={{
                    top: 8,
                    right: 10,
                    left: 4,
                    bottom: 0,
                  }}
                >
                  <defs>
                    <linearGradient
                      id="salesGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="0%"
                        stopOpacity={0.28}
                      />
                      <stop
                        offset="100%"
                        stopOpacity={0.03}
                      />
                    </linearGradient>
                  </defs>

                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="#edf1f6"
                  />

                  <XAxis
                    dataKey="date"
                    axisLine={false}
                    tickLine={false}
                    tick={{
                      fontSize: 9,
                      fill: "#8995a6",
                    }}
                  />

                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{
                      fontSize: 9,
                      fill: "#8995a6",
                    }}
                    tickFormatter={(value) =>
                      `₹${Number(value).toLocaleString(
                        "en-IN"
                      )}`
                    }
                  />

                  <Tooltip
                    formatter={(value: number | string) => [
                      formatMoney(Number(value)),
                      "Sales",
                    ]}
                    contentStyle={{
                      borderRadius: 8,
                      border: "1px solid #e5eaf1",
                      boxShadow:
                        "0 8px 25px rgba(20,35,55,.10)",
                      fontSize: 11,
                    }}
                  />

                  <Area
                    type="monotone"
                    dataKey="amount"
                    stroke="#11a36a"
                    fill="url(#salesGradient)"
                    strokeWidth={2.5}
                    dot={false}
                    activeDot={{
                      r: 5,
                    }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="retailer-empty-state">
                <BarChart3 size={24} />
                <span>No sales data available yet.</span>
              </div>
            )}
          </div>
        </div>

        <div className="retailer-panel retailer-payment-panel">
          <PanelHeader
            title="Payment Methods"
            subtitle="Collected payments"
          />

          {data.payment_methods.length > 0 ? (
            <div className="payment-method-list">
              {data.payment_methods.map((item) => (
                <div
                  className="payment-method-row"
                  key={item.method}
                >
                  <div className="payment-method-icon">
                    <Wallet size={15} />
                  </div>

                  <div className="payment-method-main">
                    <strong>
                      {formatMethod(item.method)}
                    </strong>

                    <div className="payment-method-bar">
                      <span
                        style={{
                          width: `${Math.min(
                            Number(item.percentage || 0),
                            100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>

                  <div className="payment-method-value">
                    <strong>
                      {formatMoney(item.amount)}
                    </strong>

                    <span>
                      {Number(item.percentage || 0).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="retailer-empty-state">
              <Wallet size={24} />
              <span>No payments recorded yet.</span>
            </div>
          )}
        </div>

        <div className="retailer-panel retailer-stock-panel">
          <PanelHeader
            title="Low Stock Alerts"
            subtitle="Items at or below reorder level"
          />

          {data.low_stock_items.length > 0 ? (
            <div className="stock-list">
              {data.low_stock_items.map((item) => (
                <div
                  className="stock-row"
                  key={item.product_variant_id}
                >
                  <div className="stock-warning-icon">
                    <AlertTriangle size={15} />
                  </div>

                  <div className="stock-info">
                    <strong>{item.variant_name}</strong>
                    <span>{item.sku}</span>
                  </div>

                  <div className="stock-quantity">
                    <strong>{item.quantity_available}</strong>
                    <span>
                      available
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="retailer-empty-state">
              <Package size={24} />
              <span>All inventory levels look healthy.</span>
            </div>
          )}
        </div>

        <div className="retailer-panel retailer-list-panel">
          <PanelHeader
            title="Recent Invoices"
            subtitle="Latest billing activity"
          />

          {data.recent_invoices.length > 0 ? (
            <div className="retailer-list">
              {data.recent_invoices.map((invoice) => (
                <div
                  className="retailer-list-row"
                  key={invoice.invoice_id}
                >
                  <div className="retailer-list-avatar">
                    <FileText size={14} />
                  </div>

                  <div className="retailer-list-main">
                    <strong>
                      {invoice.invoice_number ||
                        invoice.invoice_id}
                    </strong>

                    <span>
                      {invoice.customer_id}
                    </span>
                  </div>

                  <div className="retailer-list-date">
                    {formatDate(invoice.invoice_date)}
                  </div>

                  <div className="retailer-list-amount">
                    <strong>
                      {formatMoney(invoice.total_amount)}
                    </strong>

                    <StatusBadge
                      status={invoice.payment_status}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="retailer-empty-state">
              <FileText size={24} />
              <span>No invoices yet.</span>
            </div>
          )}
        </div>

        <div className="retailer-panel retailer-list-panel">
          <PanelHeader
            title="Recent Payments"
            subtitle="Latest collections"
          />

          {data.recent_payments.length > 0 ? (
            <div className="retailer-list">
              {data.recent_payments.map((payment) => (
                <div
                  className="retailer-list-row"
                  key={payment.payment_id}
                >
                  <div className="retailer-list-avatar payment">
                    <Wallet size={14} />
                  </div>

                  <div className="retailer-list-main">
                    <strong>{payment.payment_id}</strong>

                    <span>
                      {formatMethod(payment.payment_method)}
                      {" · "}
                      {payment.invoice_id}
                    </span>
                  </div>

                  <div className="retailer-list-date">
                    {formatDate(payment.paid_at)}
                  </div>

                  <div className="retailer-list-amount">
                    <strong>
                      {formatMoney(payment.amount)}
                    </strong>

                    <StatusBadge
                      status={payment.payment_status}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="retailer-empty-state">
              <Wallet size={24} />
              <span>No payments yet.</span>
            </div>
          )}
        </div>

        <div className="retailer-panel retailer-summary-panel">
          <PanelHeader
            title="Business Snapshot"
            subtitle="Current invoice position"
          />

          <div className="snapshot-grid">
            <div>
              <span>Total invoices</span>
              <strong>{data.total_invoices}</strong>
            </div>

            <div>
              <span>Paid</span>
              <strong>{data.paid_invoices}</strong>
            </div>

            <div>
              <span>Partial</span>
              <strong>{data.partial_invoices}</strong>
            </div>

            <div>
              <span>Unpaid</span>
              <strong>{data.unpaid_invoices}</strong>
            </div>
          </div>

          <div className="snapshot-progress">
            <div
              className="snapshot-progress-paid"
              style={{
                width: `${
                  data.total_invoices > 0
                    ? (data.paid_invoices /
                        data.total_invoices) *
                      100
                    : 0
                }%`,
              }}
            />

            <div
              className="snapshot-progress-partial"
              style={{
                width: `${
                  data.total_invoices > 0
                    ? (data.partial_invoices /
                        data.total_invoices) *
                      100
                    : 0
                }%`,
              }}
            />

            <div
              className="snapshot-progress-unpaid"
              style={{
                width: `${
                  data.total_invoices > 0
                    ? (data.unpaid_invoices /
                        data.total_invoices) *
                      100
                    : 0
                }%`,
              }}
            />
          </div>

          <div className="snapshot-footer">
            <span>
              Outstanding
            </span>

            <strong>
              {formatMoney(data.outstanding_amount)}
            </strong>
          </div>
        </div>
      </div>
    </section>
  );
}
