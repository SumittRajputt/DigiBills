import {
  Search,
  ShoppingCart,
  CheckCircle,
  Clock,
  XCircle,
  PackageCheck,
  Plus,
  X,
  RefreshCw,
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
};

type Location = {
  id: string;
  retailer_id: string;
  name: string;
  location_type: string;
  address: string | null;
  is_active: boolean;
};

type Variant = {
  id: string;
  product_id: string;
  sku: string;
  barcode: string | null;
  variant_name: string;
  selling_price: string;
  purchase_cost: string | null;
  tax_rate: string;
  track_inventory: boolean;
  requires_serial_number: boolean;
  status: string;
};

type PurchaseOrder = {
  id: string;
  purchase_order_id: string;
  retailer_id: string;
  supplier_id: string;
  location_id: string;
  created_by_user_id: string | null;
  status: string;
  subtotal: string;
  tax_amount: string;
  total_amount: string;
  expected_delivery_date: string | null;
  received_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

type PurchaseItem = {
  id: string;
  purchase_order_id: string;
  product_variant_id: string;
  product_name: string;
  sku: string | null;
  ordered_quantity: number;
  received_quantity: number;
  unit_cost: string;
  tax_rate: string;
  tax_amount: string;
  line_total: string;
  received_at: string | null;
  created_at: string;
  updated_at: string;
};

type DraftItem = {
  sku: string;
  ordered_quantity: string;
  unit_cost: string;
  tax_rate: string;
};

export default function RetailerPurchases() {
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [variants, setVariants] = useState<Variant[]>([]);

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedOrder, setSelectedOrder] =
    useState<PurchaseOrder | null>(null);
  const [selectedItems, setSelectedItems] =
    useState<PurchaseItem[]>([]);
  const [itemsLoading, setItemsLoading] = useState(false);

  const [showCreate, setShowCreate] = useState(false);
  const [supplierId, setSupplierId] = useState("");
  const [locationId, setLocationId] = useState("");
  const [expectedDelivery, setExpectedDelivery] =
    useState("");
  const [notes, setNotes] = useState("");

  const [draftItems, setDraftItems] = useState<DraftItem[]>([
    {
      sku: "",
      ordered_quantity: "1",
      unit_cost: "",
      tax_rate: "0",
    },
  ]);

  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState("");

  async function loadData() {
    try {
      setLoading(true);
      setError("");

      const [orderResult, supplierResult, locationResult, variantResult] =
        await Promise.all([
          apiFetch<PurchaseOrder[]>("/purchase-orders"),
          apiFetch<Supplier[]>("/suppliers"),
          apiFetch<Location[]>("/inventory-locations"),
          apiFetch<Variant[]>("/product-variants"),
        ]);

      setOrders(orderResult);
      setSuppliers(supplierResult);
      setLocations(locationResult);
      setVariants(variantResult);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load purchases."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function loadItems(order: PurchaseOrder) {
    try {
      setItemsLoading(true);

      const result = await apiFetch<PurchaseItem[]>(
        `/purchase-orders/${encodeURIComponent(
          order.purchase_order_id
        )}/items`
      );

      setSelectedItems(result);
    } catch (err) {
      setActionError(
        err instanceof Error
          ? err.message
          : "Unable to load purchase items."
      );
    } finally {
      setItemsLoading(false);
    }
  }

  async function openOrder(order: PurchaseOrder) {
    setActionError("");
    setSelectedOrder(order);
    await loadItems(order);
  }

  const filteredOrders = useMemo(() => {
    const query = search.toLowerCase().trim();

    return orders.filter((order) => {
      const supplier = suppliers.find(
        (item) => item.supplier_id === order.supplier_id
      );

      const matchesSearch =
        !query ||
        order.purchase_order_id
          .toLowerCase()
          .includes(query) ||
        order.supplier_id
          .toLowerCase()
          .includes(query) ||
        (supplier?.name || "")
          .toLowerCase()
          .includes(query);

      const matchesStatus =
        status === "all" ||
        order.status.toLowerCase() === status;

      return matchesSearch && matchesStatus;
    });
  }, [orders, suppliers, search, status]);

  const pendingCount = orders.filter(
    (order) =>
      order.status.toLowerCase() === "draft" ||
      order.status.toLowerCase() === "ordered" ||
      order.status.toLowerCase() === "partially_received"
  ).length;

  const receivedCount = orders.filter(
    (order) =>
      order.status.toLowerCase() === "received"
  ).length;

  const cancelledCount = orders.filter(
    (order) =>
      order.status.toLowerCase() === "cancelled"
  ).length;

  const totalValue = orders.reduce(
    (sum, order) =>
      sum + Number(order.total_amount || 0),
    0
  );

  function formatMoney(value: string | number) {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(Number(value || 0));
  }

  function formatDate(value: string | null) {
    if (!value) return "—";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "—";
    }

    return date.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  function supplierName(id: string) {
    return (
      suppliers.find(
        (supplier) => supplier.supplier_id === id
      )?.name || id
    );
  }

  function locationName(id: string) {
    return (
      locations.find(
        (location) => location.id === id
      )?.name || id
    );
  }

  function updateDraftItem(
    index: number,
    field: keyof DraftItem,
    value: string
  ) {
    setDraftItems((current) =>
      current.map((item, itemIndex) =>
        itemIndex === index
          ? { ...item, [field]: value }
          : item
      )
    );
  }

  function addDraftItem() {
    setDraftItems((current) => [
      ...current,
      {
        sku: "",
        ordered_quantity: "1",
        unit_cost: "",
        tax_rate: "0",
      },
    ]);
  }

  function removeDraftItem(index: number) {
    setDraftItems((current) =>
      current.length === 1
        ? current
        : current.filter(
            (_, itemIndex) => itemIndex !== index
          )
    );
  }

  async function createOrder() {
    if (!supplierId) {
      setActionError("Please select a supplier.");
      return;
    }

    if (!locationId) {
      setActionError(
        "Please select an inventory location."
      );
      return;
    }

    const validItems = draftItems.filter(
      (item) => item.sku.trim()
    );

    if (!validItems.length) {
      setActionError(
        "Add at least one product item."
      );
      return;
    }

    try {
      setActionLoading(true);
      setActionError("");

      const created = await apiFetch<PurchaseOrder>(
        "/purchase-orders",
        {
          method: "POST",
          body: JSON.stringify({
            supplier_id: supplierId,
            location_id: locationId,
            expected_delivery_date:
              expectedDelivery
                ? new Date(
                    expectedDelivery
                  ).toISOString()
                : null,
            notes: notes.trim() || null,
          }),
        }
      );

      for (const item of validItems) {
        const quantity = Number(
          item.ordered_quantity
        );
        const unitCost = Number(item.unit_cost);
        const taxRate = Number(item.tax_rate || 0);

        if (
          !Number.isFinite(quantity) ||
          quantity <= 0
        ) {
          throw new Error(
            `Invalid quantity for SKU ${item.sku}.`
          );
        }

        if (
          !Number.isFinite(unitCost) ||
          unitCost < 0
        ) {
          throw new Error(
            `Invalid unit cost for SKU ${item.sku}.`
          );
        }

        await apiFetch(
          `/purchase-orders/${encodeURIComponent(
            created.purchase_order_id
          )}/items`,
          {
            method: "POST",
            body: JSON.stringify({
              sku: item.sku.trim(),
              ordered_quantity: quantity,
              unit_cost: unitCost.toFixed(2),
              tax_rate: taxRate.toFixed(2),
            }),
          }
        );
      }

      setShowCreate(false);
      setSupplierId("");
      setLocationId("");
      setExpectedDelivery("");
      setNotes("");
      setDraftItems([
        {
          sku: "",
          ordered_quantity: "1",
          unit_cost: "",
          tax_rate: "0",
        },
      ]);

      await loadData();

      const refreshed = await apiFetch<PurchaseOrder>(
        `/purchase-orders/${encodeURIComponent(
          created.purchase_order_id
        )}`
      );

      await openOrder(refreshed);
    } catch (err) {
      setActionError(
        err instanceof Error
          ? err.message
          : "Unable to create purchase order."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function receiveItem(item: PurchaseItem) {
    if (!selectedOrder) return;

    const remaining =
      item.ordered_quantity -
      item.received_quantity;

    if (remaining <= 0) {
      return;
    }

    const input = window.prompt(
      `Receive quantity for ${item.sku || item.product_name}. Remaining: ${remaining}`,
      String(remaining)
    );

    if (input === null) return;

    const quantity = Number(input);

    if (
      !Number.isInteger(quantity) ||
      quantity <= 0 ||
      quantity > remaining
    ) {
      setActionError(
        `Enter a whole number between 1 and ${remaining}.`
      );
      return;
    }

    try {
      setActionLoading(true);
      setActionError("");

      await apiFetch<PurchaseItem>(
        `/purchase-orders/${encodeURIComponent(
          selectedOrder.purchase_order_id
        )}/items/${encodeURIComponent(
          item.id
        )}/receive`,
        {
          method: "POST",
          body: JSON.stringify({
            received_quantity: quantity,
          }),
        }
      );

      await loadData();

      const refreshed = await apiFetch<PurchaseOrder>(
        `/purchase-orders/${encodeURIComponent(
          selectedOrder.purchase_order_id
        )}`
      );

      setSelectedOrder(refreshed);
      await loadItems(refreshed);
    } catch (err) {
      setActionError(
        err instanceof Error
          ? err.message
          : "Unable to receive purchase item."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function updateStatus(newStatus: string) {
    if (!selectedOrder) return;

    try {
      setActionLoading(true);
      setActionError("");

      const updated =
        await apiFetch<PurchaseOrder>(
          `/purchase-orders/${encodeURIComponent(
            selectedOrder.purchase_order_id
          )}/status?new_status=${encodeURIComponent(
            newStatus
          )}`,
          {
            method: "PATCH",
          }
        );

      setOrders((current) =>
        current.map((order) =>
          order.id === updated.id
            ? updated
            : order
        )
      );

      setSelectedOrder(updated);
    } catch (err) {
      setActionError(
        err instanceof Error
          ? err.message
          : "Unable to update purchase order."
      );
    } finally {
      setActionLoading(false);
    }
  }

  return (
    <section className="dashboard retailer-purchases-page">
      <div className="admin-payments-header">
        <div>
          <div className="page-eyebrow">
            <span>RETAILER MANAGEMENT</span>
          </div>

          <h1>Purchases</h1>

          <p>
            Create purchase orders, track deliveries
            and receive inventory.
          </p>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <button
            type="button"
            className="secondary-button"
            onClick={loadData}
            disabled={loading}
          >
            <RefreshCw size={14} />
            Refresh
          </button>

          <button
            type="button"
            className="primary-button"
            onClick={() => {
              setActionError("");
              setShowCreate(true);
            }}
          >
            <Plus size={14} />
            New Purchase
          </button>
        </div>
      </div>

      <div className="payment-stats-grid">
        <MiniStat
          icon={<ShoppingCart />}
          title="Total Orders"
          value={orders.length}
          tone="blue"
        />

        <MiniStat
          icon={<Clock />}
          title="Pending"
          value={pendingCount}
          tone="yellow"
        />

        <MiniStat
          icon={<CheckCircle />}
          title="Received"
          value={receivedCount}
          tone="green"
        />

        <MiniStat
          icon={<PackageCheck />}
          title="Purchase Value"
          value={formatMoney(totalValue)}
          tone="purple"
        />
      </div>

      <div className="payments-panel">
        <div className="payments-panel-header">
          <div>
            <h3>Purchase Orders</h3>

            <span>
              {filteredOrders.length} of{" "}
              {orders.length} orders
            </span>
          </div>

          <div className="payments-toolbar">
            <div className="payments-search">
              <Search size={16} />

              <input
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search purchases..."
              />
            </div>

            <select
              value={status}
              onChange={(event) =>
                setStatus(event.target.value)
              }
            >
              <option value="all">
                All Status
              </option>
              <option value="draft">Draft</option>
              <option value="pending">Pending</option>
              <option value="ordered">Ordered</option>
              <option value="partially_received">
                Partially Received
              </option>
              <option value="received">Received</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        {loading && (
          <div className="table-state">
            Loading purchases...
          </div>
        )}

        {!loading && error && (
          <div className="table-state negative">
            {error}
          </div>
        )}

        {!loading &&
          !error &&
          filteredOrders.length === 0 && (
            <div className="table-state">
              No purchase orders found.
            </div>
          )}

        {!loading &&
          !error &&
          filteredOrders.length > 0 && (
            <div className="payments-table-wrap">
              <table className="payments-table">
                <thead>
                  <tr>
                    <th>Purchase Order</th>
                    <th>Supplier</th>
                    <th>Total</th>
                    <th>Status</th>
                    <th>Expected Delivery</th>
                    <th>Received</th>
                    <th>Created</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredOrders.map((order) => (
                    <tr
                      key={order.id}
                      onClick={() =>
                        openOrder(order)
                      }
                    >
                      <td>
                        <div className="payment-cell">
                          <div className="payment-avatar">
                            <ShoppingCart size={15} />
                          </div>

                          <div>
                            <strong>
                              {order.purchase_order_id}
                            </strong>

                            <small>
                              {locationName(
                                order.location_id
                              )}
                            </small>
                          </div>
                        </div>
                      </td>

                      <td>
                        {supplierName(
                          order.supplier_id
                        )}
                      </td>

                      <td>
                        {formatMoney(
                          order.total_amount
                        )}
                      </td>

                      <td>
                        <span
                          className={`status-badge ${order.status}`}
                        >
                          {order.status.replace(
                            /_/g,
                            " "
                          )}
                        </span>
                      </td>

                      <td>
                        {formatDate(
                          order.expected_delivery_date
                        )}
                      </td>

                      <td>
                        {formatDate(
                          order.received_at
                        )}
                      </td>

                      <td>
                        {formatDate(order.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </div>

      {selectedOrder && (
        <div
          className="modal-backdrop"
          onClick={() =>
            setSelectedOrder(null)
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
                <h2>Purchase Order</h2>

                <p>
                  {selectedOrder.purchase_order_id}
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() =>
                  setSelectedOrder(null)
                }
              >
                <X size={17} />
              </button>
            </div>

            {actionError && (
              <div className="login-error">
                {actionError}
              </div>
            )}

            <div className="user-details-grid">
              <div className="detail">
                <span className="detail-label">
                  Purchase Order
                </span>

                <span className="detail-value">
                  {selectedOrder.purchase_order_id}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Supplier
                </span>

                <span className="detail-value">
                  {supplierName(
                    selectedOrder.supplier_id
                  )}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Location
                </span>

                <span className="detail-value">
                  {locationName(
                    selectedOrder.location_id
                  )}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Status
                </span>

                <span className="detail-value">
                  {selectedOrder.status}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Subtotal
                </span>

                <span className="detail-value">
                  {formatMoney(
                    selectedOrder.subtotal
                  )}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Tax
                </span>

                <span className="detail-value">
                  {formatMoney(
                    selectedOrder.tax_amount
                  )}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Total
                </span>

                <span className="detail-value">
                  {formatMoney(
                    selectedOrder.total_amount
                  )}
                </span>
              </div>

              <div className="detail">
                <span className="detail-label">
                  Expected Delivery
                </span>

                <span className="detail-value">
                  {formatDate(
                    selectedOrder.expected_delivery_date
                  )}
                </span>
              </div>
            </div>

            <div className="roles-section">
              <h3>Items</h3>

              {itemsLoading ? (
                <div className="table-state">
                  Loading items...
                </div>
              ) : selectedItems.length === 0 ? (
                <div className="table-state">
                  No items in this purchase order.
                </div>
              ) : (
                <div className="payments-table-wrap">
                  <table className="payments-table">
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>SKU</th>
                        <th>Ordered</th>
                        <th>Received</th>
                        <th>Unit Cost</th>
                        <th>Total</th>
                        <th />
                      </tr>
                    </thead>

                    <tbody>
                      {selectedItems.map((item) => {
                        const remaining =
                          item.ordered_quantity -
                          item.received_quantity;

                        return (
                          <tr key={item.id}>
                            <td>
                              {item.product_name}
                            </td>

                            <td>
                              {item.sku || "—"}
                            </td>

                            <td>
                              {item.ordered_quantity}
                            </td>

                            <td>
                              {item.received_quantity}
                            </td>

                            <td>
                              {formatMoney(
                                item.unit_cost
                              )}
                            </td>

                            <td>
                              {formatMoney(
                                item.line_total
                              )}
                            </td>

                            <td>
                              {remaining > 0 && (
                                <button
                                  type="button"
                                  className="secondary-button"
                                  onClick={() =>
                                    receiveItem(item)
                                  }
                                  disabled={
                                    actionLoading
                                  }
                                >
                                  Receive
                                </button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="roles-section">
              <h3>Order Actions</h3>

              <div
                style={{
                  display: "flex",
                  gap: 8,
                  flexWrap: "wrap",
                }}
              >
                {selectedOrder.status !==
                  "received" &&
                  selectedOrder.status !==
                    "cancelled" && (
                    <>
                      <button
                        type="button"
                        className="primary-button"
                        onClick={() =>
                          updateStatus("ordered")
                        }
                        disabled={actionLoading}
                      >
                        Mark Ordered
                      </button>

                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() =>
                          updateStatus("cancelled")
                        }
                        disabled={actionLoading}
                      >
                        <XCircle size={14} />
                        Cancel Order
                      </button>
                    </>
                  )}
              </div>
            </div>
          </div>
        </div>
      )}

      {showCreate && (
        <div
          className="modal-backdrop"
          onClick={() =>
            setShowCreate(false)
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
                <h2>New Purchase Order</h2>

                <p>
                  Create a purchase order for your
                  retailer inventory.
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

            {actionError && (
              <div className="login-error">
                {actionError}
              </div>
            )}

            <div className="form-group">
              <label>
                Supplier
                <select
                  value={supplierId}
                  onChange={(event) =>
                    setSupplierId(
                      event.target.value
                    )
                  }
                >
                  <option value="">
                    Select supplier
                  </option>

                  {suppliers
                    .filter(
                      (supplier) =>
                        supplier.is_active
                    )
                    .map((supplier) => (
                      <option
                        key={supplier.supplier_id}
                        value={
                          supplier.supplier_id
                        }
                      >
                        {supplier.name} (
                        {supplier.supplier_id})
                      </option>
                    ))}
                </select>
              </label>

              <label>
                Inventory Location
                <select
                  value={locationId}
                  onChange={(event) =>
                    setLocationId(
                      event.target.value
                    )
                  }
                >
                  <option value="">
                    Select location
                  </option>

                  {locations
                    .filter(
                      (location) =>
                        location.is_active
                    )
                    .map((location) => (
                      <option
                        key={location.id}
                        value={location.id}
                      >
                        {location.name}
                      </option>
                    ))}
                </select>
              </label>

              <label>
                Expected Delivery
                <input
                  type="datetime-local"
                  value={expectedDelivery}
                  onChange={(event) =>
                    setExpectedDelivery(
                      event.target.value
                    )
                  }
                />
              </label>

              <label>
                Notes
                <textarea
                  rows={3}
                  value={notes}
                  onChange={(event) =>
                    setNotes(event.target.value)
                  }
                  placeholder="Optional notes"
                />
              </label>
            </div>

            <div className="roles-section">
              <h3>Products</h3>

              {draftItems.map((item, index) => (
                <div
                  key={index}
                  style={{
                    display: "grid",
                    gridTemplateColumns:
                      "2fr 1fr 1fr 1fr auto",
                    gap: 8,
                    marginBottom: 8,
                    alignItems: "end",
                  }}
                >
                  <label>
                    SKU
                    <input
                      list="purchase-product-skus"
                      value={item.sku}
                      onChange={(event) =>
                        updateDraftItem(
                          index,
                          "sku",
                          event.target.value
                        )
                      }
                      placeholder="Product SKU"
                    />
                  </label>

                  <label>
                    Quantity
                    <input
                      type="number"
                      min="1"
                      value={
                        item.ordered_quantity
                      }
                      onChange={(event) =>
                        updateDraftItem(
                          index,
                          "ordered_quantity",
                          event.target.value
                        )
                      }
                    />
                  </label>

                  <label>
                    Unit Cost
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={item.unit_cost}
                      onChange={(event) =>
                        updateDraftItem(
                          index,
                          "unit_cost",
                          event.target.value
                        )
                      }
                      placeholder="0.00"
                    />
                  </label>

                  <label>
                    Tax %
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={item.tax_rate}
                      onChange={(event) =>
                        updateDraftItem(
                          index,
                          "tax_rate",
                          event.target.value
                        )
                      }
                    />
                  </label>

                  <button
                    type="button"
                    className="icon-button"
                    onClick={() =>
                      removeDraftItem(index)
                    }
                    disabled={
                      draftItems.length === 1
                    }
                  >
                    <X size={15} />
                  </button>
                </div>
              ))}

              <datalist id="purchase-product-skus">
                {variants
                  .filter(
                    (variant) =>
                      variant.status === "active"
                  )
                  .map((variant) => (
                    <option
                      key={variant.id}
                      value={variant.sku}
                    >
                      {variant.variant_name}
                    </option>
                  ))}
              </datalist>

              <button
                type="button"
                className="secondary-button"
                onClick={addDraftItem}
              >
                <Plus size={14} />
                Add Product
              </button>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  setShowCreate(false)
                }
              >
                Cancel
              </button>

              <button
                type="button"
                className="primary-button"
                onClick={createOrder}
                disabled={actionLoading}
              >
                <ShoppingCart size={14} />
                {actionLoading
                  ? "Creating..."
                  : "Create Purchase Order"}
              </button>
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
  value: string | number;
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
