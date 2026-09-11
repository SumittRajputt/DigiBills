import { useEffect, useState } from "react";
import { Eye, RefreshCw } from "lucide-react";
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

function statusClass(
  value: string | null | undefined,
  type: "payment" | "order"
) {
  const normalized = String(value ?? "unknown")
    .toLowerCase()
    .replace(/\s+/g, "_");

  return `customer-order-status customer-order-${type}-${normalized}`;
}

export default function CustomerOrders() {
  const navigate = useNavigate();

  const [orders, setOrders] = useState<CustomerOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
          : "Unable to load your orders."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadOrders();
  }, []);

  return (
    <section className="dashboard customer-orders-page">
      <div className="customer-orders-heading">
        <div>
          <span className="page-eyebrow">
            CUSTOMER ACCOUNT
          </span>

          <h1>My Orders</h1>

          <p>
            View your purchase records associated with your
            DigiBills account.
          </p>
        </div>

        <button
          className="secondary-button"
          type="button"
          onClick={loadOrders}
          disabled={loading}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      <div className="panel customer-orders-panel">
        <div className="customer-orders-panel-header">
          <div>
            <h2>Purchase Records</h2>
            <p>
              {orders.length}{" "}
              {orders.length === 1 ? "order" : "orders"} found
            </p>
          </div>
        </div>

        {loading ? (
          <div className="customer-orders-empty">
            Loading your orders...
          </div>
        ) : error ? (
          <div className="customer-orders-error">
            {error}
          </div>
        ) : orders.length === 0 ? (
          <div className="customer-orders-empty">
            <strong>No orders found.</strong>
            <span>
              Purchase records associated with your bills will
              appear here.
            </span>
          </div>
        ) : (
          <div className="customer-orders-table-wrap">
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
                {orders.map((order) => (
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
                        {statusLabel(
                          order.payment_status
                        )}
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
                        onClick={() =>
                          navigate(
                            `/customer/invoices/${encodeURIComponent(
                              order.invoice_id
                            )}`
                          )
                        }
                        title="View invoice"
                        aria-label="View invoice"
                      >
                        <Eye size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
