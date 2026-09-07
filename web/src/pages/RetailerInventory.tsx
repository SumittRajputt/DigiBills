import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Boxes,
  MapPin,
  Package,
  Plus,
  RefreshCw,
  Search,
  Warehouse,
  X,
} from "lucide-react";
import { apiFetch } from "../api";

type Location = {
  id: string;
  name: string;
  location_type?: string;
  address?: string | null;
  is_active: boolean;
};

type Inventory = {
  id: string;
  location_id: string;
  product_variant_id: string;
  quantity_on_hand: number;
  quantity_reserved: number;
  quantity_available: number;
  reorder_level: number;
  reorder_quantity: number;
  average_cost: number | string;
  tax_rate: number | string;
  last_stocked_at?: string | null;
  updated_at: string;
};

type Movement = {
  id: string;
  movement_type: string;
  quantity: number;
  unit_cost?: number | string | null;
  reference_type?: string | null;
  notes?: string | null;
  created_at: string;
};

const money = (value: number | string | null | undefined) =>
  `₹${Number(value ?? 0).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;

const dateText = (value?: string | null) => {
  if (!value) return "—";
  const d = new Date(value);
  return Number.isNaN(d.getTime())
    ? "—"
    : d.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });
};

export default function RetailerInventory() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [locationId, setLocationId] = useState("");
  const [sku, setSku] = useState("");
  const [inventory, setInventory] = useState<Inventory | null>(null);
  const [movements, setMovements] = useState<Movement[]>([]);
  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [savingTax, setSavingTax] = useState(false);
  const [taxRate, setTaxRate] = useState("");
  const [error, setError] = useState("");

  const [showLocation, setShowLocation] = useState(false);
  const [showMovement, setShowMovement] = useState(false);

  const [locationForm, setLocationForm] = useState({
    name: "",
    location_type: "warehouse",
    address: "",
  });

  const [movementForm, setMovementForm] = useState({
    sku: "",
    movement_type: "stock_in",
    quantity: "",
    unit_cost: "",
    notes: "",
  });

  const loadLocations = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await apiFetch<Location[]>("/inventory-locations");

      setLocations(data);

      if (!locationId) {
        const active = data.find((item) => item.is_active);
        if (active) setLocationId(active.id);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load inventory locations."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLocations();
  }, []);

  const checkInventory = async () => {
    if (!locationId) {
      setError("Please select an inventory location.");
      return;
    }

    if (!sku.trim()) {
      setError("Please enter a SKU.");
      return;
    }

    try {
      setChecking(true);
      setError("");
      setInventory(null);
      setMovements([]);

      const item = await apiFetch<Inventory>(
        `/inventory/${encodeURIComponent(
          sku.trim()
        )}?location_id=${encodeURIComponent(locationId)}`
      );

      setInventory(item);
      setTaxRate(String(item.tax_rate ?? ""));

      try {
        const history = await apiFetch<Movement[]>(
          `/stock-movements/${encodeURIComponent(
            sku.trim()
          )}?location_id=${encodeURIComponent(locationId)}`
        );
        setMovements(history);
      } catch {
        setMovements([]);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to find inventory for this SKU."
      );
    } finally {
      setChecking(false);
    }
  };

  const saveTaxRate = async () => {
    if (!inventory) {
      setError("Please load an inventory item first.");
      return;
    }

    const value = Number(taxRate);

    if (!Number.isFinite(value) || value < 0 || value > 100) {
      setError("GST rate must be between 0 and 100 percent.");
      return;
    }

    try {
      setSavingTax(true);
      setError("");

      const updated = await apiFetch<Inventory>(
        `/inventory/${encodeURIComponent(inventory.id)}/tax-rate`,
        {
          method: "PUT",
          body: JSON.stringify({
            tax_rate: Number(value.toFixed(2)),
          }),
        }
      );

      setInventory(updated);
      setTaxRate(String(updated.tax_rate ?? value));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to update GST rate."
      );
    } finally {
      setSavingTax(false);
    }
  };

  const createLocation = async () => {
    if (!locationForm.name.trim()) {
      setError("Location name is required.");
      return;
    }

    try {
      setError("");

      const created = await apiFetch<Location>("/inventory-locations", {
        method: "POST",
        body: JSON.stringify({
          name: locationForm.name.trim(),
          location_type: locationForm.location_type.trim(),
          address: locationForm.address.trim() || null,
        }),
      });

      setLocations((current) => [created, ...current]);
      setLocationId(created.id);

      setLocationForm({
        name: "",
        location_type: "warehouse",
        address: "",
      });

      setShowLocation(false);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to create inventory location."
      );
    }
  };

  const createMovement = async () => {
    if (!locationId) {
      setError("Please select an inventory location.");
      return;
    }

    if (!movementForm.sku.trim()) {
      setError("SKU is required.");
      return;
    }

    const quantity = Number(movementForm.quantity);

    if (!Number.isInteger(quantity) || quantity <= 0) {
      setError("Quantity must be a positive whole number.");
      return;
    }

    try {
      setError("");

      await apiFetch("/stock-movements", {
        method: "POST",
        body: JSON.stringify({
          location_id: locationId,
          sku: movementForm.sku.trim(),
          movement_type: movementForm.movement_type,
          quantity,
          unit_cost: movementForm.unit_cost
            ? Number(movementForm.unit_cost)
            : null,
          notes: movementForm.notes.trim() || null,
        }),
      });

      setSku(movementForm.sku.trim());

      setMovementForm({
        sku: "",
        movement_type: "stock_in",
        quantity: "",
        unit_cost: "",
        notes: "",
      });

      setShowMovement(false);

      await checkInventory();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to record stock movement."
      );
    }
  };

  const selectedLocation = locations.find(
    (item) => item.id === locationId
  );

  const filteredMovements = movements.filter((movement) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;

    return [
      movement.movement_type,
      movement.reference_type,
      movement.notes,
      String(movement.quantity),
    ].some((value) => String(value ?? "").toLowerCase().includes(q));
  });

  const stockStatus =
    !inventory
      ? ""
      : inventory.quantity_available <= 0
      ? "out"
      : inventory.quantity_available <= inventory.reorder_level
      ? "low"
      : "healthy";

  return (
    <div className="dashboard retailer-inventory-page">
      
      <div className="retailer-inventory-heading">
        <div>
          <span className="page-eyebrow">INVENTORY MANAGEMENT</span>
          <h1>Inventory</h1>
          <p>Track stock levels, locations and stock movements.</p>
        </div>

        <div className="retailer-inventory-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={loadLocations}
            disabled={loading}
          >
            <RefreshCw size={14} />
            Refresh
          </button>

          <button
            type="button"
            className="primary-button"
            onClick={() => setShowMovement(true)}
            disabled={!locationId}
          >
            <Plus size={14} />
            Stock Movement
          </button>
        </div>
      </div>

      {error && (
        <div className="retailer-inventory-error">
          <AlertTriangle size={15} />
          <span>{error}</span>
          <button type="button" onClick={() => setError("")}>
            <X size={14} />
          </button>
        </div>
      )}

      <div className="inventory-summary-grid">
        <div className="inventory-summary-card">
          <div className="inventory-summary-icon blue">
            <Warehouse size={18} />
          </div>
          <div>
            <span>Locations</span>
            <strong>{locations.length}</strong>
          </div>
        </div>

        <div className="inventory-summary-card">
          <div className="inventory-summary-icon green">
            <Boxes size={18} />
          </div>
          <div>
            <span>Available Stock</span>
            <strong>{inventory?.quantity_available ?? "—"}</strong>
          </div>
        </div>

        <div className="inventory-summary-card">
          <div className="inventory-summary-icon orange">
            <Package size={18} />
          </div>
          <div>
            <span>Reserved</span>
            <strong>{inventory?.quantity_reserved ?? "—"}</strong>
          </div>
        </div>

        <div className="inventory-summary-card">
          <div className="inventory-summary-icon purple">
            <Package size={18} />
          </div>
          <div>
            <span>Average Cost</span>
            <strong>
              {inventory ? money(inventory.average_cost) : "—"}
            </strong>
          </div>
        </div>
      </div>

      <div className="inventory-toolbar">
        <div className="inventory-location-control">
          <MapPin size={15} />
          <select
            value={locationId}
            onChange={(event) => {
              setLocationId(event.target.value);
              setInventory(null);
              setMovements([]);
            }}
            disabled={loading}
          >
            <option value="">Select location</option>

            {locations.map((location) => (
              <option
                key={location.id}
                value={location.id}
                disabled={!location.is_active}
              >
                {location.name}
                {location.location_type
                  ? ` — ${location.location_type}`
                  : ""}
              </option>
            ))}
          </select>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={() => setShowLocation(true)}
        >
          <Plus size={14} />
          Add Location
        </button>

        <div className="inventory-search">
          <Search size={15} />

          <input
            value={sku}
            onChange={(event) => setSku(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") checkInventory();
            }}
            placeholder="Enter product SKU..."
          />

          <button
            type="button"
            onClick={checkInventory}
            disabled={checking || !locationId}
          >
            {checking ? "Checking..." : "Check Stock"}
          </button>
        </div>
      </div>

      {!locationId && !loading ? (
        <div className="inventory-empty-state">
          <Warehouse size={30} />
          <h3>No inventory location selected</h3>
          <p>Select an existing location or create a new one.</p>

          <button
            type="button"
            className="primary-button"
            onClick={() => setShowLocation(true)}
          >
            <Plus size={14} />
            Create Location
          </button>
        </div>
      ) : !inventory ? (
        <div className="inventory-empty-state compact">
          <Package size={30} />
          <h3>Check product inventory</h3>
          <p>
            Select a location and enter a SKU to view current stock,
            reorder levels and movement history.
          </p>
        </div>
      ) : (
        <>
          <div className="inventory-detail-grid">
            <section className="inventory-panel">
              <div className="inventory-panel-header">
                <div>
                  <h3>Stock Overview</h3>
                  <span>{selectedLocation?.name ?? "Selected location"}</span>
                </div>

                <span className={`inventory-health ${stockStatus}`}>
                  {stockStatus === "healthy"
                    ? "Healthy"
                    : stockStatus === "low"
                    ? "Low Stock"
                    : "Out of Stock"}
                </span>
              </div>

              <div className="inventory-stock-main">
                <div className="inventory-stock-number">
                  <span>Available Quantity</span>
                  <strong>{inventory.quantity_available}</strong>
                  <small>
                    {inventory.quantity_on_hand} on hand ·{" "}
                    {inventory.quantity_reserved} reserved
                  </small>
                </div>

                <div className="inventory-metric-list">
                  <div>
                    <span>Reorder Level</span>
                    <strong>{inventory.reorder_level}</strong>
                  </div>

                  <div>
                    <span>Reorder Quantity</span>
                    <strong>{inventory.reorder_quantity}</strong>
                  </div>

                  <div>
                    <span>Average Cost</span>
                    <strong>{money(inventory.average_cost)}</strong>
                  </div>

                  <div>
                    <span>Last Stocked</span>
                    <strong>{dateText(inventory.last_stocked_at)}</strong>
                  </div>
                </div>
              </div>
            </section>

            <section className="inventory-panel">
              <div className="inventory-panel-header">
                <div>
                  <h3>Inventory Location</h3>
                  <span>Current stock location</span>
                </div>
              </div>

              <div className="inventory-location-detail">
                <div className="inventory-location-icon">
                  <Warehouse size={20} />
                </div>

                <div>
                  <strong>{selectedLocation?.name ?? "—"}</strong>
                  <span>
                    {selectedLocation?.location_type ?? "—"}
                  </span>
                  <small>
                    {selectedLocation?.address ||
                      "No address provided"}
                  </small>
                </div>
              </div>
            </section>
          </div>

          <section className="inventory-panel">
            <div className="inventory-panel-header">
              <div>
                <h3>GST Configuration</h3>
                <span>Retailer-controlled GST for this inventory item</span>
              </div>
            </div>

            <div className="inventory-form">
              <label>
                GST Rate (%)
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.01"
                  value={taxRate}
                  onChange={(event) => setTaxRate(event.target.value)}
                  placeholder="18.00"
                />
              </label>

              <div style={{ marginTop: "12px" }}>
                <button
                  type="button"
                  className="primary-button"
                  onClick={saveTaxRate}
                  disabled={savingTax}
                >
                  {savingTax ? "Saving..." : "Save GST"}
                </button>
              </div>
            </div>
          </section>

          <section className="inventory-panel inventory-movement-panel">
            <div className="inventory-panel-header">
              <div>
                <h3>Stock Movements</h3>
                <span>Recent inventory movement history</span>
              </div>

              <div className="inventory-movement-search">
                <Search size={13} />
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search"
                />
              </div>
            </div>

            {filteredMovements.length === 0 ? (
              <div className="inventory-empty-inline">
                <Package size={20} />
                <span>No stock movements found.</span>
              </div>
            ) : (
              <div className="inventory-movement-table-wrap">
                <table className="inventory-movement-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Movement</th>
                      <th>Quantity</th>
                      <th>Unit Cost</th>
                      <th>Reference</th>
                      <th>Notes</th>
                    </tr>
                  </thead>

                  <tbody>
                    {filteredMovements.map((movement) => (
                      <tr key={movement.id}>
                        <td>{dateText(movement.created_at)}</td>

                        <td>
                          <span
                            className={`movement-type ${movement.movement_type}`}
                          >
                            {movement.movement_type.split("_").join(" ")}
                          </span>
                        </td>

                        <td>
                          <strong>{movement.quantity}</strong>
                        </td>

                        <td>
                          {movement.unit_cost
                            ? money(movement.unit_cost)
                            : "—"}
                        </td>

                        <td>{movement.reference_type || "—"}</td>

                        <td>
                          <span className="movement-notes">
                            {movement.notes || "—"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}

      {showLocation && (
        <div className="inventory-modal-backdrop">
          <div className="inventory-modal">
            <div className="inventory-modal-header">
              <div>
                <h2>Add Inventory Location</h2>
                <p>Create a warehouse or stock location.</p>
              </div>

              <button
                type="button"
                onClick={() => setShowLocation(false)}
              >
                <X size={17} />
              </button>
            </div>

            <div className="inventory-form">
              <label>
                Location Name
                <input
                  value={locationForm.name}
                  onChange={(event) =>
                    setLocationForm({
                      ...locationForm,
                      name: event.target.value,
                    })
                  }
                  placeholder="Main Warehouse"
                />
              </label>

              <label>
                Location Type
                <input
                  value={locationForm.location_type}
                  onChange={(event) =>
                    setLocationForm({
                      ...locationForm,
                      location_type: event.target.value,
                    })
                  }
                  placeholder="warehouse"
                />
              </label>

              <label>
                Address
                <textarea
                  rows={3}
                  value={locationForm.address}
                  onChange={(event) =>
                    setLocationForm({
                      ...locationForm,
                      address: event.target.value,
                    })
                  }
                  placeholder="Optional address"
                />
              </label>
            </div>

            <div className="inventory-modal-footer">
              <button
                type="button"
                className="secondary-button"
                onClick={() => setShowLocation(false)}
              >
                Cancel
              </button>

              <button
                type="button"
                className="primary-button"
                onClick={createLocation}
              >
                <Plus size={14} />
                Create Location
              </button>
            </div>
          </div>
        </div>
      )}

      {showMovement && (
        <div className="inventory-modal-backdrop">
          <div className="inventory-modal">
            <div className="inventory-modal-header">
              <div>
                <h2>Stock Movement</h2>
                <p>Record inventory coming in or going out.</p>
              </div>

              <button
                type="button"
                onClick={() => setShowMovement(false)}
              >
                <X size={17} />
              </button>
            </div>

            <div className="inventory-form">
              <label>
                SKU
                <input
                  value={movementForm.sku}
                  onChange={(event) =>
                    setMovementForm({
                      ...movementForm,
                      sku: event.target.value,
                    })
                  }
                  placeholder="Product SKU"
                />
              </label>

              <label>
                Movement Type
                <select
                  value={movementForm.movement_type}
                  onChange={(event) =>
                    setMovementForm({
                      ...movementForm,
                      movement_type: event.target.value,
                    })
                  }
                >
                  <option value="stock_in">Stock In</option>
                  <option value="stock_out">Stock Out</option>
                  <option value="adjustment">Adjustment</option>
                  <option value="opening_stock">Opening Stock</option>
                </select>
              </label>

              <label>
                Quantity
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={movementForm.quantity}
                  onChange={(event) =>
                    setMovementForm({
                      ...movementForm,
                      quantity: event.target.value,
                    })
                  }
                  placeholder="0"
                />
              </label>

              <label>
                Unit Cost
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={movementForm.unit_cost}
                  onChange={(event) =>
                    setMovementForm({
                      ...movementForm,
                      unit_cost: event.target.value,
                    })
                  }
                  placeholder="0.00"
                />
              </label>

              <label>
                Notes
                <textarea
                  rows={3}
                  value={movementForm.notes}
                  onChange={(event) =>
                    setMovementForm({
                      ...movementForm,
                      notes: event.target.value,
                    })
                  }
                  placeholder="Optional notes"
                />
              </label>
            </div>

            <div className="inventory-modal-footer">
              <button
                type="button"
                className="secondary-button"
                onClick={() => setShowMovement(false)}
              >
                Cancel
              </button>

              <button
                type="button"
                className="primary-button"
                onClick={createMovement}
              >
                <Package size={14} />
                Record Movement
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
