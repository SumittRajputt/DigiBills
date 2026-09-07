import { useEffect, useState } from "react";
import {
  ArrowLeft,
  Eye,
  Package,
  RefreshCw,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api";

type CustomerProduct = {
  ownership_id: string;
  product_unit_id: string;
  product_variant_id: string;
  product_id: string;

  product_name: string;
  product_code: string;
  brand: string | null;
  category: string | null;
  description: string | null;

  variant_name: string;
  sku: string;
  barcode: string | null;

  serial_number: string;
  product_unit_status: string;

  ownership_status: string;
  acquired_at: string;
  released_at: string | null;
  source: string;
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
  return `customer-product-status customer-product-status-${value}`;
}

export default function CustomerProducts() {
  const navigate = useNavigate();

  const [products, setProducts] = useState<
    CustomerProduct[]
  >([]);

  const [selectedProduct, setSelectedProduct] =
    useState<CustomerProduct | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadProducts() {
    try {
      setLoading(true);
      setError("");

      const result =
        await apiFetch<CustomerProduct[]>(
          "/customer/products"
        );

      setProducts(result);
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

  return (
    <section className="dashboard customer-dashboard-page customer-products-page">
      <div className="page-heading customer-products-heading">
        <div>
          <span className="page-eyebrow">
            CUSTOMER ACCOUNT
          </span>

          <h1>My Products</h1>

          <p>
            View products currently registered to your
            account.
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
            <Package size={18} />
          </div>

          <div>
            <span>Active Ownerships</span>
            <strong>
              {
                products.filter(
                  (product) =>
                    product.ownership_status ===
                    "active"
                ).length
              }
            </strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon purple">
            <Package size={18} />
          </div>

          <div>
            <span>Serialised Products</span>
            <strong>
              {
                products.filter(
                  (product) =>
                    Boolean(product.serial_number)
                ).length
              }
            </strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon cyan">
            <Package size={18} />
          </div>

          <div>
            <span>Categories</span>
            <strong>
              {
                new Set(
                  products
                    .map((product) => product.category)
                    .filter(Boolean)
                ).size
              }
            </strong>
          </div>
        </div>
      </div>

      <div className="panel customer-products-panel">
        <div className="panel-header">
          <div>
            <h3>Owned Products</h3>

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
                Products registered to your account
                will appear here.
              </p>
            </div>
          </div>
        ) : (
          <div className="customer-products-table-wrap">
            <table className="data-table customer-products-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Variant</th>
                  <th>SKU</th>
                  <th>Serial Number</th>
                  <th>Acquired</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>

              <tbody>
                {products.map((product) => (
                  <tr key={product.ownership_id}>
                    <td>
                      <strong>
                        {product.product_name}
                      </strong>

                      <small>
                        {product.brand ||
                          product.product_code}
                      </small>
                    </td>

                    <td>
                      {product.variant_name}
                    </td>

                    <td>
                      {product.sku}
                    </td>

                    <td>
                      <strong>
                        {product.serial_number}
                      </strong>
                    </td>

                    <td>
                      {formatDate(product.acquired_at)}
                    </td>

                    <td>
                      <span
                        className={statusClass(
                          product.ownership_status
                        )}
                      >
                        {label(
                          product.ownership_status
                        )}
                      </span>
                    </td>

                    <td>
                      <button
                        className="table-action-button"
                        type="button"
                        title="View product"
                        onClick={() =>
                          setSelectedProduct(product)
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
        className="secondary-button customer-products-back"
        type="button"
        onClick={() =>
          navigate("/customer")
        }
      >
        <ArrowLeft size={15} />
        Back to Dashboard
      </button>

      {selectedProduct && (
        <div
          className="customer-product-modal-backdrop"
          onClick={() =>
            setSelectedProduct(null)
          }
        >
          <div
            className="customer-product-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="customer-product-modal-header">
              <div>
                <span className="page-eyebrow">
                  PRODUCT DETAILS
                </span>

                <h2>
                  {selectedProduct.product_name}
                </h2>
              </div>

              <button
                className="table-action-button"
                type="button"
                onClick={() =>
                  setSelectedProduct(null)
                }
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
                <small>Product Code</small>
                <strong>
                  {selectedProduct.product_code}
                </strong>
              </div>

              <div>
                <small>Brand</small>
                <strong>
                  {selectedProduct.brand || "—"}
                </strong>
              </div>

              <div>
                <small>Category</small>
                <strong>
                  {selectedProduct.category || "—"}
                </strong>
              </div>

              <div>
                <small>Variant</small>
                <strong>
                  {selectedProduct.variant_name}
                </strong>
              </div>

              <div>
                <small>SKU</small>
                <strong>
                  {selectedProduct.sku}
                </strong>
              </div>

              <div>
                <small>Barcode</small>
                <strong>
                  {selectedProduct.barcode || "—"}
                </strong>
              </div>

              <div>
                <small>Serial Number</small>
                <strong>
                  {selectedProduct.serial_number}
                </strong>
              </div>

              <div>
                <small>Product Status</small>
                <strong>
                  {label(
                    selectedProduct.product_unit_status
                  )}
                </strong>
              </div>

              <div>
                <small>Ownership</small>
                <span
                  className={statusClass(
                    selectedProduct.ownership_status
                  )}
                >
                  {label(
                    selectedProduct.ownership_status
                  )}
                </span>
              </div>

              <div>
                <small>Acquired</small>
                <strong>
                  {formatDate(
                    selectedProduct.acquired_at
                  )}
                </strong>
              </div>

              <div>
                <small>Source</small>
                <strong>
                  {label(selectedProduct.source)}
                </strong>
              </div>

              <div className="customer-product-detail-full">
                <small>Description</small>
                <strong>
                  {selectedProduct.description || "—"}
                </strong>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
