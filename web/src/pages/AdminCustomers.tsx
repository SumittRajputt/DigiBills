import { Search, Users, CheckCircle, XCircle } from "lucide-react";
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

export default function AdminCustomers() {
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

      const result = await apiFetch<Customer[]>("/customers");
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

  const counts = {
    all: customers.length,
    active: customers.filter(
      (customer) => customer.status === "active"
    ).length,
    inactive: customers.filter(
      (customer) => customer.status === "inactive"
    ).length,
  };

  function formatDate(value: string) {
    return new Date(value).toLocaleDateString(
      "en-IN",
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
      }
    );
  }

  return (
    <section className="dashboard">
      <div className="welcome-row">
        <div>
          <h1>Customers</h1>
          <p>
            Manage all customers registered on DigiBills.
          </p>
        </div>
      </div>

      <div className="stats-grid three">
        <MiniStat
          icon={<Users />}
          title="Total Customers"
          value={counts.all}
          tone="blue"
        />

        <MiniStat
          icon={<CheckCircle />}
          title="Active"
          value={counts.active}
          tone="green"
        />

        <MiniStat
          icon={<XCircle />}
          title="Inactive"
          value={counts.inactive}
          tone="red"
        />
      </div>

      <div className="panel retailer-table-panel">
        <div className="table-toolbar">
          <div>
            <h3>All Customers</h3>
            <span>
              {filteredCustomers.length} customers
            </span>
          </div>

          <div className="table-controls">
            <div className="table-search">
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
            <div className="table-scroll">
              <table className="data-table">
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
                  {filteredCustomers.map(
                    (customer) => (
                      <tr
                        key={customer.id}
                        onClick={() =>
                          setSelectedCustomer(
                            customer
                          )
                        }
                        style={{
                          cursor: "pointer",
                        }}
                      >
                        <td>
                          <div className="retailer-cell">
                            <div className="retailer-avatar">
                              {customer.full_name
                                .charAt(0)
                                .toUpperCase()}
                            </div>

                            <div>
                              <strong>
                                {customer.full_name}
                              </strong>

                              <small>
                                {customer.user_id}
                              </small>
                            </div>
                          </div>
                        </td>

                        <td>
                          {customer.customer_id}
                        </td>

                        <td>
                          <div className="contact-cell">
                            <span>
                              {customer.phone_number}
                            </span>

                            {customer.email && (
                              <small>
                                {customer.email}
                              </small>
                            )}
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
                          {formatDate(
                            customer.created_at
                          )}
                        </td>
                      </tr>
                    )
                  )}
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
                  Customer information registered
                  on DigiBills.
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() =>
                  setSelectedCustomer(null)
                }
              >
                ×
              </button>
            </div>

            <div className="user-details-grid">
              <div>
                <span>Name</span>
                <strong>
                  {selectedCustomer.full_name}
                </strong>
              </div>

              <div>
                <span>Customer ID</span>
                <strong>
                  {selectedCustomer.customer_id}
                </strong>
              </div>

              <div>
                <span>Phone</span>
                <strong>
                  {selectedCustomer.phone_number}
                </strong>
              </div>

              <div>
                <span>Email</span>
                <strong>
                  {selectedCustomer.email ||
                    "No email"}
                </strong>
              </div>

              <div>
                <span>Status</span>
                <strong>
                  {selectedCustomer.status}
                </strong>
              </div>

              <div>
                <span>Created</span>
                <strong>
                  {formatDate(
                    selectedCustomer.created_at
                  )}
                </strong>
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
  value: number;
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
