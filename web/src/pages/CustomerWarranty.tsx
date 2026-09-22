import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  CalendarDays,
  Eye,
  FileText,
  Hash,
  Package,
  RefreshCw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api";

type Warranty = {
  id: string;
  warranty_id: string;
  invoice_id: string;
  product_variant_id: string;
  product_unit_id: string | null;
  product_name: string | null;
  variant_name: string | null;
  sku: string | null;
  serial_number: string | null;
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

function shortProductName(value: string | null | undefined) {
  if (!value) return "—";

  let shortName = value.split("|")[0].trim();

  // Remove trailing colour/variant text such as "(Black)".
  shortName = shortName
    .replace(/\s*\([^)]*\)\s*$/, "")
    .trim();

  // Remove a trailing model/SKU-style token such as "AquaSpin0075P".
  shortName = shortName
    .replace(/\s+[A-Za-z]+\d+[A-Za-z0-9]*$/, "")
    .trim();

  return shortName || value;
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

  const [searchTerm, setSearchTerm] = useState("");
  const [filterOpen, setFilterOpen] = useState(false);
  const [filterStatus, setFilterStatus] = useState("all");
  const [draftFilterStatus, setDraftFilterStatus] = useState("all");

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

  const filteredWarranties = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();

    return warranties.filter((warranty) => {
      const matchesSearch =
        !query ||
        [
          warranty.product_name,
          warranty.variant_name,
          warranty.invoice_id,
          warranty.warranty_id,
          warranty.sku,
          warranty.serial_number,
        ]
          .filter(Boolean)
          .some((value) =>
            String(value).toLowerCase().includes(query)
          );

      const matchesStatus =
        filterStatus === "all"
          ? true
          : filterStatus === "transferable"
            ? warranty.is_transferable &&
              warranty.status === "active"
            : filterStatus === "expired_cancelled"
              ? warranty.status === "expired" ||
                warranty.status === "cancelled"
              : warranty.status === filterStatus;

      return matchesSearch && matchesStatus;
    });
  }, [warranties, searchTerm, filterStatus]);

  return (
    <section className="dashboard customer-dashboard-page customer-warranty-page">
      <div className="page-heading customer-warranty-heading">
        <div>
          

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
        <div className="customer-warranty-search-row">
          <label className="customer-warranty-search">
            <Search size={19} />
            <input
              type="search"
              value={searchTerm}
              onChange={(event) =>
                setSearchTerm(event.target.value)
              }
              placeholder="Search by product, invoice..."
              aria-label="Search warranties"
            />
          </label>

          <button
            type="button"
            className={`customer-warranty-filter-button${
              filterStatus !== "all" ? " active" : ""
            }`}
            aria-label="Filter warranties"
            onClick={() => {
              setDraftFilterStatus(filterStatus);
              setFilterOpen(true);
            }}
          >
            <SlidersHorizontal size={20} />
          </button>
        </div>

        {loading ? (
          <div className="table-state">
            Loading your warranties...
          </div>
        ) : error ? (
          <div className="table-state negative">
            {error}
          </div>
        ) : filteredWarranties.length === 0 ? (
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
          <div className="customer-warranty-card-grid">
            {filteredWarranties.map((warranty) => (
              <button
                key={warranty.id}
                type="button"
                className="customer-ewarranty-card"
                onClick={() =>
                  setSelectedWarranty(warranty)
                }
              >
                <div className="customer-ewarranty-card-top">
                  <div className="customer-ewarranty-brand">
                    <div className="customer-ewarranty-icon">
                      <ShieldCheck size={20} />
                    </div>

                    <div>
                      <span>E-WARRANTY</span>
                      <strong>
                        {shortProductName(
                          warranty.product_name
                        )}
                      </strong>
                    </div>
                  </div>

                  <span
                    className={statusClass(
                      warranty.status
                    )}
                  >
                    {label(warranty.status)}
                  </span>
                </div>

                <div className="customer-ewarranty-product">
                  <span>PRODUCT</span>
                  <strong>
                    {shortProductName(
                      warranty.product_name
                    )}
                  </strong>
                </div>

                <div className="customer-ewarranty-info">
                  <div>
                    <span>WARRANTY NUMBER</span>
                    <strong>
                      {warranty.warranty_id.replace(
                        /(\d{4})(?=\d)/g,
                        "$1 "
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>VALID UP TO</span>
                    <strong>
                      {formatDate(warranty.end_date)}
                    </strong>
                  </div>
                </div>

                <div className="customer-ewarranty-card-footer">
                  <span>
                    {warranty.duration_months} month
                    {warranty.duration_months === 1
                      ? ""
                      : "s"}{" "}
                    coverage
                  </span>

                  <span className="customer-ewarranty-view">
                    View Details
                    <Eye size={16} />
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>


      {filterOpen && (
        <div
          className="customer-warranty-filter-backdrop"
          onClick={() => setFilterOpen(false)}
        >
          <div
            className="customer-warranty-filter-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="customer-warranty-filter-header">
              <div>
                <span className="page-eyebrow">
                  WARRANTY FILTERS
                </span>
                <h2>Filter Warranties</h2>
              </div>

              <button
                type="button"
                className="customer-warranty-filter-close"
                onClick={() => setFilterOpen(false)}
                aria-label="Close filters"
              >
                ×
              </button>
            </div>

            <div className="customer-warranty-filter-content">
              <div className="customer-warranty-filter-group">
                <strong>Status</strong>

                <div className="customer-warranty-filter-options">
                  {[
                    ["all", "All"],
                    ["active", "Active"],
                    ["transferable", "Transferable"],
                    ["expired_cancelled", "Expired / Cancelled"],
                  ].map(([value, labelText]) => (
                    <button
                      key={value}
                      type="button"
                      className={
                        draftFilterStatus === value
                          ? "selected"
                          : ""
                      }
                      onClick={() =>
                        setDraftFilterStatus(value)
                      }
                    >
                      <span className="customer-warranty-filter-option-icon">
                        <ShieldCheck size={18} />
                      </span>
                      <span>{labelText}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="customer-warranty-filter-group">
                <strong>Product Type</strong>

                <select
                  className="customer-warranty-filter-select"
                  defaultValue="all"
                  aria-label="Product type"
                >
                  <option value="all">All Products</option>
                </select>
              </div>

              <div className="customer-warranty-filter-group">
                <strong>Purchase Date</strong>

                <div className="customer-warranty-filter-dates">
                  <input
                    type="date"
                    aria-label="Purchase from date"
                  />
                  <input
                    type="date"
                    aria-label="Purchase to date"
                  />
                </div>
              </div>
            </div>

            <div className="customer-warranty-filter-actions">
              <button
                type="button"
                className="customer-warranty-filter-apply"
                onClick={() => {
                  setFilterStatus(draftFilterStatus);
                  setFilterOpen(false);
                }}
              >
                Apply Filters
              </button>

              <button
                type="button"
                className="customer-warranty-filter-reset"
                onClick={() => {
                  setDraftFilterStatus("all");
                  setFilterStatus("all");
                }}
              >
                Reset
              </button>
            </div>
          </div>
        </div>
      )}

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
            <div className="customer-ewarranty-modal-header">
              <div>
                <span className="page-eyebrow">
                  E-WARRANTY DETAILS
                </span>

                <h2>
                  {selectedWarranty.product_name ||
                    "Warranty Details"}
                </h2>
              </div>

              <button
                className="table-action-button"
                type="button"
                onClick={() =>
                  setSelectedWarranty(null)
                }
                aria-label="Close warranty details"
              >
                ×
              </button>
            </div>

            <div className="customer-ewarranty-modal-hero">
              <div className="customer-ewarranty-modal-product-icon">
                <Package size={28} />
              </div>

              <div className="customer-ewarranty-modal-product-copy">
                <span>E-WARRANTY</span>
                <strong>
                  {selectedWarranty.product_name ||
                    "Warranty Coverage"}
                </strong>

                {selectedWarranty.variant_name && (
                  <small>
                    {selectedWarranty.variant_name}
                  </small>
                )}
              </div>

              <span
                className={statusClass(
                  selectedWarranty.status
                )}
              >
                {label(selectedWarranty.status)}
              </span>
            </div>

            <div className="customer-ewarranty-modal-number">
              <div>
                <span>WARRANTY NUMBER</span>
                <strong>
                  {selectedWarranty.warranty_id.replace(
                    /(\d{4})(?=\d)/g,
                    "$1 "
                  )}
                </strong>
              </div>

              <div>
                <span>VALID UP TO</span>
                <strong>
                  {formatDate(
                    selectedWarranty.end_date
                  )}
                </strong>
              </div>
            </div>

            <div className="customer-ewarranty-detail-section">
              <div className="customer-ewarranty-detail-section-title">
                <Package size={17} />
                <strong>Product Information</strong>
              </div>

              <div className="customer-ewarranty-detail-list">
                <div>
                  <span>Product Name</span>
                  <strong>
                    {selectedWarranty.product_name ||
                      "—"}
                  </strong>
                </div>

                <div>
                  <span>Variant</span>
                  <strong>
                    {selectedWarranty.variant_name ||
                      "—"}
                  </strong>
                </div>

                <div>
                  <span>SKU</span>
                  <strong>
                    {selectedWarranty.sku || "—"}
                  </strong>
                </div>

                <div>
                  <span>Serial Number</span>
                  <strong>
                    {selectedWarranty.serial_number ||
                      "Not available"}
                  </strong>
                </div>
              </div>
            </div>

            <div className="customer-ewarranty-detail-section">
              <div className="customer-ewarranty-detail-section-title">
                <FileText size={17} />
                <strong>Purchase & Warranty Information</strong>
              </div>

              <div className="customer-ewarranty-detail-list">
                <div>
                  <span>Invoice Number</span>
                  <strong>
                    {selectedWarranty.invoice_id}
                  </strong>
                </div>

                <div>
                  <span>Warranty Start Date</span>
                  <strong>
                    {formatDate(
                      selectedWarranty.start_date
                    )}
                  </strong>
                </div>

                <div>
                  <span>Warranty End Date</span>
                  <strong>
                    {formatDate(
                      selectedWarranty.end_date
                    )}
                  </strong>
                </div>

                <div>
                  <span>Duration</span>
                  <strong>
                    {selectedWarranty.duration_months}{" "}
                    month
                    {selectedWarranty.duration_months === 1
                      ? ""
                      : "s"}
                  </strong>
                </div>

                <div>
                  <span>Transferable</span>
                  <strong>
                    {selectedWarranty.is_transferable
                      ? "Yes"
                      : "No"}
                  </strong>
                </div>

                <div>
                  <span>Created</span>
                  <strong>
                    {formatDate(
                      selectedWarranty.created_at
                    )}
                  </strong>
                </div>
              </div>
            </div>

            <div className="customer-ewarranty-status-section">
              <div className="customer-ewarranty-detail-section-title">
                <ShieldCheck size={17} />
                <strong>Warranty Status</strong>
              </div>

              <div
                className={`customer-ewarranty-status-box customer-ewarranty-status-box-${selectedWarranty.status}`}
              >
                <span>
                  <span className="customer-ewarranty-status-dot" />
                  {label(selectedWarranty.status)}
                </span>

                <small>
                  {selectedWarranty.status === "active"
                    ? "Your product is under warranty coverage."
                    : selectedWarranty.status === "expired"
                      ? "This warranty coverage has expired."
                      : "This warranty is no longer active."}
                </small>
              </div>
            </div>

            <button
              type="button"
              className="customer-ewarranty-modal-close"
              onClick={() =>
                setSelectedWarranty(null)
              }
            >
              Close
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
