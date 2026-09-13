import { useEffect, useMemo, useState } from "react";
import {
  Eye,
  Package,
  Search,
  SlidersHorizontal,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api";

type CustomerOrder = {
  id: string;
  invoice_id: string;
  invoice_number: string | null;
  invoice_date: string | null;
  item_names: string[];
  total_amount: string | number;
  payment_status: string;
  status: string;
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

function statusLabel(value: string | null | undefined) {
  if (!value) return "—";

  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function normalizeStatus(value: string | null | undefined) {
  return String(value ?? "")
    .toLowerCase()
    .replace(/\s+/g, "_");
}

function statusClass(
  value: string | null | undefined,
  type: "payment" | "order"
) {
  return `customer-order-status customer-order-${type}-${normalizeStatus(
    value
  )}`;
}

export default function CustomerOrders() {
  const navigate = useNavigate();

  const [orders, setOrders] = useState<CustomerOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  async function loadOrders() {
    try {
      setLoading(true);
      setError("");

      const result = await apiFetch<CustomerOrder[]>(
        "/customer/invoices"
      );

      setOrders(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load your purchase records."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadOrders();
  }, []);

  const filteredOrders = useMemo(() => {
    const query = search.trim().toLowerCase();

    return orders.filter((order) => {
      const normalizedOrderStatus = normalizeStatus(order.status);
      const normalizedPaymentStatus = normalizeStatus(
        order.payment_status
      );

      const matchesStatus =
        statusFilter === "all" ||
        normalizedOrderStatus === statusFilter ||
        normalizedPaymentStatus === statusFilter;

      if (!matchesStatus) return false;

      if (!query) return true;

      const searchableText = [
        order.invoice_number,
        order.invoice_id,
        order.invoice_date,
        order.status,
        order.payment_status,
        ...(order.item_names ?? []),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return searchableText.includes(query);
    });
  }, [orders, search, statusFilter]);

  const completedOrders = orders.filter(
    (order) => normalizeStatus(order.status) === "completed"
  ).length;

  const pendingOrders = orders.filter(
    (order) => normalizeStatus(order.status) === "pending"
  ).length;

  const cancelledOrders = orders.filter((order) => {
    const status = normalizeStatus(order.status);
    return status === "cancelled" || status === "canceled";
  }).length;

  const totalSpent = orders.reduce(
    (sum, order) => sum + Number(order.total_amount ?? 0),
    0
  );

  function openOrder(order: CustomerOrder) {
    navigate(
      `/customer/orders/${encodeURIComponent(order.invoice_id)}`
    );
  }

  return (
    <section className="dashboard customer-orders-page">
      <div className="customer-orders-heading">
        <div>
          <h1>My Orders</h1>
        </div>
      </div>

      <div className="customer-orders-stats">
        <article className="customer-orders-stat-card">
          <div className="customer-orders-stat-icon">
            <Package size={20} />
          </div>
          <div>
            <span>Total Orders</span>
            <strong>{orders.length}</strong>
            <small>Purchase records</small>
          </div>
        </article>

        <article className="customer-orders-stat-card">
          <div className="customer-orders-stat-icon completed">
            <Package size={20} />
          </div>
          <div>
            <span>Completed</span>
            <strong>{completedOrders}</strong>
            <small>Completed purchases</small>
          </div>
        </article>

        <article className="customer-orders-stat-card">
          <div className="customer-orders-stat-icon pending">
            <Package size={20} />
          </div>
          <div>
            <span>Pending</span>
            <strong>{pendingOrders}</strong>
            <small>Pending purchases</small>
          </div>
        </article>

        <article className="customer-orders-stat-card">
          <div className="customer-orders-stat-icon spent">
            <Package size={20} />
          </div>
          <div>
            <span>Total Spent</span>
            <strong>{money(totalSpent)}</strong>
            <small>Across purchase records</small>
          </div>
        </article>
      </div>

      <div className="panel customer-orders-panel">
        <div className="customer-orders-panel-header">
          <div>
            <h2>Purchase Records</h2>
            <p>
              {filteredOrders.length}{" "}
              {filteredOrders.length === 1 ? "order" : "orders"} found
            </p>
          </div>
        </div>

        {loading ? (
          <div className="customer-orders-empty">
            Loading your purchase records...
          </div>
        ) : error ? (
          <div className="customer-orders-error">{error}</div>
        ) : orders.length === 0 ? (
          <div className="customer-orders-empty">
            <strong>No purchase records found.</strong>
            <span>
              Purchase records associated with your bills will appear
              here.
            </span>
          </div>
        ) : (
          <>
            <div className="customer-orders-mobile-controls">
              <label className="customer-orders-mobile-search">
                <Search size={17} />
                <input
                  type="search"
                  placeholder="Search orders..."
                  value={search}
                  onChange={(event) =>
                    setSearch(event.target.value)
                  }
                />
              </label>

              <label className="customer-orders-mobile-filter">
                <SlidersHorizontal size={17} />
                <select
                  value={statusFilter}
                  onChange={(event) =>
                    setStatusFilter(event.target.value)
                  }
                  aria-label="Filter orders by status"
                >
                  <option value="all">All Status</option>
                  <option value="completed">Completed</option>
                  <option value="pending">Pending</option>
                  <option value="cancelled">Cancelled</option>
                  <option value="unpaid">Unpaid</option>
                  <option value="partial">Partial</option>
                  <option value="paid">Paid</option>
                </select>
              </label>
            </div>

            <div className="customer-orders-mobile-list">
              {filteredOrders.map((order) => (
                <article
                  className="customer-order-mobile-card"
                  key={`mobile-${order.id}`}
                >
                  <div className="customer-order-mobile-top">
                    <div className="customer-order-mobile-id">
                      <div className="customer-order-mobile-icon">
                        <Package size={18} />
                      </div>
                      <div>
                        <span>ORDER</span>
                        <strong>
                          {order.invoice_number ||
                            order.invoice_id}
                        </strong>
                      </div>
                    </div>

                    <span
                      className={statusClass(
                        order.status,
                        "order"
                      )}
                    >
                      {statusLabel(order.status)}
                    </span>
                  </div>

                  <div className="customer-order-mobile-date">
                    {formatDate(order.invoice_date)}
                  </div>

                  <div className="customer-order-mobile-divider" />

                  <div className="customer-order-mobile-item">
                    <span>ITEMS</span>
                    <strong>
                      {order.item_names?.length
                        ? order.item_names.join(", ")
                        : "Purchase record"}
                    </strong>
                  </div>

                  <div className="customer-order-mobile-grid">
                    <div>
                      <span>AMOUNT</span>
                      <strong>{money(order.total_amount)}</strong>
                    </div>

                    <div>
                      <span>PAYMENT</span>
                      <span
                        className={statusClass(
                          order.payment_status,
                          "payment"
                        )}
                      >
                        {statusLabel(order.payment_status)}
                      </span>
                    </div>
                  </div>

                  <button
                    className="customer-orders-mobile-view-button"
                    type="button"
                    onClick={() => openOrder(order)}
                  >
                    <Eye size={16} />
                    View Order Details
                  </button>
                </article>
              ))}
            </div>

            <div className="customer-orders-table-wrap">
              <div className="customer-orders-desktop-controls">
                <label className="customer-orders-desktop-search">
                  <Search size={17} />
                  <input
                    type="search"
                    placeholder="Search orders..."
                    value={search}
                    onChange={(event) =>
                      setSearch(event.target.value)
                    }
                  />
                </label>

                <label className="customer-orders-desktop-filter">
                  <SlidersHorizontal size={17} />
                  <select
                    value={statusFilter}
                    onChange={(event) =>
                      setStatusFilter(event.target.value)
                    }
                    aria-label="Filter orders by status"
                  >
                    <option value="all">All Status</option>
                    <option value="completed">Completed</option>
                    <option value="pending">Pending</option>
                    <option value="cancelled">Cancelled</option>
                    <option value="unpaid">Unpaid</option>
                    <option value="partial">Partial</option>
                    <option value="paid">Paid</option>
                  </select>
                </label>
              </div>

              <table className="customer-orders-table">
                <thead>
                  <tr>
                    <th>ORDER</th>
                    <th>DATE</th>
                    <th>ITEMS</th>
                    <th>AMOUNT</th>
                    <th>PAYMENT</th>
                    <th>STATUS</th>
                    <th>ACTION</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredOrders.map((order) => (
                    <tr key={order.id}>
                      <td>
                        <strong>
                          {order.invoice_number ||
                            order.invoice_id}
                        </strong>
                      </td>

                      <td>{formatDate(order.invoice_date)}</td>

                      <td>
                        <span className="customer-orders-items">
                          {order.item_names?.length
                            ? order.item_names.join(", ")
                            : "Purchase record"}
                        </span>
                      </td>

                      <td>
                        <strong>
                          {money(order.total_amount)}
                        </strong>
                      </td>

                      <td>
                        <span
                          className={statusClass(
                            order.payment_status,
                            "payment"
                          )}
                        >
                          {statusLabel(order.payment_status)}
                        </span>
                      </td>

                      <td>
                        <span
                          className={statusClass(
                            order.status,
                            "order"
                          )}
                        >
                          {statusLabel(order.status)}
                        </span>
                      </td>

                      <td>
                        <button
                          className="customer-orders-view-button"
                          type="button"
                          onClick={() => openOrder(order)}
                          title="View order details"
                          aria-label="View order details"
                        >
                          <Eye size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
