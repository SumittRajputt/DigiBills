import { Search, Package, CheckCircle, XCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../api";

type Product = {
  id: string;
  product_code: string;
  name: string;
  brand: string | null;
  category: string | null;
  description: string | null;
  is_transferable: boolean;
  status: string;
  created_at: string;
  updated_at: string;
};

export default function AdminProducts() {
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedProduct, setSelectedProduct] =
    useState<Product | null>(null);

  async function loadProducts() {
    try {
      setLoading(true);
      setError("");

      const result = await apiFetch<Product[]>("/products");
      setProducts(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load products."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProducts();
  }, []);

  const filteredProducts = useMemo(() => {
    const query = search.toLowerCase().trim();

    return products.filter((product) => {
      const matchesSearch =
        !query ||
        product.name.toLowerCase().includes(query) ||
        product.product_code.toLowerCase().includes(query) ||
        (product.brand || "")
          .toLowerCase()
          .includes(query) ||
        (product.category || "")
          .toLowerCase()
          .includes(query);

      const matchesStatus =
        status === "all" ||
        product.status.toLowerCase() === status;

      return matchesSearch && matchesStatus;
    });
  }, [products, search, status]);

  const counts = {
    all: products.length,
    active: products.filter(
      (product) => product.status === "active"
    ).length,
    inactive: products.filter(
      (product) => product.status === "inactive"
    ).length,
  };

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
    <section className="dashboard admin-products-page">
      <div className="admin-products-header">
        <div>
          <div className="page-eyebrow">
            <span>ADMINISTRATION</span>
          </div>
          <h1>Products</h1>
          <p>
            Manage product catalog, status and transfer settings across DigiBills.
          </p>
        </div>
      </div>

      <div className="product-stats-grid">
        <MiniStat
          icon={<Package />}
          title="Total Products"
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
          icon={<XCircle />}
          title="Inactive"
          value={counts.inactive}
          tone="red"
        />
      </div>

      <div className="products-panel">
        <div className="products-panel-header">
          <div>
            <h3>Product Directory</h3>
            <span>
              {filteredProducts.length} of {products.length} products
            </span>
          </div>

          <div className="products-toolbar">
            <div className="products-search">
              <Search size={16} />

              <input
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search products..."
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
            Loading products...
          </div>
        )}

        {!loading && error && (
          <div className="table-state negative">
            {error}
          </div>
        )}

        {!loading &&
          !error &&
          filteredProducts.length === 0 && (
            <div className="table-state">
              No products found.
            </div>
          )}

        {!loading &&
          !error &&
          filteredProducts.length > 0 && (
            <div className="products-table-wrap">
              <table className="products-table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Brand</th>
                    <th>Category</th>
                    <th>Status</th>
                    <th>Transferable</th>
                    <th>Created</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredProducts.map((product) => (
                    <tr
                      key={product.id}
                      onClick={() =>
                        setSelectedProduct(product)
                      }
                      style={{ cursor: "pointer" }}
                    >
                      <td>
                        <div className="product-cell">
                          <div className="product-avatar">
                            {product.name
                              .charAt(0)
                              .toUpperCase()}
                          </div>

                          <div>
                            <strong>
                              {product.name}
                            </strong>

                            <small>
                              {product.product_code}
                            </small>
                          </div>
                        </div>
                      </td>

                      <td>
                        {product.brand || "—"}
                      </td>

                      <td>
                        {product.category || "—"}
                      </td>

                      <td>
                        <span
                          className={`status-badge ${product.status}`}
                        >
                          {product.status}
                        </span>
                      </td>

                      <td>
                        <span
                          className={
                            product.is_transferable
                              ? "verified"
                              : "not-verified"
                          }
                        >
                          {product.is_transferable
                            ? "Yes"
                            : "No"}
                        </span>
                      </td>

                      <td>
                        {formatDate(
                          product.created_at
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </div>

      {selectedProduct && (
        <div
          className="modal-backdrop"
          onClick={() =>
            setSelectedProduct(null)
          }
        >
          <div
            className="product-details-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="modal-header">
              <div>
                <h2>Product Details</h2>
                <p>
                  Product information registered
                  on DigiBills.
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() =>
                  setSelectedProduct(null)
                }
              >
                ×
              </button>
            </div>

            <div className="product-details-content">

              <div className="product-detail-group">
                <div className="product-detail-heading">
                  <span className="section-number">1.</span>
                  <div>
                    <h3>Product Information</h3>
                    <p>Core information registered for this product.</p>
                  </div>
                </div>

                <div className="product-detail-grid">
                  <div className="product-detail-card">
                    <span>Product Name</span>
                    <strong>{selectedProduct.name}</strong>
                  </div>

                  <div className="product-detail-card">
                    <span>Product Code</span>
                    <strong>{selectedProduct.product_code}</strong>
                  </div>

                  <div className="product-detail-card">
                    <span>Brand</span>
                    <strong>{selectedProduct.brand || "—"}</strong>
                  </div>

                  <div className="product-detail-card">
                    <span>Category</span>
                    <strong>{selectedProduct.category || "—"}</strong>
                  </div>
                </div>
              </div>

              <div className="product-detail-group">
                <div className="product-detail-heading">
                  <span className="section-number">2.</span>
                  <div>
                    <h3>Product Status</h3>
                    <p>Current availability and transfer configuration.</p>
                  </div>
                </div>

                <div className="product-detail-grid">
                  <div className="product-detail-card">
                    <span>Status</span>
                    <strong className={`product-status-value ${selectedProduct.status}`}>
                      {selectedProduct.status}
                    </strong>
                  </div>

                  <div className="product-detail-card">
                    <span>Transferable</span>
                    <strong className={selectedProduct.is_transferable ? "product-transfer-yes" : "product-transfer-no"}>
                      {selectedProduct.is_transferable ? "Yes" : "No"}
                    </strong>
                  </div>
                </div>
              </div>

              <div className="product-detail-group">
                <div className="product-detail-heading">
                  <span className="section-number">3.</span>
                  <div>
                    <h3>Record Information</h3>
                    <p>Product creation and update history.</p>
                  </div>
                </div>

                <div className="product-detail-grid">
                  <div className="product-detail-card">
                    <span>Created</span>
                    <strong>
                      {formatDate(selectedProduct.created_at)}
                    </strong>
                  </div>

                  <div className="product-detail-card">
                    <span>Last Updated</span>
                    <strong>
                      {formatDate(selectedProduct.updated_at)}
                    </strong>
                  </div>
                </div>
              </div>

              <div className="product-detail-description">
                <span>Description</span>
                <p>
                  {selectedProduct.description || "No description available for this product."}
                </p>
              </div>

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
        <strong>{value}</strong>
      </div>
    </div>
  );
}
