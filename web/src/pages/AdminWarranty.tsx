import {
  Search,
  ShieldCheck,
  CheckCircle,
  XCircle,
  Clock,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../api";

type Warranty = {
  id: string;
  warranty_id: string;
  invoice_id: string;
  product_variant_id: string;
  customer_id: string;
  start_date: string;
  end_date: string;
  duration_months: number;
  is_transferable: boolean;
  status: string;
  created_at: string;
  updated_at: string;
};

export default function AdminWarranty() {
  const [warranties, setWarranties] = useState<Warranty[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedWarranty, setSelectedWarranty] =
    useState<Warranty | null>(null);

  async function loadWarranties() {
    try {
      setLoading(true);
      setError("");

      const result = await apiFetch<Warranty[]>(
        "/admin/warranties"
      );

      setWarranties(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load warranties."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadWarranties();
  }, []);

  const filteredWarranties = useMemo(() => {
    const query = search.toLowerCase().trim();

    return warranties.filter((item) => {
      const matchesSearch =
        !query ||
        item.warranty_id.toLowerCase().includes(query) ||
        item.invoice_id.toLowerCase().includes(query) ||
        item.product_variant_id
          .toLowerCase()
          .includes(query) ||
        item.customer_id.toLowerCase().includes(query);

      const matchesStatus =
        status === "all" ||
        item.status.toLowerCase() === status;

      return matchesSearch && matchesStatus;
    });
  }, [warranties, search, status]);

  const counts = {
    all: warranties.length,
    active: warranties.filter(
      (item) => item.status === "active"
    ).length,
    expired: warranties.filter(
      (item) => item.status === "expired"
    ).length,
    cancelled: warranties.filter(
      (item) => item.status === "cancelled"
    ).length,
  };

  function formatDate(value: string) {
    return new Date(value).toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  return (
    <section className="dashboard admin-warranty-page">
      <div className="admin-warranty-header">
        <div>
          <div className="page-eyebrow">
            <span>ADMINISTRATION</span>
          </div>
          <h1>Warranties</h1>
          <p>
            Monitor product warranties and coverage records across DigiBills.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={loadWarranties}
          disabled={loading}
        >
          Refresh
        </button>
      </div>

      <div className="warranty-stats-grid">
        <MiniStat
          icon={<ShieldCheck />}
          title="Total Warranties"
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
          icon={<Clock />}
          title="Expired"
          value={counts.expired}
          tone="orange"
        />

        <MiniStat
          icon={<XCircle />}
          title="Cancelled"
          value={counts.cancelled}
          tone="red"
        />
      </div>

      <div className="warranty-panel">
        <div className="warranty-panel-header">
          <div>
            <h3>All Warranties</h3>
            <span>
              {filteredWarranties.length} of {warranties.length} warranties
            </span>
          </div>

          <div className="warranty-toolbar">
            <div className="warranty-search">
              <Search size={16} />

              <input
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search warranties..."
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
              <option value="expired">Expired</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        {loading && (
          <div className="table-state">
            Loading warranties...
          </div>
        )}

        {!loading && error && (
          <div className="table-state negative">
            {error}
          </div>
        )}

        {!loading &&
          !error &&
          filteredWarranties.length === 0 && (
            <div className="table-state">
              No warranties found.
            </div>
          )}

        {!loading &&
          !error &&
          filteredWarranties.length > 0 && (
            <div className="warranty-table-wrap">
              <table className="warranty-table">
                <thead>
                  <tr>
                    <th>Warranty ID</th>
                    <th>Invoice</th>
                    <th>Customer</th>
                    <th>Duration</th>
                    <th>Transferable</th>
                    <th>Status</th>
                    <th>End Date</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredWarranties.map((item) => (
                    <tr
                      key={item.id}
                      onClick={() =>
                        setSelectedWarranty(item)
                      }
                      style={{
                        cursor: "pointer",
                      }}
                    >
                      <td>
                        <strong>
                          {item.warranty_id}
                        </strong>
                      </td>

                      <td>{item.invoice_id}</td>

                      <td>{item.customer_id}</td>

                      <td>
                        {item.duration_months} months
                      </td>

                      <td>
                        {item.is_transferable
                          ? "Yes"
                          : "No"}
                      </td>

                      <td>
                        <span
                          className={`status-badge ${item.status}`}
                        >
                          {item.status}
                        </span>
                      </td>

                      <td>
                        {formatDate(item.end_date)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </div>

      {selectedWarranty && (
        <div
          className="modal-backdrop"
          onClick={() =>
            setSelectedWarranty(null)
          }
        >
          <div
            className="warranty-details-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="modal-header">
              <div>
                <h2>Warranty Details</h2>
                <p>
                  Warranty information registered on
                  DigiBills.
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() =>
                  setSelectedWarranty(null)
                }
              >
                ×
              </button>
            </div>

            <div className="user-details-grid">
              <Detail
                label="Warranty ID"
                value={selectedWarranty.warranty_id}
              />

              <Detail
                label="Invoice ID"
                value={selectedWarranty.invoice_id}
              />

              <Detail
                label="Product Variant ID"
                value={selectedWarranty.product_variant_id}
              />

              <Detail
                label="Customer ID"
                value={selectedWarranty.customer_id}
              />

              <Detail
                label="Start Date"
                value={formatDate(
                  selectedWarranty.start_date
                )}
              />

              <Detail
                label="End Date"
                value={formatDate(
                  selectedWarranty.end_date
                )}
              />

              <Detail
                label="Duration"
                value={`${selectedWarranty.duration_months} months`}
              />

              <Detail
                label="Transferable"
                value={
                  selectedWarranty.is_transferable
                    ? "Yes"
                    : "No"
                }
              />

              <Detail
                label="Status"
                value={selectedWarranty.status}
              />

              <Detail
                label="Created"
                value={formatDate(
                  selectedWarranty.created_at
                )}
              />
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function Detail({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
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
