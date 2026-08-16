import {
  Activity,
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

const paymentColors = ["#1769ff", "#6f4fd8", "#18a66d", "#9ca8ba"];

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

  return money(value);
}

function formatDate(value: string) {
  const date = new Date(value);

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
  });
}

function formatActivityTime(value: string) {
  const date = new Date(value);

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function Stat({
  icon,
  title,
  value,
  tone = "blue",
}: {
  icon: React.ReactNode;
  title: string;
  value: string;
  tone?: string;
}) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${tone}`}>{icon}</div>

      <div>
        <span>{title}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const [data, setData] = useState<AdminDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        setError("");

        const result = await apiFetch<AdminDashboardData>(
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
      <section className="dashboard">
        <div className="welcome-row">
          <div>
            <h1>Welcome back, Super Admin! 👋</h1>
            <p>Loading your dashboard...</p>
          </div>
        </div>
      </section>
    );
  }

  if (error || !data) {
    return (
      <section className="dashboard">
        <div className="welcome-row">
          <div>
            <h1>Welcome back, Super Admin! 👋</h1>
            <p className="negative">
              {error || "Dashboard data unavailable."}
            </p>
          </div>
        </div>
      </section>
    );
  }

  const salesData = data.sales_overview.map((item) => ({
    date: formatDate(item.date),
    sales: Number(item.amount),
  }));

  const paymentData = data.payment_methods.map((item) => ({
    name: item.method,
    value: Number(item.percentage),
  }));

  const maxRetailerSales = Math.max(
    ...data.top_retailers.map((item) => Number(item.sales)),
    1
  );

  return (
    <section className="dashboard">
      <div className="welcome-row">
        <div>
          <h1>Welcome back, Super Admin! 👋</h1>
          <p>Here's what's happening across DigiBills.</p>
        </div>

        <button className="date-filter">
          ▣ All Time⌄
        </button>
      </div>

      <div className="stats-grid six">
        <Stat
          icon={<Store />}
          title="Total Retailers"
          value={data.total_retailers.toLocaleString("en-IN")}
          tone="blue"
        />

        <Stat
          icon={<Users />}
          title="Active Retailers"
          value={data.active_retailers.toLocaleString("en-IN")}
          tone="green"
        />

        <Stat
          icon={<ClipboardCheck />}
          title="Pending Approvals"
          value={data.pending_approvals.toLocaleString("en-IN")}
          tone="orange"
        />

        <Stat
          icon={<Users />}
          title="Total Customers"
          value={data.total_customers.toLocaleString("en-IN")}
          tone="purple"
        />

        <Stat
          icon={<FileText />}
          title="Total Invoices"
          value={data.total_invoices.toLocaleString("en-IN")}
          tone="purple"
        />

        <Stat
          icon={<BarChart3 />}
          title="Total Sales"
          value={shortMoney(data.total_sales)}
          tone="cyan"
        />
      </div>

      <div className="stats-grid four">
        <Stat
          icon={<BadgeIndianRupee />}
          title="Payments Collected"
          value={shortMoney(data.payments_collected)}
          tone="blue"
        />

        <Stat
          icon={<BadgeIndianRupee />}
          title="Refunds"
          value={shortMoney(data.refunds)}
          tone="purple"
        />

        <Stat
          icon={<RotateCcw />}
          title="Returns"
          value={shortMoney(data.returns)}
          tone="red"
        />

        <Stat
          icon={<BadgeIndianRupee />}
          title="Outstanding Amount"
          value={shortMoney(data.outstanding_amount)}
          tone="orange"
        />
      </div>

      <div className="panel-grid admin-grid">
        <div className="panel chart-panel">
          <PanelHeader title="Sales Overview" />

          {salesData.length > 0 ? (
            <ResponsiveContainer width="100%" height={230}>
              <AreaChart data={salesData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                />

                <XAxis dataKey="date" />

                <YAxis
                  tickFormatter={(value) =>
                    `₹${Number(value).toLocaleString("en-IN")}`
                  }
                />

                <Tooltip
                  formatter={(value) => money(String(value))}
                />

                <Area
                  type="monotone"
                  dataKey="sales"
                  stroke="#1769ff"
                  fill="#eaf2ff"
                  strokeWidth={3}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState text="No sales data available." />
          )}
        </div>

        <div className="panel">
          <PanelHeader title="Sales by Top Retailers" />

          {data.top_retailers.length > 0 ? (
            <div className="rank-list">
              {data.top_retailers.map((retailer, index) => {
                const sales = Number(retailer.sales);

                return (
                  <div
                    className="rank"
                    key={retailer.business_name}
                  >
                    <b>{index + 1}</b>

                    <div className="rank-body">
                      <span>{retailer.business_name}</span>

                      <div className="progress">
                        <i
                          style={{
                            width: `${Math.max(
                              5,
                              (sales / maxRetailerSales) * 100
                            )}%`,
                          }}
                        />
                      </div>
                    </div>

                    <strong>
                      {shortMoney(retailer.sales)}
                    </strong>
                  </div>
                );
              })}
            </div>
          ) : (
            <EmptyState text="No retailer sales data available." />
          )}
        </div>

        <div className="panel donut-panel">
          <PanelHeader title="Payment Methods" />

          {paymentData.length > 0 ? (
            <div className="donut-wrap">
              <ResponsiveContainer
                width="52%"
                height={190}
              >
                <PieChart>
                  <Pie
                    data={paymentData}
                    dataKey="value"
                    innerRadius={55}
                    outerRadius={82}
                    paddingAngle={2}
                  >
                    {paymentData.map((_, index) => (
                      <Cell
                        key={index}
                        fill={
                          paymentColors[
                            index % paymentColors.length
                          ]
                        }
                      />
                    ))}
                  </Pie>

                  <Tooltip
                    formatter={(value) =>
                      `${Number(value).toFixed(2)}%`
                    }
                  />
                </PieChart>
              </ResponsiveContainer>

              <div className="legend">
                {data.payment_methods.map(
                  (payment, index) => (
                    <div key={payment.method}>
                      <i
                        style={{
                          background:
                            paymentColors[
                              index % paymentColors.length
                            ],
                        }}
                      />

                      <span>
                        {payment.method}
                      </span>

                      <b>
                        {Number(
                          payment.percentage
                        ).toFixed(2)}
                        %
                      </b>
                    </div>
                  )
                )}
              </div>
            </div>
          ) : (
            <EmptyState text="No payment data available." />
          )}
        </div>

        <div className="panel activity">
          <PanelHeader title="Recent Activity" />

          {data.recent_activity.length > 0 ? (
            data.recent_activity.map(
              (activity, index) => (
                <div
                  className="activity-row"
                  key={`${activity.created_at}-${index}`}
                >
                  <span
                    className={`activity-dot a${
                      index % 5
                    }`}
                  >
                    <Activity size={13} />
                  </span>

                  <div>
                    <b>
                      {activity.description ||
                        activity.action}
                    </b>

                    <small>
                      {formatActivityTime(
                        activity.created_at
                      )}
                    </small>
                  </div>
                </div>
              )
            )
          ) : (
            <EmptyState text="No recent activity." />
          )}
        </div>
      </div>
    </section>
  );
}

function PanelHeader({
  title,
}: {
  title: string;
}) {
  return (
    <div className="panel-header">
      <h3>{title}</h3>
      <button>All Time⌄</button>
    </div>
  );
}

function EmptyState({
  text,
}: {
  text: string;
}) {
  return (
    <div className="empty-state">
      <span>{text}</span>
    </div>
  );
}
