import {
  Search,
  Users,
  CheckCircle,
  XCircle,
  RefreshCw,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../api";

type Customer = {
  id: string;
  customer_id: string;
  user_id: string;
  full_name: string;
  phone_number: string;
  email: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export default function RetailerCustomers() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedCustomer, setSelectedCustomer] =
    useState<Customer | null>(null);

  async function loadCustomers() {
    try {
      setLoading(true);
      setError("");

      const result =
        await apiFetch<Customer[]>("/customers");

      setCustomers(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load customers."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCustomers();
  }, []);

  const filteredCustomers = useMemo(() => {
    const query = search.toLowerCase().trim();

    return customers.filter((customer) => {
      const matchesSearch =
        !query ||
        customer.full_name
          .toLowerCase()
          .includes(query) ||
        customer.customer_id
          .toLowerCase()
          .includes(query) ||
        customer.phone_number.includes(query) ||
        (customer.email || "")
          .toLowerCase()
          .includes(query);

      const matchesStatus =
        status === "all" ||
        customer.status.toLowerCase() === status;

      return matchesSearch && matchesStatus;
    });
  }, [customers, search, status]);

  const activeCount = customers.filter(
    (customer) => customer.status.toLowerCase() === "active"
  ).length;

  const inactiveCount = customers.filter(
    (customer) => customer.status.toLowerCase() === "inactive"
  ).length;

  function formatDate(value: string) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "—";
    }

    return date.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  return (
    <section className="dashboard admin-customers-page">
      <div className="admin-customers-header">
        <div>
          <div className="page-eyebrow">
            <span>RETAILER MANAGEMENT</span>
          </div>

          <h1>Customers</h1>

          <p>
            Manage customers registered with your
            DigiBills retailer account.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={loadCustomers}
          disabled={loading}
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      <div className="customer-stats-grid">
        <MiniStat
          icon={<Users />}
          title="Total Customers"
          value={customers.length}
          tone="blue"
        />

        <MiniStat
          icon={<CheckCircle />}
          title="Active"
          value={activeCount}
          tone="green"
        />

        <MiniStat
          icon={<XCircle />}
          title="Inactive"
          value={inactiveCount}
          tone="red"
        />
      </div>

      <div className="customers-panel">
        <div className="customers-panel-header">
          <div>
            <h3>All Customers</h3>

            <span>
              {filteredCustomers.length} of{" "}
              {customers.length} customers
            </span>
          </div>

          <div className="customers-toolbar">
            <div className="customers-search">
              <Search size={16} />

              <input
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search customers..."
              />
            </div>

            <select
              value={status}
              onChange={(event) =>
                setStatus(event.target.value)
              }
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </div>

        {loading && (
          <div className="table-state">
            Loading customers...
          </div>
        )}

        {!loading && error && (
          <div className="table-state negative">
            {error}
          </div>
        )}

        {!loading &&
          !error &&
          filteredCustomers.length === 0 && (
            <div className="table-state">
              No customers found.
            </div>
          )}

        {!loading &&
          !error &&
          filteredCustomers.length > 0 && (
            <div className="customers-table-wrap">
              <table className="customers-table">
                <thead>
                  <tr>
                    <th>Customer</th>
                    <th>Customer ID</th>
                    <th>Contact</th>
                    <th>Status</th>
                    <th>Created</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredCustomers.map((customer) => (
                    <tr
                      key={customer.id}
                      onClick={() =>
                        setSelectedCustomer(customer)
                      }
                    >
                      <td>
                        <div className="customer-cell">
                          <div className="customer-avatar">
                            {customer.full_name
                              .charAt(0)
                              .toUpperCase()}
                          </div>

                          <div>
                            <strong>
                              {customer.full_name}
                            </strong>

                            <small>
                              {customer.email || "No email"}
                            </small>
                          </div>
                        </div>
                      </td>

                      <td>
                        {customer.customer_id}
                      </td>

                      <td>
                        <div>
                          <strong>
                            {customer.phone_number}
                          </strong>
                        </div>
                      </td>

                      <td>
                        <span
                          className={`status-badge ${customer.status}`}
                        >
                          {customer.status}
                        </span>
                      </td>

                      <td>
                        {formatDate(customer.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </div>

      {selectedCustomer && (
        <div
          className="modal-backdrop"
          onClick={() =>
            setSelectedCustomer(null)
          }
        >
          <div
            className="user-details-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="modal-header">
              <div>
                <h2>Customer Details</h2>
                <p>
                  {selectedCustomer.customer_id}
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() =>
                  setSelectedCustomer(null)
                }
              >
                <X size={17} />
              </button>
            </div>

            <div className="user-details-grid">
              <div className="detail">
                <span className="detail-label">
                  Customer
                </span>
                <span className="detail-value">
                  {selectedCustomer.full_name}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Customer ID
                </span>
                <span className="detail-value">
                  {selectedCustomer.customer_id}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Phone
                </span>
                <span className="detail-value">
                  {selectedCustomer.phone_number}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Email
                </span>
                <span className="detail-value">
                  {selectedCustomer.email || "—"}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Status
                </span>
                <span className="detail-value">
                  {selectedCustomer.status}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Created
                </span>
                <span className="detail-value">
                  {formatDate(
                    selectedCustomer.created_at
                  )}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function MiniStat({
  icon,
  title,
  value,
  tone,
}: {
  icon: React.ReactNode;
  title: string;
  value: string | number;
  tone: "blue" | "green" | "red";
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
