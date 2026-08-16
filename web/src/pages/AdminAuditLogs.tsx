import {
  Search,
  Activity,
  Clock,
  FileText,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../api";

type AuditLog = {
  id: string;
  retailer_id: string | null;
  user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  description: string | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
};

export default function AdminAuditLogs() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [search, setSearch] = useState("");
  const [action, setAction] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedLog, setSelectedLog] =
    useState<AuditLog | null>(null);

  async function loadLogs() {
    try {
      setLoading(true);
      setError("");

      const result = await apiFetch<AuditLog[]>(
        "/admin/audit-logs"
      );

      setLogs(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load audit logs."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadLogs();
  }, []);

  const actions = useMemo(
    () =>
      Array.from(
        new Set(logs.map((item) => item.action))
      ).sort(),
    [logs]
  );

  const filteredLogs = useMemo(() => {
    const query = search.toLowerCase().trim();

    return logs.filter((item) => {
      const matchesSearch =
        !query ||
        item.action.toLowerCase().includes(query) ||
        item.entity_type.toLowerCase().includes(query) ||
        (item.entity_id || "")
          .toLowerCase()
          .includes(query) ||
        (item.description || "")
          .toLowerCase()
          .includes(query);

      const matchesAction =
        action === "all" || item.action === action;

      return matchesSearch && matchesAction;
    });
  }, [logs, search, action]);

  function formatDate(value: string) {
    return new Date(value).toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  return (
    <section className="dashboard audit-logs-page">
      <div className="audit-logs-header">
        <div>
          <div className="page-eyebrow">
            <span>SECURITY & ACTIVITY</span>
          </div>
          <h1>Audit Logs</h1>
          <p>
            Monitor important actions and system activity across DigiBills.
          </p>
        </div>
      </div>

      <div className="audit-stats-grid">
        <MiniStat
          icon={<Activity />}
          title="Total Events"
          value={logs.length}
          tone="blue"
        />

        <MiniStat
          icon={<Clock />}
          title="Latest Event"
          value={
            logs.length
              ? formatDate(logs[0].created_at)
              : "—"
          }
          tone="green"
        />

        <MiniStat
          icon={<FileText />}
          title="Filtered Events"
          value={filteredLogs.length}
          tone="purple"
        />
      </div>

      <div className="panel audit-panel">
        <div className="audit-panel-header">
          <div>
            <h3>System Activity</h3>
            <span>
              Showing {filteredLogs.length} of {logs.length} audit events
            </span>
          </div>

          <div className="audit-toolbar">
            <div className="audit-search">
              <Search size={16} />

              <input
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search activity..."
              />
            </div>

            <select
              value={action}
              onChange={(event) =>
                setAction(event.target.value)
              }
            >
              <option value="all">
                All Actions
              </option>

              {actions.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </div>
        </div>

        {loading && (
          <div className="table-state">
            Loading audit logs...
          </div>
        )}

        {!loading && error && (
          <div className="table-state negative">
            {error}
          </div>
        )}

        {!loading &&
          !error &&
          filteredLogs.length === 0 && (
            <div className="table-state">
              No audit logs found.
            </div>
          )}

        {!loading &&
          !error &&
          filteredLogs.length > 0 && (
            <div className="audit-table-wrap">
              <table className="audit-table">
                <thead>
                  <tr>
                    <th>Action</th>
                    <th>Entity</th>
                    <th>Description</th>
                    <th>User</th>
                    <th>Created</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredLogs.map((item) => (
                    <tr
                      key={item.id}
                      onClick={() =>
                        setSelectedLog(item)
                      }
                      style={{ cursor: "pointer" }}
                    >
                      <td>
                        <strong>{item.action}</strong>
                      </td>

                      <td>
                        <span className="status-badge">
                          {item.entity_type}
                        </span>
                      </td>

                      <td>
                        {item.description ||
                          "No description"}
                      </td>

                      <td>
                        {item.user_id
                          ? `${item.user_id.slice(
                              0,
                              8
                            )}...`
                          : "System"}
                      </td>

                      <td>
                        {formatDate(item.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </div>

      {selectedLog && (
        <AuditLogModal
          item={selectedLog}
          formatDate={formatDate}
          onClose={() => setSelectedLog(null)}
        />
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
  value: number | string;
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

function AuditLogModal({
  item,
  formatDate,
  onClose,
}: {
  item: AuditLog;
  formatDate: (value: string) => string;
  onClose: () => void;
}) {
  return (
    <div
      className="modal-backdrop"
      onClick={onClose}
    >
      <div
        className="audit-details-modal"
        onClick={(event) =>
          event.stopPropagation()
        }
      >
        <div className="modal-header">
          <div>
            <h2>Audit Log Details</h2>
            <p>
              Detailed system activity recorded by
              DigiBills.
            </p>
          </div>

          <button
            type="button"
            className="icon-button"
            onClick={onClose}
          >
            ×
          </button>
        </div>

        <div className="user-details-grid">
          <Detail
            label="Action"
            value={item.action}
          />
          <Detail
            label="Entity Type"
            value={item.entity_type}
          />
          <Detail
            label="Entity ID"
            value={item.entity_id || "Not specified"}
          />
          <Detail
            label="User ID"
            value={item.user_id || "System"}
          />
          <Detail
            label="Retailer ID"
            value={
              item.retailer_id || "Not specified"
            }
          />
          <Detail
            label="Description"
            value={
              item.description || "No description"
            }
          />
          <Detail
            label="IP Address"
            value={
              item.ip_address || "Not recorded"
            }
          />
          <Detail
            label="User Agent"
            value={
              item.user_agent || "Not recorded"
            }
          />
          <Detail
            label="Created At"
            value={formatDate(item.created_at)}
          />
        </div>
      </div>
    </div>
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
