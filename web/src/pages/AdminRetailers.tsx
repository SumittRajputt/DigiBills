import {
  Building2,
  CheckCircle2,
  Clock3,
  Mail,
  MapPin,
  Phone,
  RefreshCw,
  Search,
  ShieldCheck,
  XCircle,
} from "lucide-react";
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

type Status = "all" | "active" | "pending" | "rejected";

export default function AdminRetailers() {
  const [retailers, setRetailers] = useState<Retailer[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<Status>("all");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState("");
  const [actionError, setActionError] = useState("");

  async function loadRetailers(showRefresh = false) {
    try {
      if (showRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

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
      setRefreshing(false);
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

  const counts = {
    all: retailers.length,
    active: retailers.filter(
      (retailer) => retailer.status === "active"
    ).length,
    pending: retailers.filter(
      (retailer) => retailer.status === "pending"
    ).length,
    rejected: retailers.filter(
      (retailer) => retailer.status === "rejected"
    ).length,
  };

  async function approveRetailer(retailerId: string) {
    try {
      setActionLoading(retailerId);
      setActionError("");

      await apiFetch(`/retailers/${retailerId}/approve`, {
        method: "POST",
      });

      await loadRetailers(true);
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

      await loadRetailers(true);
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

  return (
    <section className="dashboard retailers-page">
      <header className="retailers-header">
        <div>
          <div className="page-eyebrow">
            <ShieldCheck size={14} />
            Administration
          </div>

          <h1>Retailers</h1>

          <p>
            Manage retailer accounts, approvals and
            business information across DigiBills.
          </p>
        </div>

        <button
          type="button"
          className="retailers-refresh"
          onClick={() => loadRetailers(true)}
          disabled={refreshing}
        >
          <RefreshCw
            size={15}
            className={refreshing ? "spin" : ""}
          />
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </header>

      <div className="retailer-stats">
        <RetailerStat
          icon={<Building2 />}
          label="Total retailers"
          value={counts.all}
          tone="blue"
        />

        <RetailerStat
          icon={<CheckCircle2 />}
          label="Active"
          value={counts.active}
          tone="green"
        />

        <RetailerStat
          icon={<Clock3 />}
          label="Pending review"
          value={counts.pending}
          tone="orange"
        />

        <RetailerStat
          icon={<XCircle />}
          label="Rejected"
          value={counts.rejected}
          tone="red"
        />
      </div>

      <section className="retailers-panel">
        <div className="retailers-panel-header">
          <div>
            <h2>Retailer directory</h2>
            <p>
              {filteredRetailers.length} of {retailers.length}{" "}
              retailers
            </p>
          </div>

          <div className="retailer-filter-summary">
            {status === "all"
              ? "All retailers"
              : `${status.charAt(0).toUpperCase()}${status.slice(1)} retailers`}
          </div>
        </div>

        <div className="retailers-toolbar">
          <div className="retailer-search">
            <Search size={17} />

            <input
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search by retailer, ID, phone or email..."
            />
          </div>

          <select
            value={status}
            onChange={(event) =>
              setStatus(event.target.value as Status)
            }
            className="retailer-status-filter"
          >
            <option value="all">All statuses</option>
            <option value="active">Active</option>
            <option value="pending">Pending</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>

        {actionError && (
          <div className="retailer-alert error">
            <XCircle size={16} />
            {actionError}
          </div>
        )}

        {loading && (
          <div className="retailer-table-state">
            <RefreshCw size={20} className="spin" />
            <strong>Loading retailers</strong>
            <span>
              Fetching the latest retailer information...
            </span>
          </div>
        )}

        {!loading && error && (
          <div className="retailer-table-state error">
            <XCircle size={22} />
            <strong>Unable to load retailers</strong>
            <span>{error}</span>

            <button
              type="button"
              onClick={() => loadRetailers()}
            >
              Try again
            </button>
          </div>
        )}

        {!loading &&
          !error &&
          filteredRetailers.length === 0 && (
            <div className="retailer-table-state">
              <Search size={22} />
              <strong>No retailers found</strong>
              <span>
                Try changing your search or status filter.
              </span>
            </div>
          )}

        {!loading &&
          !error &&
          filteredRetailers.length > 0 && (
            <div className="retailers-table-wrap">
              <table className="retailers-table">
                <thead>
                  <tr>
                    <th>Retailer</th>
                    <th>Business</th>
                    <th>Contact</th>
                    <th>Location</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Action</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredRetailers.map((retailer) => (
                    <tr key={retailer.id}>
                      <td>
                        <div className="retailer-identity">
                          <div className="retailer-avatar">
                            {retailer.business_name
                              .charAt(0)
                              .toUpperCase()}
                          </div>

                          <div className="retailer-identity-text">
                            <strong>
                              {retailer.business_name}
                            </strong>

                            <span>
                              {retailer.retailer_id}
                            </span>
                          </div>
                        </div>
                      </td>

                      <td>
                        <div className="retailer-business">
                          <strong>
                            {retailer.business_type}
                          </strong>
                          <span>Registered business</span>
                        </div>
                      </td>

                      <td>
                        <div className="retailer-contact">
                          <span>
                            <Phone size={13} />
                            {retailer.phone_number}
                          </span>

                          {retailer.email && (
                            <span>
                              <Mail size={13} />
                              {retailer.email}
                            </span>
                          )}
                        </div>
                      </td>

                      <td>
                        <div className="retailer-location">
                          <MapPin size={14} />
                          <span>
                            {retailer.address ||
                              "Address not provided"}
                          </span>
                        </div>
                      </td>

                      <td>
                        <StatusBadge
                          status={retailer.status}
                        />
                      </td>

                      <td>
                        <div className="retailer-date">
                          {formatDate(retailer.created_at)}
                        </div>
                      </td>

                      <td>
                        {retailer.status === "pending" ? (
                          <div className="retailer-actions">
                            <button
                              type="button"
                              className="retailer-action approve"
                              disabled={
                                actionLoading ===
                                retailer.retailer_id
                              }
                              onClick={() =>
                                approveRetailer(
                                  retailer.retailer_id
                                )
                              }
                            >
                              {actionLoading ===
                              retailer.retailer_id
                                ? "..."
                                : "Approve"}
                            </button>

                            <button
                              type="button"
                              className="retailer-action reject"
                              disabled={
                                actionLoading ===
                                retailer.retailer_id
                              }
                              onClick={() =>
                                rejectRetailer(
                                  retailer.retailer_id
                                )
                              }
                            >
                              Reject
                            </button>
                          </div>
                        ) : (
                          <span className="retailer-action-muted">
                            {retailer.status === "active"
                              ? "Approved"
                              : "Rejected"}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </section>
    </section>
  );
}

function RetailerStat({
  icon,
  label,
  value,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  tone: string;
}) {
  return (
    <div className="retailer-stat">
      <div className={`retailer-stat-icon ${tone}`}>
        {icon}
      </div>

      <div>
        <span>{label}</span>
        <strong>{value.toLocaleString("en-IN")}</strong>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();

  return (
    <span
      className={`retailer-status-badge ${normalized}`}
    >
      <span />
      {status.charAt(0).toUpperCase() +
        status.slice(1)}
    </span>
  );
}

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
