import {
  Search,
  Truck,
  CheckCircle,
  XCircle,
  Plus,
  RefreshCw,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../api";

type Supplier = {
  id: string;
  supplier_id: string;
  retailer_id: string;
  name: string;
  contact_person: string | null;
  phone_number: string | null;
  email: string | null;
  address: string | null;
  tax_identifier: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

type SupplierForm = {
  name: string;
  contact_person: string;
  phone_number: string;
  email: string;
  address: string;
  tax_identifier: string;
};

export default function RetailerSuppliers() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedSupplier, setSelectedSupplier] =
    useState<Supplier | null>(null);

  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");

  const [form, setForm] = useState<SupplierForm>({
    name: "",
    contact_person: "",
    phone_number: "",
    email: "",
    address: "",
    tax_identifier: "",
  });

  async function loadSuppliers() {
    try {
      setLoading(true);
      setError("");

      const result =
        await apiFetch<Supplier[]>("/suppliers");

      setSuppliers(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load suppliers."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSuppliers();
  }, []);

  const filteredSuppliers = useMemo(() => {
    const query = search.toLowerCase().trim();

    return suppliers.filter((supplier) => {
      const matchesSearch =
        !query ||
        supplier.name.toLowerCase().includes(query) ||
        supplier.supplier_id.toLowerCase().includes(query) ||
        (supplier.contact_person || "")
          .toLowerCase()
          .includes(query) ||
        (supplier.phone_number || "").includes(query) ||
        (supplier.email || "")
          .toLowerCase()
          .includes(query);

      const matchesStatus =
        status === "all" ||
        (status === "active" && supplier.is_active) ||
        (status === "inactive" && !supplier.is_active);

      return matchesSearch && matchesStatus;
    });
  }, [suppliers, search, status]);

  const counts = {
    all: suppliers.length,
    active: suppliers.filter(
      (supplier) => supplier.is_active
    ).length,
    inactive: suppliers.filter(
      (supplier) => !supplier.is_active
    ).length,
  };

  function updateForm(
    field: keyof SupplierForm,
    value: string
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  function openCreate() {
    setCreateError("");

    setForm({
      name: "",
      contact_person: "",
      phone_number: "",
      email: "",
      address: "",
      tax_identifier: "",
    });

    setShowCreate(true);
  }

  async function createSupplier(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!form.name.trim()) {
      setCreateError("Supplier name is required.");
      return;
    }

    try {
      setCreating(true);
      setCreateError("");

      await apiFetch<Supplier>("/suppliers", {
        method: "POST",
        body: JSON.stringify({
          name: form.name.trim(),
          contact_person:
            form.contact_person.trim() || null,
          phone_number:
            form.phone_number.trim() || null,
          email:
            form.email.trim() || null,
          address:
            form.address.trim() || null,
          tax_identifier:
            form.tax_identifier.trim() || null,
        }),
      });

      setShowCreate(false);

      await loadSuppliers();
    } catch (err) {
      setCreateError(
        err instanceof Error
          ? err.message
          : "Unable to create supplier."
      );
    } finally {
      setCreating(false);
    }
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

  return (
    <section className="dashboard admin-suppliers-page">
      <div className="admin-suppliers-header">
        <div>
          <div className="page-eyebrow">
            <span>SUPPLIER MANAGEMENT</span>
          </div>

          <h1>Suppliers</h1>

          <p>
            Manage suppliers and purchasing partners for your
            retailer inventory.
          </p>
        </div>

        <div
          style={{
            display: "flex",
            gap: 8,
            alignItems: "center",
          }}
        >
          <button
            type="button"
            className="secondary-button"
            onClick={loadSuppliers}
            disabled={loading}
          >
            <RefreshCw size={14} />
            Refresh
          </button>

          <button
            type="button"
            className="primary-button"
            onClick={openCreate}
          >
            <Plus size={17} />
            Add Supplier
          </button>
        </div>
      </div>

      <div className="supplier-stats-grid">
        <div className="stat-card">
          <div className="stat-icon blue">
            <Truck size={18} />
          </div>

          <div>
            <span>Total Suppliers</span>
            <strong>{counts.all}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">
            <CheckCircle size={18} />
          </div>

          <div>
            <span>Active</span>
            <strong>{counts.active}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon red">
            <XCircle size={18} />
          </div>

          <div>
            <span>Inactive</span>
            <strong>{counts.inactive}</strong>
          </div>
        </div>
      </div>

      <div className="suppliers-panel">
        <div className="suppliers-panel-header">
          <div>
            <h3>Supplier Directory</h3>
            <span>
              {filteredSuppliers.length} of {suppliers.length} suppliers
            </span>
          </div>

          <div className="suppliers-toolbar">
            <div className="suppliers-search">
              <Search size={16} />

              <input
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search suppliers..."
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
            Loading suppliers...
          </div>
        )}

        {!loading && error && (
          <div className="table-state negative">
            {error}
          </div>
        )}

        {!loading &&
          !error &&
          filteredSuppliers.length === 0 && (
            <div className="table-state">
              No suppliers found.
            </div>
          )}

        {!loading &&
          !error &&
          filteredSuppliers.length > 0 && (
            <div className="suppliers-table-wrap">
              <table className="suppliers-table">
                <thead>
                  <tr>
                    <th>Supplier</th>
                    <th>Supplier ID</th>
                    <th>Contact</th>
                    <th>Email</th>
                    <th>Status</th>
                    <th>Created</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredSuppliers.map((supplier) => (
                    <tr
                      key={supplier.id}
                      onClick={() =>
                        setSelectedSupplier(supplier)
                      }
                    >
                      <td>
                        <div className="supplier-cell">
                          <div className="supplier-avatar">
                            {supplier.name
                              .charAt(0)
                              .toUpperCase()}
                          </div>

                          <div>
                            <strong>{supplier.name}</strong>

                            <small>
                              {supplier.contact_person ||
                                "No contact person"}
                            </small>
                          </div>
                        </div>
                      </td>

                      <td>
                        <small>
                          {supplier.supplier_id}
                        </small>
                      </td>

                      <td>
                        <small>
                          {supplier.phone_number ||
                            "No phone"}
                        </small>
                      </td>

                      <td>
                        <small>
                          {supplier.email || "No email"}
                        </small>
                      </td>

                      <td>
                        <span
                          className={`supplier-status-badge ${
                            supplier.is_active
                              ? "active"
                              : "inactive"
                          }`}
                        >
                          {supplier.is_active
                            ? "Active"
                            : "Inactive"}
                        </span>
                      </td>

                      <td>
                        {formatDate(
                          supplier.created_at
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </div>

      {selectedSupplier && (
        <div
          className="modal-backdrop"
          onClick={() =>
            setSelectedSupplier(null)
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
                <h2>{selectedSupplier.name}</h2>
                <p>
                  Supplier ID:{" "}
                  {selectedSupplier.supplier_id}
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() =>
                  setSelectedSupplier(null)
                }
              >
                <X size={17} />
              </button>
            </div>

            <div className="form-group">
              <label>
                Contact Person
                <input
                  value={
                    selectedSupplier.contact_person ||
                    "Not provided"
                  }
                  readOnly
                />
              </label>

              <label>
                Phone Number
                <input
                  value={
                    selectedSupplier.phone_number ||
                    "Not provided"
                  }
                  readOnly
                />
              </label>

              <label>
                Email
                <input
                  value={
                    selectedSupplier.email ||
                    "Not provided"
                  }
                  readOnly
                />
              </label>

              <label>
                Tax Identifier
                <input
                  value={
                    selectedSupplier.tax_identifier ||
                    "Not provided"
                  }
                  readOnly
                />
              </label>

              <label>
                Address
                <textarea
                  rows={3}
                  value={
                    selectedSupplier.address ||
                    "Not provided"
                  }
                  readOnly
                />
              </label>
            </div>
          </div>
        </div>
      )}

      {showCreate && (
        <div
          className="modal-backdrop"
          onClick={() => setShowCreate(false)}
        >
          <div
            className="user-details-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="modal-header">
              <div>
                <h2>Add Supplier</h2>
                <p>
                  Add a supplier for your retailer.
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() =>
                  setShowCreate(false)
                }
              >
                <X size={17} />
              </button>
            </div>

            {createError && (
              <div className="login-error">
                {createError}
              </div>
            )}

            <form onSubmit={createSupplier}>
              <div className="form-group">
                <label>
                  Supplier Name *
                  <input
                    value={form.name}
                    onChange={(event) =>
                      updateForm(
                        "name",
                        event.target.value
                      )
                    }
                    placeholder="Supplier name"
                    required
                  />
                </label>

                <label>
                  Contact Person
                  <input
                    value={form.contact_person}
                    onChange={(event) =>
                      updateForm(
                        "contact_person",
                        event.target.value
                      )
                    }
                    placeholder="Contact person"
                  />
                </label>

                <label>
                  Phone Number
                  <input
                    type="tel"
                    value={form.phone_number}
                    onChange={(event) =>
                      updateForm(
                        "phone_number",
                        event.target.value
                      )
                    }
                    placeholder="Phone number"
                  />
                </label>

                <label>
                  Email
                  <input
                    type="email"
                    value={form.email}
                    onChange={(event) =>
                      updateForm(
                        "email",
                        event.target.value
                      )
                    }
                    placeholder="supplier@example.com"
                  />
                </label>

                <label>
                  Tax Identifier
                  <input
                    value={form.tax_identifier}
                    onChange={(event) =>
                      updateForm(
                        "tax_identifier",
                        event.target.value
                      )
                    }
                    placeholder="GST / Tax ID"
                  />
                </label>

                <label>
                  Address
                  <textarea
                    rows={3}
                    value={form.address}
                    onChange={(event) =>
                      updateForm(
                        "address",
                        event.target.value
                      )
                    }
                    placeholder="Supplier address"
                  />
                </label>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() =>
                    setShowCreate(false)
                  }
                  disabled={creating}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-button"
                  disabled={creating}
                >
                  <Plus size={14} />
                  {creating
                    ? "Creating..."
                    : "Create Supplier"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}
