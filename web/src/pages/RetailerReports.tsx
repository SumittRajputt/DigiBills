import {
  FileText,
  IndianRupee,
  RotateCcw,
  TrendingUp,
} from "lucide-react";
import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
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

type SalesTrend = {
  date: string;
  invoice_count: number;
  sales: string;
};

type PaymentMethod = {
  method: string;
  payment_count: number;
  amount: string;
};

type ReportsData = {
  total_sales: string;
  total_invoices: number;
  average_invoice_value: string;
  payments_collected: string;
  total_refunds: string;
  sales_returns: string;
  purchase_returns: string;
  sales_trend: SalesTrend[];
  payment_methods: PaymentMethod[];
};

function money(value: string | number) {
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
  return new Date(value).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
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

function EmptyState({ text }: { text: string }) {
  return (
    <div className="empty-state">
      <span>{text}</span>
    </div>
  );
}

export default function RetailerReports() {
  const [data, setData] = useState<ReportsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadReports() {
      try {
        setLoading(true);
        setError("");

        const result = await apiFetch<ReportsData>(
          "/reports"
        );

        setData(result);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load reports."
        );
      } finally {
        setLoading(false);
      }
    }

    loadReports();
  }, []);

  if (loading) {
    return (
      <section className="dashboard retailer-reports-page">
        <div className="reports-header">
          <div>
            <div className="page-eyebrow">
              <span>ANALYTICS</span>
            </div>
            <h1>Reports & Analytics</h1>
            <p>Loading your business reports...</p>
          </div>
        </div>
      </section>
    );
  }

  if (error || !data) {
    return (
      <section className="dashboard retailer-reports-page">
        <div className="reports-header">
          <div>
            <div className="page-eyebrow">
              <span>ANALYTICS</span>
            </div>
            <h1>Reports & Analytics</h1>
            <p className="negative">
              {error || "Report data unavailable."}
            </p>
          </div>
        </div>
      </section>
    );
  }

  const salesTrendData = data.sales_trend.map(
    (item) => ({
      date: formatDate(item.date),
      sales: Number(item.sales),
      invoices: item.invoice_count,
    })
  );

  const paymentData = data.payment_methods.map(
    (item) => ({
      name: item.method.toUpperCase(),
      amount: Number(item.amount),
    })
  );

  return (
    <section className="dashboard retailer-reports-page">
      <div className="reports-header">
        <div>
          <div className="page-eyebrow">
            <span>ANALYTICS</span>
          </div>

          <h1>Reports & Analytics</h1>

          <p>
            Your business performance and financial insights.
          </p>
        </div>
      </div>

      <div className="reports-kpi-grid">
        <Stat
          icon={<TrendingUp />}
          title="Total Sales"
          value={shortMoney(data.total_sales)}
          tone="blue"
        />

        <Stat
          icon={<FileText />}
          title="Total Invoices"
          value={data.total_invoices.toLocaleString(
            "en-IN"
          )}
          tone="purple"
        />

        <Stat
          icon={<IndianRupee />}
          title="Average Invoice"
          value={shortMoney(
            data.average_invoice_value
          )}
          tone="cyan"
        />

        <Stat
          icon={<IndianRupee />}
          title="Payments Collected"
          value={shortMoney(
            data.payments_collected
          )}
          tone="green"
        />

        <Stat
          icon={<RotateCcw />}
          title="Refunds"
          value={shortMoney(data.total_refunds)}
          tone="orange"
        />

        <Stat
          icon={<RotateCcw />}
          title="Sales Returns"
          value={shortMoney(data.sales_returns)}
          tone="red"
        />

        <Stat
          icon={<RotateCcw />}
          title="Purchase Returns"
          value={shortMoney(data.purchase_returns)}
          tone="red"
        />
      </div>

      <div className="reports-grid">
        <div className="panel reports-sales-panel">
          <div className="reports-panel-header">
            <div>
              <h3>Sales Trend</h3>
              <span>
                Revenue performance over time
              </span>
            </div>
          </div>

          {salesTrendData.length > 0 ? (
            <ResponsiveContainer
              width="100%"
              height={280}
            >
              <BarChart
                data={salesTrendData}
                className="reports-chart"
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                />

                <XAxis dataKey="date" />

                <YAxis
                  tickFormatter={(value) =>
                    `₹${Number(value).toLocaleString(
                      "en-IN"
                    )}`
                  }
                />

                <Tooltip
                  formatter={(value) =>
                    money(String(value))
                  }
                />

                <Bar
                  dataKey="sales"
                  fill="#1769ff"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState text="No sales trend data available." />
          )}
        </div>

        <div className="panel reports-payment-panel">
          <div className="reports-panel-header">
            <div>
              <h3>Payment Methods</h3>
              <span>
                Collection breakdown by method
              </span>
            </div>
          </div>

          {paymentData.length > 0 ? (
            <ResponsiveContainer
              width="100%"
              height={280}
            >
              <PieChart className="reports-chart">
                <Pie
                  data={paymentData}
                  dataKey="amount"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label
                >
                  {paymentData.map((_, index) => (
                    <Cell
                      key={index}
                      fill={
                        [
                          "#1769ff",
                          "#6f4fd8",
                          "#18a66d",
                          "#f59e0b",
                        ][index % 4]
                      }
                    />
                  ))}
                </Pie>

                <Tooltip
                  formatter={(value) =>
                    money(String(value))
                  }
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState text="No payment method data available." />
          )}
        </div>

        <div className="panel retailer-reports-summary-panel">
          <div className="reports-panel-header">
            <div>
              <h3>Financial Summary</h3>
              <span>
                Overview of your current financial activity
              </span>
            </div>
          </div>

          <div className="retailer-report-summary-list">
            <div>
              <span>Sales</span>
              <strong>{money(data.total_sales)}</strong>
            </div>

            <div>
              <span>Payments Collected</span>
              <strong>
                {money(data.payments_collected)}
              </strong>
            </div>

            <div>
              <span>Refunds</span>
              <strong>
                {money(data.total_refunds)}
              </strong>
            </div>

            <div>
              <span>Sales Returns</span>
              <strong>
                {money(data.sales_returns)}
              </strong>
            </div>

            <div>
              <span>Purchase Returns</span>
              <strong>
                {money(data.purchase_returns)}
              </strong>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
