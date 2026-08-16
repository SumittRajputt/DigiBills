import { Search, Plus, CheckCircle, Clock, XCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../api";

type Retailer = {
  id: string;
  retailer_id: string;
  owner_user_id: string;
  business_name: string;
  business_type: string;
  phone_number: string;
  email: string | null;
  address: string | null;
  status: string;
  approved_at: string | null;
  rejection_reason: string | null;
  created_at: string;
  updated_at: string;
};

export default function AdminRetailers() {
  const [retailers, setRetailers] = useState<Retailer[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState("");
  const [actionError, setActionError] = useState("");

  async function loadRetailers() {
    try {
      setLoading(true);
      setError("");

      const result = await apiFetch<Retailer[]>("/retailers");
      setRetailers(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load retailers."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRetailers();
  }, []);

  const filteredRetailers = useMemo(() => {
    const query = search.toLowerCase().trim();

    return retailers.filter((retailer) => {
      const matchesSearch =
        !query ||
        retailer.business_name.toLowerCase().includes(query) ||
        retailer.retailer_id.toLowerCase().includes(query) ||
        retailer.phone_number.includes(query) ||
        (retailer.email || "").toLowerCase().includes(query);

      const matchesStatus =
        status === "all" ||
        retailer.status.toLowerCase() === status;

      return matchesSearch && matchesStatus;
    });
  }, [retailers, search, status]);

  async function approveRetailer(retailerId: string) {
    try {
      setActionLoading(retailerId);
      setActionError("");

      await apiFetch(`/retailers/${retailerId}/approve`, {
        method: "POST",
      });

      await loadRetailers();
    } catch (err) {
      setActionError(
        err instanceof Error
          ? err.message
          : "Unable to approve retailer."
      );
    } finally {
      setActionLoading("");
    }
  }

  async function rejectRetailer(retailerId: string) {
    const reason = window.prompt(
      "Enter rejection reason:"
    );

    if (!reason || !reason.trim()) {
      return;
    }

    try {
      setActionLoading(retailerId);
      setActionError("");

      await apiFetch(`/retailers/${retailerId}/reject`, {
        method: "POST",
        body: JSON.stringify({
          rejection_reason: reason.trim(),
        }),
      });

      await loadRetailers();
    } catch (err) {
      setActionError(
        err instanceof Error
          ? err.message
          : "Unable to reject retailer."
      );
    } finally {
      setActionLoading("");
    }
  }

  const counts = {
    all: retailers.length,
    active: retailers.filter((r) => r.status === "active").length,
    pending: retailers.filter((r) => r.status === "pending").length,
    rejected: retailers.filter((r) => r.status === "rejected").length,
  };

  return (
    <section className="dashboard">
      <div className="welcome-row">
        <div>
          <h1>Retailers</h1>
          <p>Manage all retailers registered on DigiBills.</p>
        </div>

        <button className="primary-button">
          <Plus size={17} />
          Add Retailer
        </button>
      </div>

      <div className="stats-grid four">
        <MiniStat
          icon={<CheckCircle />}
          title="Total Retailers"
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
          title="Pending"
          value={counts.pending}
          tone="orange"
        />

        <MiniStat
          icon={<XCircle />}
          title="Rejected"
          value={counts.rejected}
          tone="red"
        />
      </div>

      <div className="panel retailer-table-panel">
        <div className="table-toolbar">
          <div>
            <h3>All Retailers</h3>
            <span>{filteredRetailers.length} retailers</span>
          </div>

          <div className="table-controls">
            <div className="table-search">
              <Search size={16} />
              <input
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search retailers..."
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
              <option value="pending">Pending</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </div>

        {loading && (
          <div className="table-state">
            Loading retailers...
          </div>
        )}

        {!loading && error && (
          <div className="table-state negative">
            {error}
          </div>
        )}

        {!loading &&
          !error &&
          filteredRetailers.length === 0 && (
            <div className="table-state">
              No retailers found.
            </div>
          )}

        {actionError && (
          <div className="table-state negative">
            {actionError}
          </div>
        )}

        {!loading &&
          !error &&
          filteredRetailers.length > 0 && (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Retailer</th>
                    <th>Business Type</th>
                    <th>Contact</th>
                    <th>Location</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredRetailers.map((retailer) => (
                    <tr key={retailer.id}>
                      <td>
                        <div className="retailer-cell">
                          <div className="retailer-avatar">
                            {retailer.business_name
                              .charAt(0)
                              .toUpperCase()}
                          </div>

                          <div>
                            <strong>
                              {retailer.business_name}
                            </strong>
                            <small>
                              {retailer.retailer_id}
                            </small>
                          </div>
                        </div>
                      </td>

                      <td>{retailer.business_type}</td>

                      <td>
                        <div className="contact-cell">
                          <span>
                            {retailer.phone_number}
                          </span>
                          {retailer.email && (
                            <small>{retailer.email}</small>
                          )}
                        </div>
                      </td>

                      <td>
                        {retailer.address || "—"}
                      </td>

                      <td>
                        <StatusBadge
                          status={retailer.status}
                        />
                      </td>

                      <td>
                        {new Date(
                          retailer.created_at
                        ).toLocaleDateString(
                          "en-IN",
                          {
                            day: "2-digit",
                            month: "short",
                            year: "numeric",
                          }
                        )}
                      </td>

                      <td>
                        <div className="table-actions">
                          {retailer.status === "pending" && (
                            <>
                              <button
                                type="button"
                                className="action-button approve"
                                disabled={
                                  actionLoading === retailer.retailer_id
                                }
                                onClick={() =>
                                  approveRetailer(
                                    retailer.retailer_id
                                  )
                                }
                              >
                                {actionLoading === retailer.retailer_id
                                  ? "..."
                                  : "Approve"}
                              </button>

                              <button
                                type="button"
                                className="action-button reject"
                                disabled={
                                  actionLoading === retailer.retailer_id
                                }
                                onClick={() =>
                                  rejectRetailer(
                                    retailer.retailer_id
                                  )
                                }
                              >
                                Reject
                              </button>
                            </>
                          )}

                          {retailer.status === "active" && (
                            <span className="action-muted">
                              Approved
                            </span>
                          )}

                          {retailer.status === "rejected" && (
                            <span className="action-muted">
                              Rejected
                            </span>
                          )}
                        </div>
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
        <strong>{value.toLocaleString("en-IN")}</strong>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();

  return (
    <span className={`status-badge ${normalized}`}>
      <span className="status-dot" />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}
