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

function formatDate(value: string) {
  if (!value) return "—";

  return new Date(value).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function statusLabel(status: string) {
  return status
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function Detail({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="warranty-detail-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default function RetailerWarranty() {
  const [warranties, setWarranties] = useState<Warranty[]>([]);
  const [selectedWarranty, setSelectedWarranty] =
    useState<Warranty | null>(null);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  async function loadWarranties() {
    try {
      setLoading(true);
      setError("");

      const result = await apiFetch<Warranty[]>(
        "/warranties"
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
    const query = search.trim().toLowerCase();

    return warranties.filter((item) => {
      const matchesSearch =
        !query ||
        item.warranty_id.toLowerCase().includes(query) ||
        item.invoice_id.toLowerCase().includes(query) ||
        item.customer_id.toLowerCase().includes(query) ||
        item.product_variant_id
          .toLowerCase()
          .includes(query);

      const matchesStatus =
        statusFilter === "all" ||
        item.status.toLowerCase() === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [warranties, search, statusFilter]);

  const counts = useMemo(
    () => ({
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
    }),
    [warranties]
  );


  return (
    <section className="dashboard retailer-warranty-page">
      <div className="page-heading">
        <span className="page-eyebrow">
          RETAILER MANAGEMENT
        </span>

        <h1>Warranty</h1>

        <p>
          Manage product warranty coverage and customer
          warranty records.
        </p>
      </div>

      <div className="warranty-stats-grid">
        <button
          type="button"
          className={`warranty-stat-card ${
            statusFilter === "all" ? "selected" : ""
          }`}
          onClick={() => setStatusFilter("all")}
        >
          <span>Total Warranties</span>
          <strong>{counts.all}</strong>
        </button>

        <button
          type="button"
          className={`warranty-stat-card ${
            statusFilter === "active" ? "selected" : ""
          }`}
          onClick={() => setStatusFilter("active")}
        >
          <span>Active</span>
          <strong>{counts.active}</strong>
        </button>

        <button
          type="button"
          className={`warranty-stat-card ${
            statusFilter === "expired" ? "selected" : ""
          }`}
          onClick={() => setStatusFilter("expired")}
        >
          <span>Expired</span>
          <strong>{counts.expired}</strong>
        </button>

        <button
          type="button"
          className={`warranty-stat-card ${
            statusFilter === "cancelled" ? "selected" : ""
          }`}
          onClick={() => setStatusFilter("cancelled")}
        >
          <span>Cancelled</span>
          <strong>{counts.cancelled}</strong>
        </button>
      </div>

      <div className="warranty-panel">
        <div className="warranty-panel-header">
          <div>
            <h3>Warranty Records</h3>
            <span>
              {filteredWarranties.length} of{" "}
              {warranties.length} warranties
            </span>
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={loadWarranties}
            disabled={loading}
          >
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>

        <div className="warranty-toolbar">
          <div className="warranty-search">
            <input
              type="text"
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search warranty, invoice, customer..."
            />
          </div>

          <select
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(event.target.value)
            }
          >
            <option value="all">All Statuses</option>
            <option value="active">Active</option>
            <option value="expired">Expired</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>

        {error && (
          <div className="warranty-error">
            {error}
          </div>
        )}

        {loading ? (
          <div className="table-state">
            Loading warranties...
          </div>
        ) : filteredWarranties.length === 0 ? (
          <div className="table-state">
            No warranties found.
          </div>
        ) : (
          <div className="warranty-table-wrap">
            <table className="warranty-table">
              <thead>
                <tr>
                  <th>Warranty ID</th>
                  <th>Invoice</th>
                  <th>Customer</th>
                  <th>Coverage</th>
                  <th>Duration</th>
                  <th>Transferable</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {filteredWarranties.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => {
                      setSelectedWarranty(item);
                    }}
                    style={{ cursor: "pointer" }}
                  >
                    <td>
                      <strong>{item.warranty_id}</strong>
                    </td>

                    <td>{item.invoice_id}</td>

                    <td>
                      <span className="warranty-mono">
                        {item.customer_id}
                      </span>
                    </td>

                    <td>
                      {formatDate(item.start_date)}
                      {" — "}
                      {formatDate(item.end_date)}
                    </td>

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
                        {statusLabel(item.status)}
                      </span>
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
          className="warranty-modal-overlay"
          onClick={() => setSelectedWarranty(null)}
        >
          <div
            className="warranty-details-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="warranty-modal-header">
              <div>
                <span className="page-eyebrow">
                  WARRANTY DETAILS
                </span>

                <h2>
                  {selectedWarranty.warranty_id}
                </h2>

                <p>
                  Warranty information registered on
                  DigiBills.
                </p>
              </div>

              <button
                type="button"
                className="modal-close-button"
                onClick={() =>
                  setSelectedWarranty(null)
                }
              >
                ×
              </button>
            </div>

            <div className="warranty-detail-grid">
              <Detail
                label="Warranty ID"
                value={selectedWarranty.warranty_id}
              />

              <Detail
                label="Invoice ID"
                value={selectedWarranty.invoice_id}
              />

              <Detail
                label="Customer ID"
                value={selectedWarranty.customer_id}
              />

              <Detail
                label="Product Variant"
                value={
                  selectedWarranty.product_variant_id
                }
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
                value={statusLabel(
                  selectedWarranty.status
                )}
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
