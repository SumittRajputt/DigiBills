import { useEffect, useRef, useState } from "react";
import {
  CheckCircle2,
  Download,
  FileText,
  Upload,
  X,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { API_BASE_URL } from "../api";

declare global {
  interface Window {
    Razorpay?: new (options: RazorpayOptions) => RazorpayInstance;
  }
}

interface RazorpayOptions {
  key: string;
  amount: number;
  currency: string;
  name: string;
  description: string;
  order_id: string;
  handler: (response: RazorpayPaymentResponse) => void | Promise<void>;
  modal?: {
    ondismiss?: () => void;
  };
  prefill?: {
    name?: string;
    email?: string;
    contact?: string;
  };
  theme?: {
    color?: string;
  };
}

interface RazorpayPaymentResponse {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

interface RazorpayInstance {
  open: () => void;
  close?: () => void;
  on?: (event: string, callback: (response: unknown) => void) => void;
}

interface UploadedBill {
  id: string;
  bill_id: string;
  original_filename: string;
  content_type: string;
  file_size: number;
  amount: number;
  payment_status: string;
  status: string;
  uploaded_at: string;
  razorpay_order_id: string | null;
}

interface DigiBillProduct {
  product_name: string | null;
  brand: string | null;
  model_number: string | null;
  serial_number: string | null;
  quantity: number | null;
  unit_price: number | null;
  discount: number | null;
  tax_amount: number | null;
  total_amount: number | null;
}

interface DigiBillConfirmation {
  bill_id: string;
  eligible: boolean;
  retailer: Record<string, unknown>;
  customer: Record<string, unknown>;
  invoice_number: string | null;
  invoice_date: string | null;
  products: DigiBillProduct[];
  totals: Record<string, unknown>;
  payment: Record<string, unknown>;
  warranty: Record<string, unknown>;
  confidence_scores: Record<string, unknown>;
  extraction_notes: string[];
}

interface DigiBill {
  digibill_id: string;
  uploaded_bill_id: string;
  customer_id: string;
  invoice_number: string | null;
  invoice_date: string | null;
  retailer: Record<string, unknown>;
  customer: Record<string, unknown>;
  products: DigiBillProduct[];
  totals: Record<string, unknown>;
  payment: Record<string, unknown>;
  warranty_evidence: Record<string, unknown>;
  confidence_scores: Record<string, unknown>;
  extraction_notes: string[];
  status: string;
  confirmed_at: string;
  created_at: string;
  updated_at: string;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const RAZORPAY_SCRIPT_URL = "https://checkout.razorpay.com/v1/checkout.js";
const RAZORPAY_KEY_ID = import.meta.env.VITE_RAZORPAY_KEY_ID as string | undefined;

export default function CustomerBills() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const razorpayRef = useRef<RazorpayInstance | null>(null);

  const [bills, setBills] = useState<UploadedBill[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedBill, setSelectedBill] = useState<UploadedBill | null>(null);
  const [billConfirmation, setBillConfirmation] =
    useState<DigiBillConfirmation | null>(null);
  const [createdDigiBill, setCreatedDigiBill] =
    useState<DigiBill | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const [customerWarrantyAnswer, setCustomerWarrantyAnswer] =
    useState<"yes" | "no" | "unknown">("unknown");
  const [warrantyDurationValue, setWarrantyDurationValue] =
    useState("");
  const [warrantyDurationUnit, setWarrantyDurationUnit] =
    useState<"months" | "years">("years");

  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [verifyingPayment, setVerifyingPayment] = useState(false);
  const [creatingDigiBill, setCreatingDigiBill] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let cancelled = false;

    const loadBills = async () => {
      try {
        setLoading(true);
        setError("");

        const token = sessionStorage.getItem("digibills_token");

        if (!token) {
          navigate("/");
          return;
        }

        const response = await fetch(
          `${API_BASE_URL}/customer/uploaded-bills`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (response.status === 401) {
          sessionStorage.removeItem("digibills_token");
          navigate("/");
          return;
        }

        if (!response.ok) {
          throw new Error(
            (await response.text()) || "Failed to load uploaded bills."
          );
        }

        const data = (await response.json()) as UploadedBill[];

        if (!cancelled) {
          setBills(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load uploaded bills."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadBills();

    return () => {
      cancelled = true;
    };
  }, [navigate]);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }

      if (razorpayRef.current?.close) {
        razorpayRef.current.close();
      }
    };
  }, [previewUrl]);

  const loadRazorpay = async (): Promise<boolean> => {
    if (window.Razorpay) {
      return true;
    }

    const existingScript = document.querySelector<HTMLScriptElement>(
      `script[src="${RAZORPAY_SCRIPT_URL}"]`
    );

    if (existingScript) {
      return new Promise((resolve) => {
        existingScript.addEventListener(
          "load",
          () => resolve(Boolean(window.Razorpay)),
          { once: true }
        );
        existingScript.addEventListener(
          "error",
          () => resolve(false),
          { once: true }
        );
      });
    }

    return new Promise((resolve) => {
      const script = document.createElement("script");
      script.src = RAZORPAY_SCRIPT_URL;
      script.async = true;

      script.onload = () => {
        resolve(Boolean(window.Razorpay));
      };

      script.onerror = () => {
        resolve(false);
      };

      document.body.appendChild(script);
    });
  };

  const clearSelectedFile = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setSelectedFile(null);
    setPreviewUrl(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleFileSelection = (file: File | undefined) => {
    setError("");
    setSuccess("");

    if (!file) {
      return;
    }

    if (
      file.type !== "application/pdf" &&
      !file.name.toLowerCase().endsWith(".pdf")
    ) {
      setError("Only PDF files are allowed.");
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError("The uploaded PDF must be 10 MB or smaller.");
      return;
    }

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    const nextPreviewUrl = URL.createObjectURL(file);

    setSelectedFile(file);
    setPreviewUrl(nextPreviewUrl);
  };

  const refreshBills = async () => {
    const token = sessionStorage.getItem("digibills_token");

    if (!token) {
      navigate("/");
      return;
    }

    const response = await fetch(
      `${API_BASE_URL}/customer/uploaded-bills`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (response.status === 401) {
      sessionStorage.removeItem("digibills_token");
      navigate("/");
      return;
    }

    if (!response.ok) {
      throw new Error(
        (await response.text()) || "Failed to refresh uploaded bills."
      );
    }

    setBills((await response.json()) as UploadedBill[]);
  };

  const verifyPayment = async (
    billId: string,
    payment: RazorpayPaymentResponse
  ) => {
    const token = sessionStorage.getItem("digibills_token");

    if (!token) {
      navigate("/");
      return;
    }

    setVerifyingPayment(true);
    setError("");
    setSuccess("");

    try {
      const params = new URLSearchParams({
        razorpay_order_id: payment.razorpay_order_id,
        razorpay_payment_id: payment.razorpay_payment_id,
        razorpay_signature: payment.razorpay_signature,
      });

      const response = await fetch(
        `${API_BASE_URL}/customer/uploaded-bills/verify-payment?${params.toString()}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        sessionStorage.removeItem("digibills_token");
        navigate("/");
        return;
      }

      if (!response.ok) {
        throw new Error(
          (await response.text()) || "Payment verification failed."
        );
      }

      await response.json();

      setSuccess("Payment successful. Your bill has been added to My Bills.");
      clearSelectedFile();
      await refreshBills();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Payment verification failed."
      );
    } finally {
      setVerifyingPayment(false);
      razorpayRef.current = null;
    }
  };

  const openPaymentCheckout = (bill: UploadedBill) => {
    if (!RAZORPAY_KEY_ID) {
      setError(
        "Razorpay is not configured on this device. Please contact support."
      );
      return;
    }

    if (!window.Razorpay) {
      setError("Razorpay Checkout could not be loaded. Please try again.");
      return;
    }

    const checkout = new window.Razorpay({
      key: RAZORPAY_KEY_ID,
      amount: Math.round(Number(bill.amount) * 100),
      currency: "INR",
      name: "DigiBills",
      description: "Customer uploaded bill",
      order_id: bill.razorpay_order_id || "",
      handler: async (response) => {
        await verifyPayment(bill.bill_id, response);
      },
      modal: {
        ondismiss: () => {
          razorpayRef.current = null;
          setSuccess("");
          setError(
            "Payment was cancelled. Your bill is still pending payment."
          );
        },
      },
      theme: {
        color: "#2563eb",
      },
    });

    razorpayRef.current = checkout;
    checkout.open();
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Please select a PDF bill first.");
      return;
    }

    const token = sessionStorage.getItem("digibills_token");

    if (!token) {
      navigate("/");
      return;
    }

    setUploading(true);
    setError("");
    setSuccess("");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch(
        `${API_BASE_URL}/customer/uploaded-bills`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        }
      );

      if (response.status === 401) {
        sessionStorage.removeItem("digibills_token");
        navigate("/");
        return;
      }

      if (!response.ok) {
        throw new Error(
          (await response.text()) || "Failed to upload bill."
        );
      }

      const bill = (await response.json()) as UploadedBill;

      if (Number(bill.amount) === 0) {
        setSuccess(
          "Bill uploaded successfully. Your active subscription covered the upload fee."
        );
        clearSelectedFile();
        await refreshBills();
        return;
      }

      if (Number(bill.amount) !== 9) {
        throw new Error("Unexpected upload fee returned by the server.");
      }

      const razorpayLoaded = await loadRazorpay();

      if (!razorpayLoaded) {
        throw new Error(
          "Razorpay Checkout could not be loaded. Please try again."
        );
      }

      clearSelectedFile();

      setSuccess("Your bill is ready. Complete the ₹9 payment to save it.");

      openPaymentCheckout(bill);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to upload bill."
      );
    } finally {
      setUploading(false);
    }
  };

  const loadBillConfirmation = async (bill: UploadedBill) => {
    const token = sessionStorage.getItem("digibills_token");

    if (!token) {
      navigate("/");
      return;
    }

    setError("");
    setSuccess("");
    setSelectedBill(bill);
    setBillConfirmation(null);
    setCustomerWarrantyAnswer("unknown");
    setWarrantyDurationValue("");
    setWarrantyDurationUnit("years");

    try {
      const response = await fetch(
        `${API_BASE_URL}/customer/uploaded-bills/${encodeURIComponent(
          bill.bill_id
        )}/confirmation`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        sessionStorage.removeItem("digibills_token");
        navigate("/");
        return;
      }

      if (!response.ok) {
        const message = await response.text();

        let detail = "Unable to review this bill.";

        try {
          const parsed = JSON.parse(message) as { detail?: string };
          detail = parsed.detail || detail;
        } catch {
          if (message) {
            detail = message;
          }
        }

        throw new Error(detail);
      }

      const confirmation =
        (await response.json()) as DigiBillConfirmation;

      setBillConfirmation(confirmation);
    } catch (err) {
      setSelectedBill(null);
      setBillConfirmation(null);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to review this bill."
      );
    }
  };

  const handleConfirmDigiBill = async () => {
    const token = sessionStorage.getItem("digibills_token");

    if (!token) {
      navigate("/");
      return;
    }

    if (!selectedBill || !billConfirmation) {
      setError("Please open the bill review before confirming the DigiBill.");
      return;
    }

    if (!billConfirmation.eligible) {
      setError("This bill is not eligible for DigiBill creation.");
      return;
    }

    if (customerWarrantyAnswer === "yes") {
      const duration = Number(warrantyDurationValue);

      if (
        !Number.isFinite(duration) ||
        duration <= 0
      ) {
        setError("Please enter a valid warranty duration.");
        return;
      }
    }

    setError("");
    setSuccess("");
    setCreatingDigiBill(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/customer/uploaded-bills/${encodeURIComponent(
          selectedBill.bill_id
        )}/confirm`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            customer_has_warranty: customerWarrantyAnswer,
            duration_value:
              customerWarrantyAnswer === "yes"
                ? Number(warrantyDurationValue)
                : null,
            duration_unit:
              customerWarrantyAnswer === "yes"
                ? warrantyDurationUnit
                : null,
          }),
        }
      );

      if (response.status === 401) {
        sessionStorage.removeItem("digibills_token");
        navigate("/");
        return;
      }

      if (!response.ok) {
        const message = await response.text();

        let detail = "Unable to create DigiBill.";

        try {
          const parsed = JSON.parse(message) as { detail?: string };
          detail = parsed.detail || detail;
        } catch {
          if (message) {
            detail = message;
          }
        }

        throw new Error(detail);
      }

      const digiBill = (await response.json()) as DigiBill;

      setCreatedDigiBill(digiBill);
      setSuccess(
        `DigiBill ${digiBill.digibill_id} created successfully.`
      );

      setBillConfirmation(null);
      setSelectedBill(null);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to create DigiBill."
      );
    } finally {
      setCreatingDigiBill(false);
    }
  };

  const closeBillConfirmation = () => {
    setSelectedBill(null);
    setBillConfirmation(null);
  };

  const handleDownload = async (billId: string, filename: string) => {
    const token = sessionStorage.getItem("digibills_token");

    if (!token) {
      navigate("/");
      return;
    }

    try {
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/customer/uploaded-bills/${encodeURIComponent(
          billId
        )}/download`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        sessionStorage.removeItem("digibills_token");
        navigate("/");
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
      link.download = filename || `${billId}.pdf`;
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
  };

  const formatFileSize = (size: number) => {
    if (size < 1024) {
      return `${size} B`;
    }

    if (size < 1024 * 1024) {
      return `${(size / 1024).toFixed(1)} KB`;
    }

    return `${(size / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatDate = (value: string) => {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleString("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  };

  return (
    <section className="dashboard customer-bills-page">
      <div className="customer-bills-header">
        <div>
          <h1>My Bills</h1>
          <p>
            Upload and securely keep your personal PDF bills in your DigiBills
            locker.
          </p>
        </div>

        <button
          type="button"
          className="customer-bills-upload-button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading || verifyingPayment}
        >
          <Upload size={17} />
          Upload Your Bill
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf,.pdf"
          hidden
          onChange={(event) => {
            handleFileSelection(event.target.files?.[0]);
            event.currentTarget.value = "";
          }}
        />
      </div>

      {error && (
        <div className="customer-bills-message error">
          <X size={18} />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="customer-bills-message success">
          <CheckCircle2 size={18} />
          <span>{success}</span>
        </div>
      )}

      {selectedFile && (
        <div className="customer-bills-upload-card">
          <div className="customer-bills-upload-zone">
            <FileText size={38} />

            <h3>PDF bill selected</h3>
            <p>
              Only PDF files up to 10 MB are supported.
            </p>

            <div className="customer-bills-file-info">
              <div className="customer-bills-file-info-icon">
                <FileText size={20} />
              </div>

              <div className="customer-bills-file-info-content">
                <strong title={selectedFile.name}>
                  {selectedFile.name}
                </strong>
                <small>
                  PDF • {formatFileSize(selectedFile.size)}
                </small>
              </div>

              <button
                type="button"
                className="customer-bills-remove-button"
                onClick={clearSelectedFile}
                disabled={uploading || verifyingPayment}
                aria-label="Remove selected file"
              >
                <X size={18} />
              </button>
            </div>
          </div>

          <div className="customer-bills-actions">
            <button
              type="button"
              className="customer-bills-secondary-button"
              onClick={clearSelectedFile}
              disabled={uploading || verifyingPayment}
            >
              Cancel
            </button>

            <button
              type="button"
              className="customer-bills-primary-button"
              onClick={() => void handleUpload()}
              disabled={uploading || verifyingPayment}
            >
              <Upload size={16} />
              {uploading ? "Uploading..." : "Continue"}
            </button>
          </div>
        </div>
      )}

      {previewUrl && (
        <div className="customer-bills-preview-card">
          <h3>PDF Preview</h3>

          <iframe
            className="customer-bills-preview"
            src={previewUrl}
            title="Selected bill preview"
          />
        </div>
      )}

      {billConfirmation && selectedBill && (
        <div className="customer-bills-review-card">
          <div className="customer-bills-review-header">
            <div>
              <span className="customer-bills-review-eyebrow">
                BILL REVIEW
              </span>
              <h2>Review Your Bill</h2>
              <p>
                Check the extracted information before creating your DigiBill.
              </p>
            </div>

            <button
              type="button"
              className="customer-bills-remove-button"
              onClick={closeBillConfirmation}
              aria-label="Close bill review"
            >
              <X size={18} />
            </button>
          </div>

          <div className="customer-bills-review-source">
            <FileText size={18} />
            <div>
              <strong>{selectedBill.original_filename}</strong>
              <small>
                {selectedBill.bill_id} • Original PDF preserved
              </small>
            </div>
          </div>

          <div className="customer-bills-review-section">
            <h3>Retailer</h3>

            <div className="customer-bills-review-grid">
              <div>
                <span>Name</span>
                <strong>
                  {String(billConfirmation.retailer.name || "Not available")}
                </strong>
              </div>

              <div>
                <span>GSTIN</span>
                <strong>
                  {String(
                    billConfirmation.retailer.gstin || "Not available"
                  )}
                </strong>
              </div>

              <div>
                <span>Phone</span>
                <strong>
                  {String(
                    billConfirmation.retailer.phone || "Not available"
                  )}
                </strong>
              </div>

              <div>
                <span>Address</span>
                <strong>
                  {String(
                    billConfirmation.retailer.address || "Not available"
                  )}
                </strong>
              </div>
            </div>
          </div>

          <div className="customer-bills-review-section">
            <h3>Invoice</h3>

            <div className="customer-bills-review-grid">
              <div>
                <span>Invoice Number</span>
                <strong>
                  {billConfirmation.invoice_number || "Not available"}
                </strong>
              </div>

              <div>
                <span>Invoice Date</span>
                <strong>
                  {billConfirmation.invoice_date
                    ? formatDate(billConfirmation.invoice_date)
                    : "Not available"}
                </strong>
              </div>
            </div>
          </div>

          <div className="customer-bills-review-section">
            <h3>Products</h3>

            {billConfirmation.products.length === 0 ? (
              <div className="customer-bills-review-empty">
                No product information was extracted from this bill.
              </div>
            ) : (
              <div className="customer-bills-product-list">
                {billConfirmation.products.map((product, index) => (
                  <div
                    className="customer-bills-product-card"
                    key={`${product.product_name || "product"}-${index}`}
                  >
                    <div className="customer-bills-product-header">
                      <strong>
                        {product.product_name || "Unnamed product"}
                      </strong>

                      {product.total_amount !== null && (
                        <strong>
                          ₹{Number(product.total_amount).toFixed(2)}
                        </strong>
                      )}
                    </div>

                    <div className="customer-bills-review-grid">
                      <div>
                        <span>Brand</span>
                        <strong>
                          {product.brand || "Not available"}
                        </strong>
                      </div>

                      <div>
                        <span>Model</span>
                        <strong>
                          {product.model_number || "Not available"}
                        </strong>
                      </div>

                      <div>
                        <span>Serial Number</span>
                        <strong>
                          {product.serial_number || "Not available"}
                        </strong>
                      </div>

                      <div>
                        <span>Quantity</span>
                        <strong>
                          {product.quantity !== null
                            ? String(product.quantity)
                            : "Not available"}
                        </strong>
                      </div>

                      <div>
                        <span>Unit Price</span>
                        <strong>
                          {product.unit_price !== null
                            ? `₹${Number(product.unit_price).toFixed(2)}`
                            : "Not available"}
                        </strong>
                      </div>

                      <div>
                        <span>Tax</span>
                        <strong>
                          {product.tax_amount !== null
                            ? `₹${Number(product.tax_amount).toFixed(2)}`
                            : "Not available"}
                        </strong>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="customer-bills-review-section">
            <h3>Totals</h3>

            <div className="customer-bills-review-grid">
              <div>
                <span>Subtotal</span>
                <strong>
                  {billConfirmation.totals.subtotal !== null &&
                  billConfirmation.totals.subtotal !== undefined
                    ? `₹${Number(
                        billConfirmation.totals.subtotal
                      ).toFixed(2)}`
                    : "Not available"}
                </strong>
              </div>

              <div>
                <span>Discount</span>
                <strong>
                  {billConfirmation.totals.discount !== null &&
                  billConfirmation.totals.discount !== undefined
                    ? `₹${Number(
                        billConfirmation.totals.discount
                      ).toFixed(2)}`
                    : "Not available"}
                </strong>
              </div>

              <div>
                <span>Tax</span>
                <strong>
                  {billConfirmation.totals.tax_amount !== null &&
                  billConfirmation.totals.tax_amount !== undefined
                    ? `₹${Number(
                        billConfirmation.totals.tax_amount
                      ).toFixed(2)}`
                    : "Not available"}
                </strong>
              </div>

              <div>
                <span>Total Amount</span>
                <strong>
                  {billConfirmation.totals.total_amount !== null &&
                  billConfirmation.totals.total_amount !== undefined
                    ? `₹${Number(
                        billConfirmation.totals.total_amount
                      ).toFixed(2)}`
                    : "Not available"}
                </strong>
              </div>
            </div>
          </div>

          <div className="customer-bills-review-section">
            <h3>Payment</h3>

            <div className="customer-bills-review-grid">
              <div>
                <span>Method</span>
                <strong>
                  {String(
                    billConfirmation.payment.payment_method ||
                      "Not available"
                  )}
                </strong>
              </div>

              <div>
                <span>Paid Amount</span>
                <strong>
                  {billConfirmation.payment.paid_amount !== null &&
                  billConfirmation.payment.paid_amount !== undefined
                    ? `₹${Number(
                        billConfirmation.payment.paid_amount
                      ).toFixed(2)}`
                    : "Not available"}
                </strong>
              </div>

              <div>
                <span>Status</span>
                <strong>
                  {String(
                    billConfirmation.payment.payment_status ||
                      "Not available"
                  )}
                </strong>
              </div>
            </div>
          </div>

          <div className="customer-bills-review-section">
            <h3>Warranty Information</h3>

            <div className="customer-bills-warranty-summary">
              <strong>
                {billConfirmation.warranty.mentioned === "yes"
                  ? "Warranty information found on the bill"
                  : billConfirmation.warranty.mentioned === "no"
                    ? "No warranty information found on the bill"
                    : "Warranty information is unclear"}
              </strong>

              {billConfirmation.warranty.provider != null &&
                String(billConfirmation.warranty.provider).trim() !== "" && (
                  <span>
                    Provider: {String(billConfirmation.warranty.provider)}
                  </span>
                )}

              {billConfirmation.warranty.warranty_type != null &&
                String(billConfirmation.warranty.warranty_type).trim() !== "" && (
                  <span>
                    Type: {String(billConfirmation.warranty.warranty_type)}
                  </span>
                )}

              {billConfirmation.warranty.duration != null &&
                String(billConfirmation.warranty.duration).trim() !== "" && (
                  <span>
                    Duration: {String(billConfirmation.warranty.duration)}
                  </span>
                )}

              {billConfirmation.warranty.registration_number != null &&
                String(billConfirmation.warranty.registration_number).trim() !== "" && (
                  <span>
                    Warranty / Registration No.:{" "}
                    {String(billConfirmation.warranty.registration_number)}
                  </span>
                )}
            </div>

            <div className="customer-bills-warranty-confirmation">
              <strong>
                {billConfirmation.warranty.mentioned === "yes"
                  ? "Warranty information was found on this bill. Is this information correct?"
                  : billConfirmation.warranty.mentioned === "no"
                    ? "No warranty information was found on this bill. Does this product have a warranty?"
                    : "Does this product have a warranty?"}
              </strong>

              <div className="customer-bills-warranty-options">
                <label>
                  <input
                    type="radio"
                    name="customer-warranty-answer"
                    value="yes"
                    checked={customerWarrantyAnswer === "yes"}
                    onChange={() => setCustomerWarrantyAnswer("yes")}
                  />
                  <span>
                    {billConfirmation.warranty.mentioned === "yes"
                      ? "Yes, this information is correct"
                      : "Yes, it has a warranty"}
                  </span>
                </label>

                <label>
                  <input
                    type="radio"
                    name="customer-warranty-answer"
                    value="no"
                    checked={customerWarrantyAnswer === "no"}
                    onChange={() => {
                      setCustomerWarrantyAnswer("no");
                      setWarrantyDurationValue("");
                    }}
                  />
                  <span>
                    {billConfirmation.warranty.mentioned === "yes"
                      ? "No, this information is not correct"
                      : "No, it doesn't have a warranty"}
                  </span>
                </label>

                {billConfirmation.warranty.mentioned !== "yes" && (
                  <label>
                    <input
                      type="radio"
                      name="customer-warranty-answer"
                      value="unknown"
                      checked={customerWarrantyAnswer === "unknown"}
                      onChange={() => {
                        setCustomerWarrantyAnswer("unknown");
                        setWarrantyDurationValue("");
                      }}
                    />
                    <span>I'm not sure</span>
                  </label>
                )}
              </div>

              {customerWarrantyAnswer === "yes" &&
                (billConfirmation.warranty.duration_value == null ||
                  billConfirmation.warranty.duration_unit == null) && (
                  <div className="customer-bills-warranty-duration">
                    <label htmlFor="warranty-duration">
                      Warranty duration
                    </label>

                    <div className="customer-bills-warranty-duration-inputs">
                      <input
                        id="warranty-duration"
                        type="number"
                        min="0.1"
                        step="0.1"
                        value={warrantyDurationValue}
                        onChange={(event) =>
                          setWarrantyDurationValue(event.target.value)
                        }
                        placeholder="Enter duration"
                      />

                      <select
                        value={warrantyDurationUnit}
                        onChange={(event) =>
                          setWarrantyDurationUnit(
                            event.target.value as "months" | "years"
                          )
                        }
                      >
                        <option value="months">Months</option>
                        <option value="years">Years</option>
                      </select>
                    </div>
                  </div>
                )}
            </div>
          </div>

          {billConfirmation.extraction_notes.length > 0 && (
            <div className="customer-bills-review-section">
              <h3>Extraction Notes</h3>

              <ul className="customer-bills-review-notes">
                {billConfirmation.extraction_notes.map((note, index) => (
                  <li key={`${note}-${index}`}>{note}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="customer-bills-review-actions">
            <button
              type="button"
              className="customer-bills-secondary-button"
              onClick={closeBillConfirmation}
            >
              Close
            </button>

            <button
              type="button"
              className="customer-bills-primary-button"
              onClick={() => void handleConfirmDigiBill()}
              disabled={creatingDigiBill}
            >
              {creatingDigiBill
                ? "Creating DigiBill..."
                : "Confirm & Create DigiBill"}
            </button>
          </div>
        </div>
      )}

      <div className="customer-bills-list-card">
        <h2>Uploaded Bills</h2>

        {loading ? (
          <div className="customer-bills-empty">
            Loading your bills...
          </div>
        ) : bills.length === 0 ? (
          <div className="customer-bills-empty">
            You have not uploaded any bills yet.
          </div>
        ) : (
          <div className="customer-bills-list">
            {bills.map((bill) => (
              <div className="customer-bill-row" key={bill.id}>
                <div className="customer-bill-icon">
                  <FileText size={20} />
                </div>

                <div className="customer-bill-details">
                  <strong title={bill.original_filename}>
                    {bill.original_filename}
                  </strong>

                  <small>
                    {bill.bill_id} • {formatFileSize(bill.file_size)} •{" "}
                    {formatDate(bill.uploaded_at)}
                  </small>
                </div>

                <div className="customer-bill-meta">
                  <span
                    className={`customer-bill-status ${bill.status}`}
                  >
                    {bill.status.replace(/_/g, " ")}
                  </span>

                  {Number(bill.amount) > 0 && (
                    <span className="customer-bill-amount">
                      ₹{Number(bill.amount).toFixed(2)}
                    </span>
                  )}

                  <button
                    type="button"
                    className="customer-bill-download"
                    onClick={() =>
                      void handleDownload(
                        bill.bill_id,
                        bill.original_filename
                      )
                    }
                  >
                    <Download size={15} />
                    Download
                  </button>

                  {bill.status === "completed" && (
                      <button
                        type="button"
                        className="customer-bills-secondary-button"
                        onClick={() => void loadBillConfirmation(bill)}
                        disabled={verifyingPayment}
                      >
                        Review Bill
                      </button>
                    )}

                  {bill.status === "payment_pending" &&
                    bill.razorpay_order_id && (
                      <button
                        type="button"
                        className="customer-bills-primary-button"
                        onClick={async () => {
                          setError("");
                          setSuccess("");

                          const loaded = await loadRazorpay();

                          if (!loaded) {
                            setError(
                              "Razorpay Checkout could not be loaded. Please try again."
                            );
                            return;
                          }

                          openPaymentCheckout(bill);
                        }}
                        disabled={verifyingPayment}
                      >
                        Pay ₹9
                      </button>
                    )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
