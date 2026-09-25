import { useEffect, useState } from "react";
import { ArrowLeft, Download, Eye, Plus } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { apiFetch } from "../api";

type CustomerInvoice = {
  id: string;
  invoice_id: string;
  retailer_id: string;
  employee_id: string | null;
  customer_id: string;
  invoice_number: string | null;
  invoice_date: string | null;
  item_names: string[];
  subtotal: string | number;
  discount_amount: string | number;
  tax_amount: string | number;
  total_amount: string | number;
  payment_status: string;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

type InvoiceItem = {
  id: string;
  invoice_id: string;
  product_variant_id: string;
  product_name: string;
  sku: string | null;
  quantity: number;
  unit_price: string | number;
  unit_cost: string | number;
  discount_amount: string | number;
  tax_rate: string | number;
  taxable_amount: string | number;
  tax_amount: string | number;
  line_total: string | number;
  created_at: string;
};

type CustomerInvoiceDetail = CustomerInvoice & {
  items: InvoiceItem[];
};

type CustomerBillProduct = {
  product_name: string | null;
  brand: string | null;
  model_number: string | null;
  serial_number: string | null;
  quantity: string | number | null;
  unit_price: string | number | null;
  discount: string | number | null;
  tax_amount: string | number | null;
  total_amount: string | number | null;
};

type CustomerBill = {
  source: "retailer" | "uploaded";
  bill_id: string;
  bill_number: string | null;
  bill_date: string | null;
  products: CustomerBillProduct[];
  subtotal: string | number | null;
  discount_amount: string | number | null;
  tax_amount: string | number | null;
  total_amount: string | number;
  payment_status: string;
  status: string;
  retailer_name: string | null;
  uploaded_bill_id: string | null;
  digibill_id: string | null;
  created_at: string;
  updated_at: string;
};

type CustomerDigiBill = {
  digibill_id: string;
  uploaded_bill_id: string;
  customer_id: string;
  invoice_number: string | null;
  invoice_date: string | null;
  retailer: Record<string, unknown>;
  customer: Record<string, unknown>;
  products: CustomerBillProduct[];
  totals: Record<string, unknown>;
  payment: Record<string, unknown>;
  warranty_evidence: Record<string, unknown>;
  confidence_scores: Record<string, unknown>;
  extraction_notes: string[];
  status: string;
  confirmed_at: string;
  created_at: string;
  updated_at: string;
};

type CustomerIdentity = {
  customer_id: string;
  full_name: string;
  phone_number: string;
  email: string | null;
  profile_image_url: string | null;
};

type CustomerWarranty = {
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


function money(value: string | number | null | undefined) {
  const amount = Number(value ?? 0);

  return `₹${amount.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

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

function statusLabel(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function statusClass(value: string) {
  return `customer-invoice-status customer-invoice-status-${value}`;
}

export default function CustomerInvoices() {
  const navigate = useNavigate();
  const { invoiceId, orderId } = useParams();
  const detailReference = orderId || invoiceId;
  const isOrderDetails = Boolean(orderId);

  const [invoices, setInvoices] = useState<CustomerInvoice[]>([]);
  const [detail, setDetail] =
    useState<CustomerInvoiceDetail | null>(null);

  const [digiBillDetail, setDigiBillDetail] =
    useState<CustomerDigiBill | null>(null);

  const [customerIdentity, setCustomerIdentity] =
    useState<CustomerIdentity | null>(null);

  const [customerWarranties, setCustomerWarranties] =
    useState<CustomerWarranty[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [invoiceSearch, setInvoiceSearch] = useState("");
  const [invoiceStatus, setInvoiceStatus] = useState("all");

  async function loadCustomerWarranties() {
    try {
      const result =
        await apiFetch<CustomerWarranty[]>(
          "/customer/warranty"
        );

      setCustomerWarranties(result);
    } catch {
      setCustomerWarranties([]);
    }
  }

  async function loadInvoices() {
    try {
      setLoading(true);
      setError("");

      const result =
        await apiFetch<CustomerBill[]>(
          "/customer/bills"
        );

      setInvoices(
        result.map((bill) => ({
          id: bill.bill_id,
          invoice_id: bill.bill_id,
          retailer_id: "",
          employee_id: null,
          customer_id: "",
          invoice_number: bill.bill_number,
          invoice_date: bill.bill_date,
          item_names: bill.products
            .map((product) => product.product_name)
            .filter(
              (name): name is string =>
                Boolean(name)
            ),
          subtotal: bill.subtotal ?? "0",
          discount_amount:
            bill.discount_amount ?? "0",
          tax_amount: bill.tax_amount ?? "0",
          total_amount: bill.total_amount,
          payment_status: bill.payment_status,
          status: bill.status,
          notes: null,
          created_at: bill.created_at,
          updated_at: bill.updated_at,
        }))
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load your bills."
      );
    } finally {
      setLoading(false);
    }
  }

  async function downloadUploadedBill(
    uploadedBillId: string,
    filename: string
  ) {
    const token = sessionStorage.getItem("digibills_token");

    if (!token) {
      navigate("/login/customer");
      return;
    }

    try {
      setError("");

      const apiBase =
        import.meta.env.VITE_API_BASE_URL ??
        "http://localhost:8000";

      const response = await fetch(
        `${apiBase}/customer/uploaded-bills/${encodeURIComponent(
          uploadedBillId
        )}/download`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        sessionStorage.removeItem("digibills_token");
        navigate("/login/customer");
        return;
      }

      if (!response.ok) {
        throw new Error(
          (await response.text()) || "Failed to download bill."
        );
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = url;
      link.download = filename || `${uploadedBillId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();

      URL.revokeObjectURL(url);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to download bill."
      );
    }
  }

  function openInvoicePdf(invoiceId: string) {
    const token = sessionStorage.getItem("digibills_token");

    if (!token) {
      navigate("/login/customer");
      return;
    }

    const apiBase =
      import.meta.env.VITE_API_BASE_URL ??
      "http://localhost:8000";

    const url =
      `${apiBase}/customer/invoices/` +
      `${encodeURIComponent(invoiceId)}/pdf`;

    const pdfWindow = window.open("", "_blank");

    if (!pdfWindow) {
      setError(
        "Unable to open the invoice PDF. Please allow pop-ups for DigiBills."
      );
      return;
    }

    fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then(async (response) => {
        if (!response.ok) {
          const body = await response.text();
          throw new Error(
            body || `Unable to generate invoice PDF (${response.status}).`
          );
        }

        return response.blob();
      })
      .then((blob) => {
        const pdfUrl = URL.createObjectURL(blob);

        pdfWindow.location.href = pdfUrl;

        window.setTimeout(() => {
          URL.revokeObjectURL(pdfUrl);
        }, 60_000);
      })
      .catch((err) => {
        pdfWindow.close();

        setError(
          err instanceof Error
            ? err.message
            : "Unable to open invoice PDF."
        );
      });
  }

  async function loadInvoiceDetail() {
    if (!detailReference) return;

    try {
      setLoading(true);
      setError("");
      setDetail(null);
      setDigiBillDetail(null);
      setCustomerWarranties([]);

      const [customerResult, warrantyResult] =
        await Promise.all([
          apiFetch<CustomerIdentity>("/customers/me"),
          apiFetch<CustomerWarranty[]>("/customer/warranty"),
        ]);

      setCustomerIdentity(customerResult);
      setCustomerWarranties(warrantyResult);

      try {
        const result =
          await apiFetch<CustomerInvoiceDetail>(
            `/customer/invoices/${encodeURIComponent(
              detailReference
            )}`
          );

        setDetail(result);
        return;
      } catch {
        const digiBill =
          await apiFetch<CustomerDigiBill>(
            `/customer/bills/${encodeURIComponent(
              detailReference
            )}`
          );

        setDigiBillDetail(digiBill);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load bill details."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (detailReference) {
      loadInvoiceDetail();
    } else {
      loadInvoices();
    }
  }, [detailReference]);

  const billWarranty = detail
    ? customerWarranties.find(
        (warranty) =>
          warranty.invoice_id === detail.invoice_id ||
          warranty.invoice_id === detail.id
      ) || null
    : null;

  const filteredInvoices = invoices.filter((invoice) => {
    const search = invoiceSearch.trim().toLowerCase();

    const matchesSearch =
      !search ||
      (invoice.invoice_number || "").toLowerCase().includes(search) ||
      (invoice.invoice_id || "").toLowerCase().includes(search) ||
      (invoice.item_names || [])
        .join(" ")
        .toLowerCase()
        .includes(search);

    const matchesStatus =
      invoiceStatus === "all" ||
      invoice.payment_status?.toLowerCase() === invoiceStatus;

    return matchesSearch && matchesStatus;
  });

  if (detailReference) {
    if (loading) {
      return (
        <section className="dashboard customer-dashboard-page">
          <div className="page-heading">
            
            <h1>
              {"Bill Details"}
            </h1>
            <p>
              {isOrderDetails
                ? "Loading purchase details..."
                : "Loading invoice..."}
            </p>
          </div>
        </section>
      );
    }

    if (error) {
      return (
        <section className="dashboard customer-dashboard-page">
          <div className="page-heading">
            
            <h1>
              {"Bill Details"}
            </h1>
            <p>{error}</p>
          </div>

          <div className="panel">
            <div style={{ padding: "32px" }}>
              <button
                className="secondary-button"
                type="button"
                onClick={() =>
                  navigate("/customer/invoices")
                }
              >
                <ArrowLeft size={16} />
                Back to My Bills
              </button>
            </div>
          </div>
        </section>
      );
    }

    if (digiBillDetail) {
      const totals = digiBillDetail.totals || {};
      const payment = digiBillDetail.payment || {};
      const warranty = digiBillDetail.warranty_evidence || {};

      const warrantyFinal =
        typeof warranty.final === "object" &&
        warranty.final !== null
          ? (warranty.final as Record<string, unknown>)
          : {};

      const hasWarranty =
        warrantyFinal.has_warranty === "yes";

      const billNumber =
        digiBillDetail.invoice_number ||
        digiBillDetail.digibill_id;

      const paymentStatus = String(
        payment.payment_status ||
          digiBillDetail.status ||
          ""
      );

      return (
        <section className="dashboard customer-dashboard-page customer-order-details-page">
          <div
            className="page-heading"
            style={{
              display: "flex",
              alignItems: "flex-end",
              justifyContent: "space-between",
              gap: "20px",
            }}
          >
            <div>
              <h1>Bill Details</h1>
              <p>Your purchase and bill details</p>
            </div>

            <div
              style={{
                display: "flex",
                gap: "10px",
                alignItems: "center",
                flexWrap: "wrap",
              }}
            >
              {digiBillDetail.uploaded_bill_id && (
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() =>
                    downloadUploadedBill(
                      digiBillDetail.uploaded_bill_id!,
                      `${billNumber}.pdf`
                    )
                  }
                >
                  <Download size={16} />
                  Download Bill
                </button>
              )}

              <button
                className="secondary-button"
                type="button"
                onClick={() =>
                  navigate("/customer/invoices")
                }
              >
                <ArrowLeft size={16} />
                Back to My Bills
              </button>
            </div>
          </div>

          {/* Bill identity */}
          <div className="panel">
            <div
              style={{
                padding: "24px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: "20px",
                flexWrap: "wrap",
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: "12px",
                    fontWeight: 700,
                    color: "#64748b",
                    marginBottom: "6px",
                  }}
                >
                  BILL
                </div>

                <h2
                  style={{
                    margin: 0,
                    fontSize: "26px",
                  }}
                >
                  {billNumber}
                </h2>

                <div
                  style={{
                    marginTop: "8px",
                    color: "#64748b",
                  }}
                >
                  Purchase date:{" "}
                  <strong>
                    {formatDate(
                      digiBillDetail.invoice_date
                    )}
                  </strong>
                </div>
              </div>

              <span className={statusClass(paymentStatus)}>
                {["paid", "completed", "captured"].includes(
                  paymentStatus.toLowerCase()
                )
                  ? "✓ Payment Completed"
                  : statusLabel(paymentStatus)}
              </span>
            </div>

            <div
              style={{
                borderTop: "1px solid #e5e7eb",
                padding: "22px 24px",
                display: "grid",
                gridTemplateColumns:
                  "repeat(auto-fit, minmax(180px, 1fr))",
                gap: "18px",
              }}
            >
              <div className="customer-order-detail-field">
                <span className="customer-order-detail-label">
                  Purchase Date
                </span>
                <strong className="customer-order-detail-value">
                  {formatDate(
                    digiBillDetail.invoice_date
                  )}
                </strong>
              </div>

              <div className="customer-order-detail-field">
                <span className="customer-order-detail-label">
                  Bill Number
                </span>
                <strong className="customer-order-detail-value">
                  {billNumber}
                </strong>
              </div>

              <div className="customer-order-detail-field">
                <span className="customer-order-detail-label">
                  Bill Status
                </span>
                <strong className="customer-order-detail-value">
                  {statusLabel(
                    digiBillDetail.status
                  )}
                </strong>
              </div>

              <div className="customer-order-detail-field">
                <span className="customer-order-detail-label">
                  Payment Status
                </span>
                <strong className="customer-order-detail-value">
                  {statusLabel(paymentStatus)}
                </strong>
              </div>
            </div>
          </div>

          {/* Products */}
          <div className="panel">
            <div className="panel-header">
              <div>
                <h3>Products</h3>
                <p>
                  {digiBillDetail.products.length} product
                  {digiBillDetail.products.length === 1
                    ? ""
                    : "s"} in this bill
                </p>
              </div>
            </div>

            <div className="customer-digibill-products">
              {digiBillDetail.products.length === 0 ? (
                <div className="customer-invoice-empty">
                  No product details are available.
                </div>
              ) : (
                digiBillDetail.products.map(
                  (product, index) => (
                    <article
                      key={`${product.product_name || "product"}-${index}`}
                      className="customer-digibill-product"
                    >
                      <div className="customer-digibill-product-main">
                        <span className="customer-order-detail-label">
                          PRODUCT
                        </span>

                        <strong className="customer-order-detail-value">
                          {product.product_name ||
                            "Product"}
                        </strong>

                        {product.brand && (
                          <span className="customer-digibill-product-meta">
                            Brand: {product.brand}
                          </span>
                        )}

                        {product.model_number && (
                          <span className="customer-digibill-product-meta">
                            Model: {product.model_number}
                          </span>
                        )}

                        {product.serial_number && (
                          <span className="customer-digibill-product-meta">
                            Serial: {product.serial_number}
                          </span>
                        )}
                      </div>

                      <div className="customer-digibill-product-price">
                        <span className="customer-order-detail-label">
                          LINE TOTAL
                        </span>

                        <strong className="customer-order-detail-value">
                          {money(
                            product.total_amount
                          )}
                        </strong>

                        {product.quantity != null && (
                          <span className="customer-digibill-product-meta">
                            Quantity:{" "}
                            {String(product.quantity)}
                          </span>
                        )}
                      </div>
                    </article>
                  )
                )
              )}
            </div>
          </div>

          {/* Bill summary */}
          <div className="panel">
            <div className="panel-header">
              <div>
                <h3>Bill Summary</h3>
                <p>Price breakdown</p>
              </div>
            </div>

            <div className="customer-digibill-summary">
              <div className="customer-order-detail-field">
                <span className="customer-order-detail-label">
                  Subtotal
                </span>
                <strong className="customer-order-detail-value">
                  {money(
                    totals.subtotal as
                      | string
                      | number
                  )}
                </strong>
              </div>

              <div className="customer-order-detail-field">
                <span className="customer-order-detail-label">
                  Discount
                </span>
                <strong className="customer-order-detail-value">
                  {money(
                    totals.discount as
                      | string
                      | number
                  )}
                </strong>
              </div>

              <div className="customer-order-detail-field">
                <span className="customer-order-detail-label">
                  Tax
                </span>
                <strong className="customer-order-detail-value">
                  {money(
                    totals.tax_amount as
                      | string
                      | number
                  )}
                </strong>
              </div>

              <div className="customer-digibill-summary-total">
                <span>Total Amount</span>
                <strong>
                  {money(
                    totals.total_amount as
                      | string
                      | number
                  )}
                </strong>
              </div>
            </div>
          </div>

          {/* Payment */}
          <div className="panel">
            <div className="panel-header">
              <div>
                <h3>Payment Details</h3>
                <p>Payment information for this bill</p>
              </div>
            </div>

            <div className="customer-digibill-payment">
              <div className="customer-order-detail-field">
                <span className="customer-order-detail-label">
                  Payment Status
                </span>
                <strong className="customer-order-detail-value">
                  {statusLabel(paymentStatus)}
                </strong>
              </div>

              <div className="customer-order-detail-field">
                <span className="customer-order-detail-label">
                  Payment Method
                </span>
                <strong className="customer-order-detail-value">
                  {String(
                    payment.payment_method || "—"
                  )}
                </strong>
              </div>

              <div className="customer-order-detail-field">
                <span className="customer-order-detail-label">
                  Amount Paid
                </span>
                <strong className="customer-order-detail-value">
                  {money(
                    payment.paid_amount as
                      | string
                      | number
                  )}
                </strong>
              </div>
            </div>
          </div>

          {/* Warranty */}
          {hasWarranty && (
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h3>Warranty Protection</h3>
                  <p>
                    Warranty coverage for this purchase
                  </p>
                </div>
              </div>

              <div className="customer-digibill-warranty">
                <div className="customer-digibill-warranty-status">
                  <strong>Warranty confirmed</strong>
                  <span className="customer-invoice-status customer-invoice-status-paid">
                    Active
                  </span>
                </div>

                <div className="customer-digibill-warranty-grid">
                  {Boolean(warrantyFinal.provider) && (
                    <div className="customer-order-detail-field">
                      <span className="customer-order-detail-label">
                        PROVIDER
                      </span>
                      <strong className="customer-order-detail-value">
                        {String(
                          warrantyFinal.provider
                        )}
                      </strong>
                    </div>
                  )}

                  {Boolean(
                    warrantyFinal.warranty_number
                  ) && (
                    <div className="customer-order-detail-field">
                      <span className="customer-order-detail-label">
                        WARRANTY NUMBER
                      </span>
                      <strong className="customer-order-detail-value">
                        {String(
                          warrantyFinal.warranty_number
                        )}
                      </strong>
                    </div>
                  )}

                  {Boolean(warrantyFinal.warranty_type) && (
                    <div className="customer-order-detail-field">
                      <span className="customer-order-detail-label">
                        WARRANTY TYPE
                      </span>
                      <strong className="customer-order-detail-value">
                        {String(
                          warrantyFinal.warranty_type
                        )}
                      </strong>
                    </div>
                  )}

                  {Boolean(warrantyFinal.end_date) && (
                    <div className="customer-order-detail-field">
                      <span className="customer-order-detail-label">
                        VALID UNTIL
                      </span>
                      <strong className="customer-order-detail-value">
                        {formatDate(
                          String(
                            warrantyFinal.end_date
                          )
                        )}
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

    if (!detail) return null;

    return (
      <section className="dashboard customer-dashboard-page customer-order-details-page">
        <div
          className="page-heading"
          style={{
            display: "flex",
            alignItems: "flex-end",
            justifyContent: "space-between",
            gap: "20px",
          }}
        >
          <div>
            
            <h1>
              {"Bill Details"}
            </h1>
            <p>
              {isOrderDetails
                ? "View the complete details of your purchase record."
                : "View the complete details of your invoice."}
            </p>
          </div>

          <button
            className="secondary-button"
            type="button"
            onClick={() =>
              navigate(
                isOrderDetails
                  ? "/customer/orders"
                  : "/customer/invoices"
              )
            }
          >
            <ArrowLeft size={16} />
            {isOrderDetails ? "Back to My Orders" : "Back to My Bills"}
          </button>
        </div>

        <div className="panel">
          <div
            style={{
              padding: "24px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              gap: "20px",
              flexWrap: "wrap",
            }}
          >
            <div>
              <div
                style={{
                  fontSize: "12px",
                  fontWeight: 700,
                  color: "#64748b",
                  marginBottom: "6px",
                }}
              >
                {isOrderDetails ? "ORDER" : "INVOICE"}
              </div>

              <h2
                style={{
                  margin: 0,
                  fontSize: "26px",
                }}
              >
                  {detail.invoice_number || detail.invoice_id}
              </h2>

              <div
                style={{
                  marginTop: "8px",
                  color: "#64748b",
                }}
              >
                Purchase date:{" "}
                <strong>
                  {formatDate(detail.invoice_date)}
                </strong>
              </div>
            </div>

            <span className={statusClass(detail.payment_status)}>
                {["paid", "completed", "captured"].includes(
                  detail.payment_status?.toLowerCase()
                )
                  ? "✓ Payment Completed"
                  : statusLabel(detail.payment_status)}
              </span>
          </div>

          <div
            style={{
              borderTop: "1px solid #e5e7eb",
              padding: "22px 24px",
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "18px",
            }}
          >
              <div className="customer-order-detail-field">
                <span className="customer-order-detail-label">
                  Purchase Date
                </span>
                <strong className="customer-order-detail-value">
                  {formatDate(detail.invoice_date)}
                </strong>
              </div>

            <div className="customer-order-detail-field">
              <span className="customer-order-detail-label">
                Invoice Number
              </span>
              <strong className="customer-order-detail-value">
                {detail.invoice_number || detail.invoice_id}
              </strong>
            </div>

            <div className="customer-order-detail-field">
              <span className="customer-order-detail-label">
                Invoice Status
              </span>
              <strong className="customer-order-detail-value">
                {statusLabel(detail.status)}
              </strong>
            </div>

            <div className="customer-order-detail-field">
              <span className="customer-order-detail-label">
                Payment Status
              </span>
              <strong className="customer-order-detail-value">
                {statusLabel(detail.payment_status)}
              </strong>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>Products</h3>
              <span>
                {detail.items.length} item
                {detail.items.length === 1 ? "" : "s"} in this bill
              </span>
            </div>
          </div>

          <div className="customer-order-items-responsive">
            <div className="customer-order-items-mobile">
              {detail.items.length === 0 ? (
                <div className="customer-order-item-mobile-empty">
                  No items found for this purchase.
                </div>
              ) : (
                detail.items.map((item) => (
                  <article
                    className="customer-order-item-mobile-card"
                    key={`mobile-item-${item.id}`}
                  >
                    <div className="customer-order-item-mobile-title">
                      <span>PRODUCT</span>
                      <strong>{item.product_name}</strong>
                    </div>

                    <div className="customer-order-item-mobile-grid">
                      <div>
                        <span>SKU</span>
                        <strong>{item.sku || "—"}</strong>
                      </div>

                      <div>
                        <span>QUANTITY</span>
                        <strong>{item.quantity}</strong>
                      </div>

                      <div>
                        <span>UNIT PRICE</span>
                        <strong>{money(item.unit_price)}</strong>
                      </div>

                      <div>
                        <span>TAX</span>
                        <strong>
                          {money(item.tax_amount)}
                          <small>{item.tax_rate}%</small>
                        </strong>
                      </div>

                      <div className="customer-order-item-mobile-total">
                        <span>LINE TOTAL</span>
                        <strong>{money(item.line_total)}</strong>
                      </div>
                    </div>
                  </article>
                ))
              )}
            </div>

            <div className="customer-order-items-desktop">
              <div style={{ overflowX: "auto" }}>
                <table className="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>SKU</th>
                  <th>Qty</th>
                  <th>Unit Price</th>
                  <th>Tax</th>
                  <th>Line Total</th>
                </tr>
              </thead>

              <tbody>
                {detail.items.length === 0 ? (
                  <tr>
                    <td colSpan={6}>
                      No items found for this invoice.
                    </td>
                  </tr>
                ) : (
                  detail.items.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <strong>{item.product_name}</strong>
                      </td>

                      <td>{item.sku || "—"}</td>

                      <td>{item.quantity}</td>

                      <td>{money(item.unit_price)}</td>


                      <td>
                        {money(item.tax_amount)}
                        <div
                          style={{
                            fontSize: "11px",
                            color: "#64748b",
                          }}
                        >
                          {item.tax_rate}%
                        </div>
                      </td>

                      <td>
                        <strong>
                          {money(item.line_total)}
                        </strong>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
                </table>
              </div>
            </div>
          </div>
            </div>
<div
          className="customer-order-summary-grid"
          style={{
            display: "grid",
            gridTemplateColumns:
              "minmax(0, 1fr) minmax(300px, 420px)",
            gap: "20px",
          }}
        >
          {billWarranty && (
            <div className="panel customer-bill-warranty-panel">
              <div className="panel-header">
                <div>
                  <h3>Warranty Protection</h3>
                  <span>Warranty coverage for this purchase</span>
                </div>
              </div>

              <div style={{ padding: "24px" }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "14px",
                    marginBottom: "20px",
                  }}
                >
                  <div
                    style={{
                      width: "44px",
                      height: "44px",
                      borderRadius: "12px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      background: "#eef6ff",
                      color: "#2563eb",
                      fontSize: "20px",
                      fontWeight: 700,
                    }}
                  >
                    ✓
                  </div>

                  <div>
                    <strong>
                      {billWarranty.product_name ||
                        "Product Warranty"}
                    </strong>
                    <div style={{ marginTop: "4px" }}>
                      <span
                        className={`customer-invoice-status customer-invoice-status-${billWarranty.status}`}
                      >
                        {statusLabel(billWarranty.status)}
                      </span>
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns:
                      "repeat(2, minmax(0, 1fr))",
                    gap: "16px",
                  }}
                >
                  <div>
                    <span
                      style={{
                        display: "block",
                        fontSize: "12px",
                        color: "#6b7280",
                        marginBottom: "4px",
                      }}
                    >
                      WARRANTY NUMBER
                    </span>
                    <strong>{billWarranty.warranty_id}</strong>
                  </div>

                  <div>
                    <span
                      style={{
                        display: "block",
                        fontSize: "12px",
                        color: "#6b7280",
                        marginBottom: "4px",
                      }}
                    >
                      VALID UNTIL
                    </span>
                    <strong>
                      {formatDate(billWarranty.end_date)}
                    </strong>
                  </div>

                  <div>
                    <span
                      style={{
                        display: "block",
                        fontSize: "12px",
                        color: "#6b7280",
                        marginBottom: "4px",
                      }}
                    >
                      DURATION
                    </span>
                    <strong>
                      {billWarranty.duration_months} month
                      {billWarranty.duration_months === 1
                        ? ""
                        : "s"}
                    </strong>
                  </div>

                  {billWarranty.variant_name && (
                    <div>
                      <span
                        style={{
                          display: "block",
                          fontSize: "12px",
                          color: "#6b7280",
                          marginBottom: "4px",
                        }}
                      >
                        VARIANT
                      </span>
                      <strong>
                        {billWarranty.variant_name}
                      </strong>
                    </div>
                  )}
                </div>

                <button
                  className="secondary-button"
                  type="button"
                  style={{ marginTop: "20px" }}
                  onClick={() => navigate("/customer/warranty")}
                >
                  View Warranty
                </button>
              </div>
            </div>
          )}

          <div className="panel">
            <div className="panel-header">
              <div>
                <h3>Purchase Notes</h3>
                <span>Additional information about this bill</span>
              </div>
            </div>

            <div style={{ padding: "24px" }}>
              {detail.notes || "No additional notes were added to this bill."}
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <div>
                <h3>Bill Summary</h3>
                <span>Price breakdown</span>
              </div>
            </div>

            <div style={{ padding: "24px" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "8px 0",
                }}
              >
                <span>Subtotal</span>
                <strong>{money(detail.subtotal)}</strong>
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "8px 0",
                }}
              >
                <span>Discount</span>
                <strong>
                  {money(detail.discount_amount)}
                </strong>
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "8px 0",
                }}
              >
                <span>Tax</span>
                <strong>{money(detail.tax_amount)}</strong>
              </div>

              <div
                style={{
                  marginTop: "12px",
                  paddingTop: "16px",
                  borderTop: "1px solid #e5e7eb",
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: "20px",
                }}
              >
                <strong>Total Amount</strong>
                <strong>{money(detail.total_amount)}</strong>
              </div>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="dashboard customer-dashboard-page">
      <div
        className="page-heading"
        style={{
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
          gap: "20px",
        }}
      >
        <div>
          <span className="page-eyebrow">DIGITAL BILL LOCKER</span>
          <h1>My Bills</h1>
          <p>All your digital purchase bills, safely stored in one place.</p>
        </div>

        <button
          className="primary-button"
          type="button"
          onClick={() => navigate("/customer/bills")}
        >
          <Plus size={16} />
          Add Bill
        </button>
      </div>

      {loading ? (
        <div className="panel">
          <div style={{ padding: "32px" }}>
            Loading your invoices...
          </div>
        </div>
      ) : error ? (
        <div className="panel">
          <div style={{ padding: "32px" }}>
            <strong>Unable to load invoices</strong>
            <p>{error}</p>
          </div>
        </div>
      ) : (
        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>Your Bills</h3>
              <span>
                {invoices.length} bill
                {invoices.length === 1 ? "" : "s"} found
              </span>
            </div>
          </div>

          <div className="customer-invoices-desktop-controls">
          <div className="customer-invoices-mobile-search">
            <span>⌕</span>
            <input
              type="search"
              placeholder="Search bills..."
              value={invoiceSearch}
              onChange={(event) =>
                setInvoiceSearch(event.target.value)
              }
              aria-label="Search bills"
            />
          </div>

          <select
            value={invoiceStatus}
            onChange={(event) =>
              setInvoiceStatus(event.target.value)
            }
            aria-label="Filter bills by status"
          >
            <option value="all">All Status</option>
            <option value="paid">Paid</option>
            <option value="partial">Partial</option>
            <option value="unpaid">Unpaid</option>
          </select>
        </div>

        <div className="customer-invoices-desktop-table">
            <div style={{ overflowX: "auto" }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Bill</th>
                    <th>Purchase Date</th>
                    <th>Products</th>
                    <th>Amount</th>
                    <th>Payment</th>
                    <th>Action</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredInvoices.length === 0 ? (
                    <tr>
                      <td colSpan={6}>
                        {invoices.length === 0 ? (
                          <div className="customer-bills-empty-state">
                            <div className="customer-bills-empty-icon">
                              <Eye size={22} />
                            </div>
                            <strong>No bills yet</strong>
                            <span>
                              Your digital purchase bills will appear here
                              after you add or receive a bill.
                            </span>
                            <button
                              type="button"
                              className="primary-button"
                              onClick={() => navigate("/customer/bills")}
                            >
                              Add a Bill
                            </button>
                          </div>
                        ) : (
                          "No bills match your search or filter."
                        )}
                      </td>
                    </tr>
                  ) : (
                    filteredInvoices.map((invoice) => (
                      <tr key={invoice.id}>
                        <td>
                          <strong>
                            #{invoice.invoice_number ||
                              invoice.invoice_id}
                          </strong>
                        </td>

                        <td>
                          {formatDate(invoice.invoice_date)}
                        </td>

                        <td>
                          <strong>
                            {invoice.item_names?.length
                              ? invoice.item_names.join(", ")
                              : "No items"}
                          </strong>
                        </td>

                        <td>
                          <strong>
                            {money(invoice.total_amount)}
                          </strong>
                        </td>

                        <td>
                          <span
                            className={statusClass(
                              invoice.payment_status
                            )}
                          >
                            {statusLabel(
                              invoice.payment_status
                            )}
                          </span>
                        </td>

                        <td>
                          <button
                            className="secondary-button"
                            type="button"
                            onClick={() =>
                              navigate(
                                `/customer/invoices/${encodeURIComponent(
                                  invoice.invoice_id
                                )}`
                              )
                            }
                          >
                            <Eye size={15} />
                            View Bill
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="customer-invoices-mobile-content">

            <div className="customer-invoices-mobile-controls">
              <div className="customer-invoices-mobile-search">
                <span>⌕</span>
                <input
                  type="search"
                  placeholder="Search bills..."
                  value={invoiceSearch}
                  onChange={(event) =>
                    setInvoiceSearch(event.target.value)
                  }
                  aria-label="Search bills"
                />
              </div>

              <select
                value={invoiceStatus}
                onChange={(event) =>
                  setInvoiceStatus(event.target.value)
                }
                aria-label="Filter invoices by status"
              >
                <option value="all">All Status</option>
                <option value="paid">Paid</option>
                <option value="partial">Partial</option>
                <option value="unpaid">Unpaid</option>
              </select>
            </div>

            {loading ? (
              <div className="customer-invoices-mobile-empty">
                Loading your invoices...
              </div>
            ) : filteredInvoices.length === 0 ? (
              <div className="customer-invoices-mobile-empty">
                No bills found.
              </div>
            ) : (
              <div className="customer-invoices-mobile-list">
                {filteredInvoices.map((invoice) => (
                  <article
                    className="customer-invoice-mobile-card"
                    key={invoice.id}
                  >
                    <div className="customer-invoice-mobile-card-top">
                      <div className="customer-invoice-mobile-icon">
                        <span>▤</span>
                      </div>

                      <div className="customer-invoice-mobile-main">
                        <strong>
                          #
                          {invoice.invoice_number ||
                            invoice.invoice_id}
                        </strong>

                        <small>
                          {formatDate(invoice.invoice_date)}
                        </small>
                      </div>

                      <span
                        className={`customer-invoice-mobile-status ${
                          invoice.payment_status
                            ?.toLowerCase() || ""
                        }`}
                      >
                        {statusLabel(
                          invoice.payment_status || "pending"
                        )}
                      </span>
                    </div>

                    <div className="customer-invoice-mobile-divider" />

                    <div className="customer-invoice-mobile-item">
                      <small>ITEM</small>
                      <strong>
                        {invoice.item_names?.length
                          ? invoice.item_names.join(", ")
                          : "No items"}
                      </strong>
                    </div>

                    <div className="customer-invoice-mobile-bottom">
                      <div>
                        <small>AMOUNT</small>
                        <strong>
                          {money(invoice.total_amount)}
                        </strong>
                      </div>

                      <button
                        type="button"
                        className="customer-invoice-mobile-view"
                        onClick={() =>
                          navigate(
                            `/customer/invoices/${encodeURIComponent(
                              invoice.invoice_id
                            )}`
                          )
                        }
                      >
                        <Eye size={15} />
                        View Bill
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}

          </div>
          </div>
      )}
    </section>
  );
}
