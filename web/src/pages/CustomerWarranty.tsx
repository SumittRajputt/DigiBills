import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  Eye,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
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

function label(value: string | null | undefined) {
  if (!value) return "—";

  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase()
    );
}

function statusClass(value: string) {
  return `customer-warranty-status customer-warranty-status-${value}`;
}

export default function CustomerWarranty() {
  const navigate = useNavigate();

  const [warranties, setWarranties] = useState<Warranty[]>([]);
  const [selectedWarranty, setSelectedWarranty] =
    useState<Warranty | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadWarranties() {
    try {
      setLoading(true);
      setError("");

      const result =
        await apiFetch<Warranty[]>(
          "/customer/warranty"
        );

      setWarranties(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load your warranties."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadWarranties();
  }, []);

  const activeCount = useMemo(
    () =>
      warranties.filter(
        (warranty) => warranty.status === "active"
      ).length,
    [warranties]
  );

  const transferableCount = useMemo(
    () =>
      warranties.filter(
        (warranty) =>
          warranty.is_transferable &&
          warranty.status === "active"
      ).length,
    [warranties]
  );

  return (
    <section className="dashboard customer-dashboard-page customer-warranty-page">
      <div className="page-heading customer-warranty-heading">
        <div>
          <span className="page-eyebrow">
            CUSTOMER ACCOUNT
          </span>

          <h1>My Warranty</h1>

          <p>
            View warranty coverage associated with your
            purchases.
          </p>
        </div>

        <button
          className="secondary-button"
          type="button"
          onClick={loadWarranties}
          disabled={loading}
        >
          <RefreshCw
            size={15}
            className={loading ? "spin" : ""}
          />
          Refresh
        </button>
      </div>

      <div className="stats-grid four">
        <div className="stat-card">
          <div className="stat-icon blue">
            <ShieldCheck size={18} />
          </div>

          <div>
            <span>Total Warranties</span>
            <strong>{warranties.length}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">
            <ShieldCheck size={18} />
          </div>

          <div>
            <span>Active Warranties</span>
            <strong>{activeCount}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon purple">
            <ShieldCheck size={18} />
          </div>

          <div>
            <span>Transferable</span>
            <strong>{transferableCount}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon cyan">
            <ShieldCheck size={18} />
          </div>

          <div>
            <span>Expired / Cancelled</span>
            <strong>
              {warranties.length - activeCount}
            </strong>
          </div>
        </div>
      </div>

      <div className="panel customer-warranty-panel">
        <div className="panel-header">
          <div>
            <h3>Warranty Records</h3>
            <span>
              {warranties.length} warranty
              {warranties.length === 1 ? "" : "ies"} found
            </span>
          </div>
        </div>

        {loading ? (
          <div className="table-state">
            Loading your warranties...
          </div>
        ) : error ? (
          <div className="table-state negative">
            {error}
          </div>
        ) : warranties.length === 0 ? (
          <div className="table-state">
            <ShieldCheck size={22} />

            <div>
              <strong>No warranties found</strong>
              <p>
                Warranty records associated with your
                purchases will appear here.
              </p>
            </div>
          </div>
        ) : (
          <div className="customer-warranty-table-wrap">
            <table className="data-table customer-warranty-table">
              <thead>
                <tr>
                  <th>Warranty ID</th>
                  <th>Invoice</th>
                  <th>Start Date</th>
                  <th>End Date</th>
                  <th>Duration</th>
                  <th>Transferable</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>

              <tbody>
                {warranties.map((warranty) => (
                  <tr key={warranty.id}>
                    <td>
                      <strong>
                        {warranty.warranty_id}
                      </strong>
                    </td>

                    <td>
                      {warranty.invoice_id}
                    </td>

                    <td>
                      {formatDate(warranty.start_date)}
                    </td>

                    <td>
                      {formatDate(warranty.end_date)}
                    </td>

                    <td>
                      {warranty.duration_months} months
                    </td>

                    <td>
                      {warranty.is_transferable
                        ? "Yes"
                        : "No"}
                    </td>

                    <td>
                      <span
                        className={statusClass(
                          warranty.status
                        )}
                      >
                        {label(warranty.status)}
                      </span>
                    </td>

                    <td>
                      <button
                        className="table-action-button"
                        type="button"
                        title="View warranty"
                        onClick={() =>
                          setSelectedWarranty(warranty)
                        }
                      >
                        <Eye size={15} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <button
        className="secondary-button customer-warranty-back"
        type="button"
        onClick={() => navigate("/customer")}
      >
        <ArrowLeft size={15} />
        Back to Dashboard
      </button>

      {selectedWarranty && (
        <div
          className="customer-warranty-modal-backdrop"
          onClick={() =>
            setSelectedWarranty(null)
          }
        >
          <div
            className="customer-warranty-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="customer-warranty-modal-header">
              <div>
                <span className="page-eyebrow">
                  WARRANTY DETAILS
                </span>

                <h2>
                  {selectedWarranty.warranty_id}
                </h2>
              </div>

              <button
                className="table-action-button"
                type="button"
                onClick={() =>
                  setSelectedWarranty(null)
                }
              >
                ×
              </button>
            </div>

            <div className="customer-warranty-detail-grid">
              <div>
                <small>Warranty ID</small>
                <strong>
                  {selectedWarranty.warranty_id}
                </strong>
              </div>

              <div>
                <small>Invoice</small>
                <strong>
                  {selectedWarranty.invoice_id}
                </strong>
              </div>

              <div>
                <small>Start Date</small>
                <strong>
                  {formatDate(
                    selectedWarranty.start_date
                  )}
                </strong>
              </div>

              <div>
                <small>End Date</small>
                <strong>
                  {formatDate(
                    selectedWarranty.end_date
                  )}
                </strong>
              </div>

              <div>
                <small>Duration</small>
                <strong>
                  {selectedWarranty.duration_months} months
                </strong>
              </div>

              <div>
                <small>Transferable</small>
                <strong>
                  {selectedWarranty.is_transferable
                    ? "Yes"
                    : "No"}
                </strong>
              </div>

              <div>
                <small>Status</small>
                <span
                  className={statusClass(
                    selectedWarranty.status
                  )}
                >
                  {label(
                    selectedWarranty.status
                  )}
                </span>
              </div>

              <div>
                <small>Created</small>
                <strong>
                  {formatDate(
                    selectedWarranty.created_at
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
