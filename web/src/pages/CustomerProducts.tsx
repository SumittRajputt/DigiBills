import { useEffect, useState } from "react";
import {
  Eye,
  Package,
  RefreshCw,
  ShieldCheck,
  Upload,
} from "lucide-react";
import { apiFetch } from "../api";

type CustomerProduct = {
  product_name: string;
  brand: string | null;
  category: string | null;
  description: string | null;

  ownership_id: string | null;
  product_unit_id: string | null;
  product_variant_id: string | null;
  product_id: string | null;

  product_code: string | null;
  variant_name: string | null;
  sku: string | null;
  barcode: string | null;
  serial_number: string | null;
  product_unit_status: string | null;

  ownership_status: string;
  acquired_at: string;
  released_at: string | null;

  source: string;

  invoice_id: string | null;
  invoice_date: string | null;
  invoice_number: string | null;

  digibill_id: string | null;
  uploaded_bill_id: string | null;
  model_number: string | null;
  quantity: number | null;
  unit_price: number | null;
  total_amount: number | null;

  transfer_eligible: boolean;
  transfer_status: string | null;
  transfer_reason: string | null;
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

function formatCurrency(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(value);
}

function label(value: string | null | undefined) {
  if (!value) return "—";

  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function isUploadedBill(product: CustomerProduct) {
  return product.source === "uploaded_bill";
}

function transferLabel(product: CustomerProduct) {
  if (product.transfer_status === "eligible") {
    return "Eligible";
  }

  if (product.transfer_status === "eligible_for_verification") {
    return "Verification Required";
  }

  if (product.transfer_status === "verification_required") {
    return "Verification Required";
  }

  return product.transfer_eligible ? "Eligible" : "Not Available";
}

export default function CustomerProducts() {
  const [products, setProducts] = useState<CustomerProduct[]>([]);
  const [selectedProduct, setSelectedProduct] =
    useState<CustomerProduct | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadProducts() {
    try {
      setLoading(true);
      setError("");

      const result = await apiFetch<CustomerProduct[]>(
        "/customer/products"
      );

      setProducts(Array.isArray(result) ? result : []);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load your products."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProducts();
  }, []);

  const uploadedProducts = products.filter(isUploadedBill);

  const registeredProducts = products.filter(
    (product) => !isUploadedBill(product)
  );

  const activeOwnerships = products.filter(
    (product) => product.ownership_status === "active"
  ).length;

  const serialisedProducts = products.filter(
    (product) => Boolean(product.serial_number)
  ).length;

  const categories = new Set(
    products
      .map((product) => product.category)
      .filter(Boolean)
  ).size;

  return (
    <section className="dashboard customer-dashboard-page customer-products-page">
      <div className="page-heading customer-products-heading">
        <div>
          <span className="page-eyebrow">
            DIGITAL PRODUCT LOCKER
          </span>

          <h1>My Products</h1>

          <p>
            Products connected to your DigiBills account,
            including registered products and products from
            uploaded bills.
          </p>
        </div>

        <button
          className="secondary-button"
          type="button"
          onClick={loadProducts}
          disabled={loading}
        >
          <RefreshCw
            size={15}
            className={loading ? "spin" : ""}
          />
          Refresh
        </button>
      </div>

      <div className="stats-grid four customer-product-stats">
        <div className="stat-card">
          <div className="stat-icon blue">
            <Package size={18} />
          </div>

          <div>
            <span>My Products</span>
            <strong>{products.length}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">
            <ShieldCheck size={18} />
          </div>

          <div>
            <span>Active Ownerships</span>
            <strong>{activeOwnerships}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon purple">
            <Package size={18} />
          </div>

          <div>
            <span>Serialised Products</span>
            <strong>{serialisedProducts}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon cyan">
            <Upload size={18} />
          </div>

          <div>
            <span>From Uploaded Bills</span>
            <strong>{uploadedProducts.length}</strong>
          </div>
        </div>
      </div>

      <div className="panel customer-products-panel">
        <div className="panel-header">
          <div>
            <h3>My Products</h3>

            <span>
              {products.length} product
              {products.length === 1 ? "" : "s"} found
            </span>
          </div>
        </div>

        {loading ? (
          <div className="table-state">
            Loading your products...
          </div>
        ) : error ? (
          <div className="table-state negative">
            {error}
          </div>
        ) : products.length === 0 ? (
          <div className="table-state">
            <Package size={22} />

            <div>
              <strong>No products found</strong>

              <p>
                Products connected to your bills or
                registered to your account will appear here.
              </p>
            </div>
          </div>
        ) : (
          <div className="customer-products-list">
            {products.map((product) => (
              <div
                className="customer-product-card"
                key={
                  product.ownership_id ||
                  `${product.digibill_id}-${product.product_name}`
                }
              >
                <div className="customer-product-card-main">
                  <div className="customer-product-icon">
                    <Package size={20} />
                  </div>

                  <div className="customer-product-card-info">
                    <div className="customer-product-title-row">
                      <h4>{product.product_name}</h4>

                      <span
                        className={`customer-product-source ${
                          isUploadedBill(product)
                            ? "uploaded"
                            : "registered"
                        }`}
                      >
                        {isUploadedBill(product)
                          ? "Uploaded Bill"
                          : "Registered"}
                      </span>
                    </div>

                    <div className="customer-product-meta">
                      {product.brand && (
                        <span>
                          Brand: <strong>{product.brand}</strong>
                        </span>
                      )}

                      {product.model_number && (
                        <span>
                          Model:{" "}
                          <strong>{product.model_number}</strong>
                        </span>
                      )}

                      {product.variant_name && (
                        <span>
                          Variant:{" "}
                          <strong>{product.variant_name}</strong>
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="customer-product-card-details">
                  <div>
                    <small>
                      {isUploadedBill(product)
                        ? "Bill"
                        : "Purchase Date"}
                    </small>

                    <strong>
                      {isUploadedBill(product)
                        ? product.invoice_number || "—"
                        : formatDate(product.invoice_date)}
                    </strong>
                  </div>

                  <div>
                    <small>Purchase Date</small>

                    <strong>
                      {formatDate(
                        product.invoice_date ||
                          product.acquired_at
                      )}
                    </strong>
                  </div>

                  <div>
                    <small>Amount</small>

                    <strong>
                      {formatCurrency(product.total_amount)}
                    </strong>
                  </div>

                  <div>
                    <small>Transfer</small>

                    <span
                      className={`customer-product-transfer ${
                        product.transfer_eligible
                          ? "eligible"
                          : "verification"
                      }`}
                    >
                      {transferLabel(product)}
                    </span>
                  </div>
                </div>

                <button
                  className="table-action-button customer-product-view-button"
                  type="button"
                  title="View product"
                  onClick={() =>
                    setSelectedProduct(product)
                  }
                >
                  <Eye size={15} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {registeredProducts.length > 0 &&
        uploadedProducts.length > 0 && (
          <div className="customer-products-note">
            <ShieldCheck size={17} />

            <div>
              <strong>
                Your products come from two sources
              </strong>

              <p>
                Registered products are linked to DigiBills
                product ownership records. Products from
                uploaded bills remain bill-based unless they
                have enough information to establish a
                registered product identity.
              </p>
            </div>
          </div>
        )}

      {selectedProduct && (
        <div
          className="customer-product-modal-backdrop"
          onClick={() => setSelectedProduct(null)}
        >
          <div
            className="customer-product-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="customer-product-modal-header">
              <div>
                <span className="page-eyebrow">
                  {isUploadedBill(selectedProduct)
                    ? "UPLOADED BILL PRODUCT"
                    : "REGISTERED PRODUCT"}
                </span>

                <h2>{selectedProduct.product_name}</h2>
              </div>

              <button
                className="table-action-button"
                type="button"
                onClick={() => setSelectedProduct(null)}
              >
                ×
              </button>
            </div>

            <div className="customer-product-detail-grid">
              <div>
                <small>Product</small>
                <strong>
                  {selectedProduct.product_name}
                </strong>
              </div>

              <div>
                <small>Brand</small>
                <strong>
                  {selectedProduct.brand || "—"}
                </strong>
              </div>

              <div>
                <small>Model</small>
                <strong>
                  {selectedProduct.model_number || "—"}
                </strong>
              </div>

              <div>
                <small>Category</small>
                <strong>
                  {selectedProduct.category || "—"}
                </strong>
              </div>

              {selectedProduct.variant_name && (
                <div>
                  <small>Variant</small>
                  <strong>
                    {selectedProduct.variant_name}
                  </strong>
                </div>
              )}

              {selectedProduct.sku && (
                <div>
                  <small>SKU</small>
                  <strong>{selectedProduct.sku}</strong>
                </div>
              )}

              {selectedProduct.barcode && (
                <div>
                  <small>Barcode</small>
                  <strong>
                    {selectedProduct.barcode}
                  </strong>
                </div>
              )}

              {selectedProduct.serial_number && (
                <div>
                  <small>Serial Number</small>
                  <strong>
                    {selectedProduct.serial_number}
                  </strong>
                </div>
              )}

              {selectedProduct.invoice_number && (
                <div>
                  <small>Bill Number</small>
                  <strong>
                    {selectedProduct.invoice_number}
                  </strong>
                </div>
              )}

              <div>
                <small>Purchase Date</small>
                <strong>
                  {formatDate(
                    selectedProduct.invoice_date ||
                      selectedProduct.acquired_at
                  )}
                </strong>
              </div>

              {selectedProduct.quantity !== null && (
                <div>
                  <small>Quantity</small>
                  <strong>
                    {selectedProduct.quantity}
                  </strong>
                </div>
              )}

              {selectedProduct.total_amount !== null && (
                <div>
                  <small>Purchase Amount</small>
                  <strong>
                    {formatCurrency(
                      selectedProduct.total_amount
                    )}
                  </strong>
                </div>
              )}

              <div>
                <small>
                  {isUploadedBill(selectedProduct)
                    ? "Bill Association"
                    : "Ownership"}
                </small>

                <span className="customer-product-transfer eligible">
                  {isUploadedBill(selectedProduct)
                    ? "Confirmed"
                    : label(
                        selectedProduct.ownership_status
                      )}
                </span>
              </div>

              <div>
                <small>Source</small>
                <strong>
                  {isUploadedBill(selectedProduct)
                    ? "Uploaded Bill"
                    : "Registered Product"}
                </strong>
              </div>

              <div>
                <small>Transfer Status</small>

                <span
                  className={`customer-product-transfer ${
                    selectedProduct.transfer_eligible
                      ? "eligible"
                      : "verification"
                  }`}
                >
                  {transferLabel(selectedProduct)}
                </span>
              </div>

              {selectedProduct.transfer_reason && (
                <div className="customer-product-detail-full">
                  <small>Transfer Information</small>
                  <strong>
                    {selectedProduct.transfer_reason}
                  </strong>
                </div>
              )}

              {selectedProduct.description && (
                <div className="customer-product-detail-full">
                  <small>Description</small>
                  <strong>
                    {selectedProduct.description}
                  </strong>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
