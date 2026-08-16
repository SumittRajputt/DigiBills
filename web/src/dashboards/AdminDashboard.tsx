import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BadgeIndianRupee,
  BarChart3,
  ClipboardCheck,
  FileText,
  RotateCcw,
  Store,
  Users,
} from "lucide-react";
import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { apiFetch } from "../api";

type SalesOverviewItem = {
  date: string;
  amount: string;
};

type TopRetailerItem = {
  business_name: string;
  sales: string;
};

type PaymentMethodItem = {
  method: string;
  amount: string;
  percentage: string;
};

type RecentActivityItem = {
  action: string;
  entity_type: string;
  description: string | null;
  created_at: string;
};

type AdminDashboardData = {
  total_retailers: number;
  active_retailers: number;
  pending_approvals: number;
  total_customers: number;
  total_invoices: number;
  total_sales: string;
  payments_collected: string;
  refunds: string;
  returns: string;
  outstanding_amount: string;
  sales_overview: SalesOverviewItem[];
  top_retailers: TopRetailerItem[];
  payment_methods: PaymentMethodItem[];
  recent_activity: RecentActivityItem[];
};

const paymentColors = [
  "#1769ff",
  "#7352d6",
  "#12a878",
  "#e89413",
];

function money(value: string) {
  return `₹${Number(value).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function shortMoney(value: string) {
  const amount = Number(value);

  if (amount >= 10000000) {
    return `₹${(amount / 10000000).toFixed(2)} Cr`;
  }

  if (amount >= 100000) {
    return `₹${(amount / 100000).toFixed(2)} L`;
  }

  if (amount >= 1000) {
    return `₹${(amount / 1000).toFixed(1)} K`;
  }

  return money(value);
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
  });
}

function formatActivityTime(value: string) {
  return new Date(value).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function StatCard({
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
    <div className="admin-kpi">
      <div className="admin-kpi-top">
        <div className={`admin-kpi-icon ${tone}`}>
          {icon}
        </div>

        <span className="admin-kpi-menu">•••</span>
      </div>

      <div className="admin-kpi-title">{title}</div>

      <div className="admin-kpi-value">{value}</div>

      <div className="admin-kpi-subtitle">
        {subtitle}
      </div>
    </div>
  );
}

function SectionHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: string;
}) {
  return (
    <div className="admin-section-header">
      <div>
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </div>

      {action && (
        <button className="admin-text-button">
          {action}
        </button>
      )}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="admin-empty-state">
      {text}
    </div>
  );
}

export default function AdminDashboard() {
  const [data, setData] =
    useState<AdminDashboardData | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        setError("");

        const result =
          await apiFetch<AdminDashboardData>(
            "/admin/dashboard"
          );

        setData(result);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load dashboard."
        );
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  if (loading) {
    return (
      <section className="admin-dashboard">
        <div className="admin-loading">
          <div className="admin-loading-bar large" />
          <div className="admin-loading-bar" />
          <div className="admin-loading-grid">
            <div />
            <div />
            <div />
            <div />
          </div>
        </div>
      </section>
    );
  }

  if (error || !data) {
    return (
      <section className="admin-dashboard">
        <div className="admin-error">
          <div className="admin-error-icon">!</div>
          <div>
            <h2>Unable to load dashboard</h2>
            <p>{error || "Dashboard data unavailable."}</p>
          </div>
        </div>
      </section>
    );
  }

  const salesData = data.sales_overview.map(
    (item) => ({
      date: formatDate(item.date),
      sales: Number(item.amount),
    })
  );

  const paymentData = data.payment_methods.map(
    (item) => ({
      name: item.method,
      value: Number(item.percentage),
    })
  );

  const maxRetailerSales = Math.max(
    ...data.top_retailers.map(
      (item) => Number(item.sales)
    ),
    1
  );

  const activeRate =
    data.total_retailers > 0
      ? Math.round(
          (data.active_retailers /
            data.total_retailers) *
            100
        )
      : 0;

  return (
    <section className="admin-dashboard">

      {/* PAGE HEADER */}
      <div className="admin-page-header">
        <div>
          <div className="admin-eyebrow">
            PLATFORM OVERVIEW
          </div>

          <h1>Dashboard</h1>

          <p>
            Monitor your DigiBills business performance,
            payments and platform activity.
          </p>
        </div>

        <div className="admin-header-actions">
          <button className="admin-filter-button">
            <span>Period</span>
            <strong>All time</strong>
            <span>⌄</span>
          </button>

          <button className="admin-export-button">
            Export report
          </button>
        </div>
      </div>

      {/* KPI ROW */}
      <div className="admin-kpi-grid">

        <StatCard
          icon={<BadgeIndianRupee />}
          title="Total Revenue"
          value={shortMoney(data.total_sales)}
          subtitle="Gross sales generated"
          tone="blue"
        />

        <StatCard
          icon={<BadgeIndianRupee />}
          title="Payments Collected"
          value={shortMoney(
            data.payments_collected
          )}
          subtitle="Successfully collected"
          tone="green"
        />

        <StatCard
          icon={<BadgeIndianRupee />}
          title="Outstanding"
          value={shortMoney(
            data.outstanding_amount
          )}
          subtitle="Awaiting payment"
          tone="orange"
        />

        <StatCard
          icon={<FileText />}
          title="Total Invoices"
          value={data.total_invoices.toLocaleString(
            "en-IN"
          )}
          subtitle="Invoices generated"
          tone="purple"
        />

      </div>

      {/* SECONDARY METRICS */}
      <div className="admin-secondary-metrics">

        <div className="admin-secondary-item">
          <span>Total retailers</span>
          <strong>
            {data.total_retailers}
          </strong>
        </div>

        <div className="admin-secondary-item">
          <span>Active retailers</span>
          <strong>
            {data.active_retailers}
          </strong>
        </div>

        <div className="admin-secondary-item">
          <span>Customers</span>
          <strong>
            {data.total_customers}
          </strong>
        </div>

        <div className="admin-secondary-item">
          <span>Pending approvals</span>
          <strong>
            {data.pending_approvals}
          </strong>
        </div>

        <div className="admin-secondary-item">
          <span>Refunds</span>
          <strong>
            {shortMoney(data.refunds)}
          </strong>
        </div>

        <div className="admin-secondary-item">
          <span>Returns</span>
          <strong>
            {shortMoney(data.returns)}
          </strong>
        </div>

      </div>

      {/* ANALYTICS */}
      <div className="admin-main-grid">

        {/* REVENUE */}
        <div className="admin-panel admin-revenue-panel">

          <SectionHeader
            title="Revenue overview"
            subtitle="Sales performance over time"
            action="View report →"
          />

          <div className="admin-chart-summary">
            <strong>
              {shortMoney(data.total_sales)}
            </strong>

            <span>
              Total revenue
            </span>
          </div>

          {salesData.length > 0 ? (
            <div className="admin-chart">
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <AreaChart
                  data={salesData}
                  margin={{
                    top: 10,
                    right: 10,
                    left: 8,
                    bottom: 0,
                  }}
                >
                  <defs>
                    <linearGradient
                      id="adminRevenueGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="0%"
                        stopColor="#1769ff"
                        stopOpacity={0.22}
                      />

                      <stop
                        offset="100%"
                        stopColor="#1769ff"
                        stopOpacity={0}
                      />
                    </linearGradient>
                  </defs>

                  <CartesianGrid
                    stroke="#edf1f6"
                    vertical={false}
                    strokeDasharray="4 4"
                  />

                  <XAxis
                    dataKey="date"
                    axisLine={false}
                    tickLine={false}
                    tick={{
                      fontSize: 10,
                      fill: "#8994a5",
                    }}
                    dy={8}
                  />

                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    width={48}
                    tick={{
                      fontSize: 9,
                      fill: "#8994a5",
                    }}
                    tickFormatter={(value) =>
                      shortMoney(String(value))
                    }
                  />

                  <Tooltip
                    contentStyle={{
                      border: "1px solid #e5eaf1",
                      borderRadius: 10,
                      boxShadow:
                        "0 10px 30px rgba(15,35,65,.10)",
                      fontSize: 11,
                    }}
                    formatter={(value) =>
                      money(String(value))
                    }
                    labelStyle={{
                      color: "#172033",
                      fontWeight: 600,
                    }}
                  />

                  <Area
                    type="monotone"
                    dataKey="sales"
                    stroke="#1769ff"
                    fill="url(#adminRevenueGradient)"
                    strokeWidth={2.5}
                    dot={false}
                    activeDot={{
                      r: 5,
                      strokeWidth: 3,
                      stroke: "#fff",
                      fill: "#1769ff",
                    }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState text="No sales data available." />
          )}
        </div>

        {/* PAYMENT METHODS */}
        <div className="admin-panel admin-payment-panel">

          <SectionHeader
            title="Payment methods"
            subtitle="Collection distribution"
          />

          {paymentData.length > 0 ? (
            <>
              <div className="admin-donut">

                <ResponsiveContainer
                  width="100%"
                  height={210}
                >
                  <PieChart>
                    <Pie
                      data={paymentData}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={62}
                      outerRadius={84}
                      paddingAngle={3}
                      stroke="#fff"
                      strokeWidth={3}
                    >
                      {paymentData.map(
                        (_, index) => (
                          <Cell
                            key={index}
                            fill={
                              paymentColors[
                                index %
                                  paymentColors.length
                              ]
                            }
                          />
                        )
                      )}
                    </Pie>

                    <Tooltip
                      contentStyle={{
                        border:
                          "1px solid #e5eaf1",
                        borderRadius: 10,
                        fontSize: 11,
                      }}
                      formatter={(value) =>
                        `${Number(value).toFixed(
                          2
                        )}%`
                      }
                    />
                  </PieChart>
                </ResponsiveContainer>

                <div className="admin-donut-center">
                  <strong>100%</strong>
                  <span>Payments</span>
                </div>

              </div>

              <div className="admin-payment-list">
                {data.payment_methods.map(
                  (payment, index) => (
                    <div
                      className="admin-payment-row"
                      key={payment.method}
                    >
                      <span
                        className="admin-payment-dot"
                        style={{
                          background:
                            paymentColors[
                              index %
                                paymentColors.length
                            ],
                        }}
                      />

                      <span>
                        {payment.method}
                      </span>

                      <strong>
                        {Number(
                          payment.percentage
                        ).toFixed(1)}
                        %
                      </strong>
                    </div>
                  )
                )}
              </div>
            </>
          ) : (
            <EmptyState text="No payment data available." />
          )}
        </div>

      </div>

      {/* LOWER GRID */}
      <div className="admin-lower-grid">

        {/* RETAILERS */}
        <div className="admin-panel">

          <SectionHeader
            title="Top retailers"
            subtitle="Highest revenue contributors"
            action="View all →"
          />

          {data.top_retailers.length > 0 ? (
            <div className="admin-retailer-table">

              <div className="admin-table-head">
                <span>#</span>
                <span>Retailer</span>
                <span>Revenue</span>
                <span>Status</span>
              </div>

              {data.top_retailers.map(
                (retailer, index) => {
                  const sales = Number(
                    retailer.sales
                  );

                  const percentage =
                    Math.max(
                      5,
                      (sales /
                        maxRetailerSales) *
                        100
                    );

                  return (
                    <div
                      className="admin-retailer-row"
                      key={retailer.business_name}
                    >
                      <span className="admin-rank">
                        {index + 1}
                      </span>

                      <div className="admin-retailer-name">
                        <strong>
                          {retailer.business_name}
                        </strong>

                        <div className="admin-progress">
                          <i
                            style={{
                              width: `${percentage}%`,
                            }}
                          />
                        </div>
                      </div>

                      <strong>
                        {shortMoney(
                          retailer.sales
                        )}
                      </strong>

                      <span className="admin-status">
                        Active
                      </span>
                    </div>
                  );
                }
              )}

            </div>
          ) : (
            <EmptyState text="No retailer sales data available." />
          )}
        </div>

        {/* PLATFORM HEALTH */}
        <div className="admin-panel">

          <SectionHeader
            title="Platform health"
            subtitle="Current business status"
          />

          <div className="admin-health">

            <div className="admin-health-row">
              <div className="admin-health-icon blue">
                <Store size={16} />
              </div>

              <div>
                <strong>
                  Retailer activity
                </strong>

                <span>
                  {activeRate}% of retailers active
                </span>
              </div>

              <b className="admin-health-good">
                Healthy
              </b>
            </div>

            <div className="admin-health-row">
              <div className="admin-health-icon purple">
                <Users size={16} />
              </div>

              <div>
                <strong>
                  Customer base
                </strong>

                <span>
                  {data.total_customers} registered
                  customers
                </span>
              </div>

              <b className="admin-health-good">
                Active
              </b>
            </div>

            <div className="admin-health-row">
              <div className="admin-health-icon orange">
                <ClipboardCheck size={16} />
              </div>

              <div>
                <strong>
                  Pending approvals
                </strong>

                <span>
                  {data.pending_approvals} awaiting
                  review
                </span>
              </div>

              <b
                className={
                  data.pending_approvals > 0
                    ? "admin-health-warning"
                    : "admin-health-good"
                }
              >
                {data.pending_approvals > 0
                  ? "Review"
                  : "Clear"}
              </b>
            </div>

            <div className="admin-health-row">
              <div className="admin-health-icon red">
                <RotateCcw size={16} />
              </div>

              <div>
                <strong>
                  Returns & refunds
                </strong>

                <span>
                  {shortMoney(data.returns)} returns
                  · {shortMoney(data.refunds)} refunds
                </span>
              </div>

              <b className="admin-health-neutral">
                Monitor
              </b>
            </div>

          </div>
        </div>

      </div>

      {/* ACTIVITY */}
      <div className="admin-panel admin-activity-panel">

        <SectionHeader
          title="Recent activity"
          subtitle="Latest actions across DigiBills"
          action="View audit logs →"
        />

        {data.recent_activity.length > 0 ? (
          <div className="admin-activity-list">

            {data.recent_activity
              .slice(0, 8)
              .map((activity, index) => (
                <div
                  className="admin-activity-row"
                  key={`${activity.created_at}-${index}`}
                >
                  <div
                    className={`admin-activity-icon activity-${index % 4}`}
                  >
                    <Activity size={14} />
                  </div>

                  <div className="admin-activity-content">
                    <strong>
                      {activity.description ||
                        activity.action}
                    </strong>

                    <span>
                      {activity.entity_type.replace(
                        /_/g,
                        " "
                      )}
                    </span>
                  </div>

                  <time>
                    {formatActivityTime(
                      activity.created_at
                    )}
                  </time>
                </div>
              ))}

          </div>
        ) : (
          <EmptyState text="No recent activity." />
        )}

      </div>

    </section>
  );
}
