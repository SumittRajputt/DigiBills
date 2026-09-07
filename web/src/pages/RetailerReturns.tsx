import {
  Search,
  RotateCcw,
  CheckCircle,
  Clock,
  Wallet,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../api";

type SalesReturn = {
  id: string;
  return_id: string;
  invoice_id: string;
  retailer_id: string;
  customer_id: string;
  processed_by_user_id: string | null;
  return_amount: string;
  refund_amount: string;
  refund_method: string | null;
  status: string;
  reason: string | null;
  notes: string | null;
  requested_at: string;
  processed_at: string | null;
  created_at: string;
  updated_at: string;
};

type PurchaseReturn = {
  id: string;
  return_id: string;
  purchase_order_id: string;
  retailer_id: string;
  supplier_id: string;
  location_id: string;
  processed_by_user_id: string | null;
  return_amount: string;
  status: string;
  reason: string | null;
  notes: string | null;
  requested_at: string;
  processed_at: string | null;
  created_at: string;
  updated_at: string;
};

type Payment = {
  id: string;
  payment_id: string;
  invoice_id: string;
  amount: string;
  payment_method: string;
  payment_status: string;
  transaction_reference: string | null;
  paid_at: string;
  refund_amount: string;
  refund_status: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

type Tab = "sales" | "purchase" | "refunds";

export default function RetailerReturns() {
  const [salesReturns, setSalesReturns] = useState<SalesReturn[]>([]);
  const [purchaseReturns, setPurchaseReturns] = useState<
    PurchaseReturn[]
  >([]);
  const [payments, setPayments] = useState<Payment[]>([]);

  const [tab, setTab] = useState<Tab>("sales");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedSalesReturn, setSelectedSalesReturn] =
    useState<SalesReturn | null>(null);

  const [selectedPurchaseReturn, setSelectedPurchaseReturn] =
    useState<PurchaseReturn | null>(null);

  const [selectedPayment, setSelectedPayment] =
    useState<Payment | null>(null);

  const [processingReturn, setProcessingReturn] =
    useState(false);

  const [processError, setProcessError] =
    useState("");

  const [refundMethod, setRefundMethod] =
    useState("original");

  async function loadData() {
    try {
      setLoading(true);
      setError("");

      const [sales, purchase, paymentData] =
        await Promise.all([
          apiFetch<SalesReturn[]>("/sales-returns"),
          apiFetch<PurchaseReturn[]>(
            "/purchase-returns"
          ),
          apiFetch<Payment[]>("/payments"),
        ]);

      setSalesReturns(sales);
      setPurchaseReturns(purchase);
      setPayments(paymentData);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load returns and refunds."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const filteredSalesReturns = useMemo(() => {
    const query = search.toLowerCase().trim();

    return salesReturns.filter((item) => {
      const matchesSearch =
        !query ||
        item.return_id.toLowerCase().includes(query) ||
        item.invoice_id.toLowerCase().includes(query) ||
        item.customer_id.toLowerCase().includes(query) ||
        (item.reason || "").toLowerCase().includes(query);

      const matchesStatus =
        status === "all" ||
        item.status.toLowerCase() === status;

      return matchesSearch && matchesStatus;
    });
  }, [salesReturns, search, status]);

  const filteredPurchaseReturns = useMemo(() => {
    const query = search.toLowerCase().trim();

    return purchaseReturns.filter((item) => {
      const matchesSearch =
        !query ||
        item.return_id.toLowerCase().includes(query) ||
        item.purchase_order_id
          .toLowerCase()
          .includes(query) ||
        item.supplier_id.toLowerCase().includes(query) ||
        (item.reason || "").toLowerCase().includes(query);

      const matchesStatus =
        status === "all" ||
        item.status.toLowerCase() === status;

      return matchesSearch && matchesStatus;
    });
  }, [purchaseReturns, search, status]);

  const filteredRefunds = useMemo(() => {
    const query = search.toLowerCase().trim();

    return payments.filter((item) => {
      if (Number(item.refund_amount) <= 0) {
        return false;
      }

      const matchesSearch =
        !query ||
        item.payment_id.toLowerCase().includes(query) ||
        item.invoice_id.toLowerCase().includes(query) ||
        (item.transaction_reference || "")
          .toLowerCase()
          .includes(query);

      const refundStatus =
        item.refund_status || "none";

      const matchesStatus =
        status === "all" ||
        refundStatus.toLowerCase() === status;

      return matchesSearch && matchesStatus;
    });
  }, [payments, search, status]);

  const salesProcessed = salesReturns.filter(
    (item) => item.status === "processed"
  ).length;

  const salesRequested = salesReturns.filter(
    (item) => item.status === "requested"
  ).length;

  const purchaseProcessed = purchaseReturns.filter(
    (item) => item.status === "processed"
  ).length;

  const purchaseRequested = purchaseReturns.filter(
    (item) => item.status === "requested"
  ).length;

  const totalRefundAmount = payments.reduce(
    (total, item) =>
      total + Number(item.refund_amount || "0"),
    0
  );

  function formatDate(value: string) {
    return new Date(value).toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  function formatAmount(value: string | number) {
    return `₹${Number(value).toLocaleString("en-IN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }

  function resetFilters() {
    setSearch("");
    setStatus("all");
  }

  async function processSalesReturn(
    item: SalesReturn,
  ) {
    if (item.status !== "requested") {
      return;
    }

    if (
      !window.confirm(
        `Process customer return ${item.return_id}?`,
      )
    ) {
      return;
    }

    try {
      setProcessingReturn(true);
      setProcessError("");

      const updated =
        await apiFetch<SalesReturn>(
          `/sales-returns/${encodeURIComponent(
            item.return_id,
          )}/process`,
          {
            method: "POST",
            body: JSON.stringify({
              refund_method:
                refundMethod === "original"
                  ? null
                  : refundMethod,
            }),
          },
        );

      setSalesReturns((current) =>
        current.map((entry) =>
          entry.id === updated.id
            ? updated
            : entry,
        ),
      );

      setSelectedSalesReturn(updated);
    } catch (err) {
      setProcessError(
        err instanceof Error
          ? err.message
          : "Unable to process customer return.",
      );
    } finally {
      setProcessingReturn(false);
    }
  }

  async function processPurchaseReturn(
    item: PurchaseReturn,
  ) {
    if (item.status !== "requested") {
      return;
    }

    if (
      !window.confirm(
        `Process supplier return ${item.return_id}?`,
      )
    ) {
      return;
    }

    try {
      setProcessingReturn(true);
      setProcessError("");

      const updated =
        await apiFetch<PurchaseReturn>(
          `/purchase-returns/${encodeURIComponent(
            item.return_id,
          )}/process`,
          {
            method: "POST",
          },
        );

      setPurchaseReturns((current) =>
        current.map((entry) =>
          entry.id === updated.id
            ? updated
            : entry,
        ),
      );

      setSelectedPurchaseReturn(updated);
    } catch (err) {
      setProcessError(
        err instanceof Error
          ? err.message
          : "Unable to process supplier return.",
      );
    } finally {
      setProcessingReturn(false);
    }
  }

  return (
    <section className="dashboard admin-returns-page">
      <div className="admin-returns-header">
        <div>
          <div className="page-eyebrow">
            <span>RETAILER</span>
          </div>
          <h1>Returns & Refunds</h1>
          <p>
            Manage your customer returns, supplier returns, and payment refunds.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={loadData}
          disabled={loading}
        >
          <RotateCcw size={16} />
          Refresh
        </button>
      </div>

      <div className="returns-stats-grid">
        <MiniStat
          icon={<RotateCcw />}
          title="Sales Returns"
          value={salesReturns.length}
          tone="blue"
        />

        <MiniStat
          icon={<CheckCircle />}
          title="Processed Returns"
          value={salesProcessed + purchaseProcessed}
          tone="green"
        />

        <MiniStat
          icon={<Clock />}
          title="Pending Returns"
          value={salesRequested + purchaseRequested}
          tone="orange"
        />

        <MiniStat
          icon={<Wallet />}
          title="Total Refunds"
          value={formatAmount(totalRefundAmount)}
          tone="purple"
        />
      </div>

      <div className="returns-panel">
        <div className="returns-panel-header">
          <div>
            <h3>
              {tab === "sales"
                ? "Customer Returns"
                : tab === "purchase"
                  ? "Supplier Returns"
                  : "Payment Refunds"}
            </h3>

            <span>
              {tab === "sales"
                ? `${filteredSalesReturns.length} returns`
                : tab === "purchase"
                  ? `${filteredPurchaseReturns.length} returns`
                  : `${filteredRefunds.length} refunds`}
            </span>
          </div>

          <div className="returns-toolbar">
            <div className="returns-search">
              <Search size={16} />

              <input
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search..."
              />
            </div>

            <select
              value={status}
              onChange={(event) =>
                setStatus(event.target.value)
              }
            >
              <option value="all">All Status</option>

              {tab === "refunds" ? (
                <>
                  <option value="partial">Partial</option>
                  <option value="refunded">Refunded</option>
                </>
              ) : (
                <>
                  <option value="processed">Processed</option>
                  <option value="requested">Requested</option>
                </>
              )}
            </select>
          </div>
        </div>

        <div className="returns-tabs">
          <TabButton
            active={tab === "sales"}
            onClick={() => {
              setTab("sales");
              resetFilters();
            }}
          >
            Customer Returns ({salesReturns.length})
          </TabButton>

          <TabButton
            active={tab === "purchase"}
            onClick={() => {
              setTab("purchase");
              resetFilters();
            }}
          >
            Supplier Returns ({purchaseReturns.length})
          </TabButton>

          <TabButton
            active={tab === "refunds"}
            onClick={() => {
              setTab("refunds");
              resetFilters();
            }}
          >
            Refunds (
            {
              payments.filter(
                (item) =>
                  Number(item.refund_amount) > 0
              ).length
            }
            )
          </TabButton>
        </div>

        {loading && (
          <div className="table-state">
            Loading returns and refunds...
          </div>
        )}

        {!loading && error && (
          <div className="table-state negative">
            {error}
          </div>
        )}

        {!loading && !error && tab === "sales" && (
          <SalesReturnsTable
            returns={filteredSalesReturns}
            formatAmount={formatAmount}
            formatDate={formatDate}
            onSelect={setSelectedSalesReturn}
          />
        )}

        {!loading && !error && tab === "purchase" && (
          <PurchaseReturnsTable
            returns={filteredPurchaseReturns}
            formatAmount={formatAmount}
            formatDate={formatDate}
            onSelect={setSelectedPurchaseReturn}
          />
        )}

        {!loading && !error && tab === "refunds" && (
          <RefundsTable
            payments={filteredRefunds}
            formatAmount={formatAmount}
            formatDate={formatDate}
            onSelect={setSelectedPayment}
          />
        )}
      </div>

      {selectedSalesReturn && (
        <SalesReturnModal
          item={selectedSalesReturn}
          formatAmount={formatAmount}
          formatDate={formatDate}
          onClose={() => setSelectedSalesReturn(null)}
          processingReturn={processingReturn}
          processError={processError}
          refundMethod={refundMethod}
          setRefundMethod={setRefundMethod}
          onProcess={() =>
            processSalesReturn(selectedSalesReturn)
          }
        />
      )}

      {selectedPurchaseReturn && (
        <PurchaseReturnModal
          item={selectedPurchaseReturn}
          formatAmount={formatAmount}
          formatDate={formatDate}
          onClose={() =>
            setSelectedPurchaseReturn(null)
          }
          processingReturn={processingReturn}
          processError={processError}
          onProcess={() =>
            processPurchaseReturn(
              selectedPurchaseReturn
            )
          }
        />
      )}

      {selectedPayment && (
        <RefundModal
          item={selectedPayment}
          formatAmount={formatAmount}
          formatDate={formatDate}
          onClose={() => setSelectedPayment(null)}
        />
      )}

      {!loading && !error && (
        <div
          style={{
            marginTop: "12px",
            fontSize: "13px",
            color: "#667085",
          }}
        >
          Pending sales returns: {salesRequested} ·
          Pending supplier returns: {purchaseRequested}
        </div>
      )}
    </section>
  );
}

function SalesReturnsTable({
  returns,
  formatAmount,
  formatDate,
  onSelect,
}: {
  returns: SalesReturn[];
  formatAmount: (value: string | number) => string;
  formatDate: (value: string) => string;
  onSelect: (item: SalesReturn) => void;
}) {
  if (returns.length === 0) {
    return (
      <div className="table-state">
        No customer returns found.
      </div>
    );
  }

  return (
    <div className="returns-table-wrap">
      <table className="returns-table">
        <thead>
          <tr>
            <th>Return ID</th>
            <th>Invoice</th>
            <th>Customer</th>
            <th>Return Amount</th>
            <th>Refund</th>
            <th>Status</th>
            <th>Requested</th>
          </tr>
        </thead>

        <tbody>
          {returns.map((item) => (
            <tr
              key={item.id}
              onClick={() => onSelect(item)}
              style={{ cursor: "pointer" }}
            >
              <td>
                <strong>{item.return_id}</strong>
              </td>
              <td>{item.invoice_id}</td>
              <td>{item.customer_id}</td>
              <td>
                {formatAmount(item.return_amount)}
              </td>
              <td>
                {formatAmount(item.refund_amount)}
              </td>
              <td>
                <span
                  className={`status-badge ${item.status}`}
                >
                  {item.status}
                </span>
              </td>
              <td>
                {formatDate(item.requested_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PurchaseReturnsTable({
  returns,
  formatAmount,
  formatDate,
  onSelect,
}: {
  returns: PurchaseReturn[];
  formatAmount: (value: string | number) => string;
  formatDate: (value: string) => string;
  onSelect: (item: PurchaseReturn) => void;
}) {
  if (returns.length === 0) {
    return (
      <div className="table-state">
        No supplier returns found.
      </div>
    );
  }

  return (
    <div className="returns-table-wrap">
      <table className="returns-table">
        <thead>
          <tr>
            <th>Return ID</th>
            <th>Purchase Order</th>
            <th>Supplier</th>
            <th>Return Amount</th>
            <th>Status</th>
            <th>Requested</th>
          </tr>
        </thead>

        <tbody>
          {returns.map((item) => (
            <tr
              key={item.id}
              onClick={() => onSelect(item)}
              style={{ cursor: "pointer" }}
            >
              <td>
                <strong>{item.return_id}</strong>
              </td>
              <td>{item.purchase_order_id}</td>
              <td>{item.supplier_id}</td>
              <td>
                {formatAmount(item.return_amount)}
              </td>
              <td>
                <span
                  className={`status-badge ${item.status}`}
                >
                  {item.status}
                </span>
              </td>
              <td>
                {formatDate(item.requested_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RefundsTable({
  payments,
  formatAmount,
  formatDate,
  onSelect,
}: {
  payments: Payment[];
  formatAmount: (value: string | number) => string;
  formatDate: (value: string) => string;
  onSelect: (item: Payment) => void;
}) {
  if (payments.length === 0) {
    return (
      <div className="table-state">
        No payment refunds found.
      </div>
    );
  }

  return (
    <div className="returns-table-wrap">
      <table className="returns-table">
        <thead>
          <tr>
            <th>Payment ID</th>
            <th>Invoice</th>
            <th>Payment Method</th>
            <th>Payment Amount</th>
            <th>Refund Amount</th>
            <th>Refund Status</th>
            <th>Paid</th>
          </tr>
        </thead>

        <tbody>
          {payments.map((item) => (
            <tr
              key={item.id}
              onClick={() => onSelect(item)}
              style={{ cursor: "pointer" }}
            >
              <td>
                <strong>{item.payment_id}</strong>
              </td>
              <td>{item.invoice_id}</td>
              <td>{item.payment_method}</td>
              <td>{formatAmount(item.amount)}</td>
              <td>
                {formatAmount(item.refund_amount)}
              </td>
              <td>
                <span
                  className={`status-badge ${
                    item.refund_status || "partial"
                  }`}
                >
                  {item.refund_status || "Refunded"}
                </span>
              </td>
              <td>{formatDate(item.paid_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      className={`returns-tab ${active ? "active" : ""}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

function SalesReturnModal({
  item,
  formatAmount,
  formatDate,
  onClose,
  processingReturn,
  processError,
  refundMethod,
  setRefundMethod,
  onProcess,
}: {
  item: SalesReturn;
  formatAmount: (value: string | number) => string;
  formatDate: (value: string) => string;
  onClose: () => void;
  processingReturn: boolean;
  processError: string;
  refundMethod: string;
  setRefundMethod: (value: string) => void;
  onProcess: () => void;
}) {
  return (
    <DetailsModal
      title="Customer Return Details"
      subtitle="Return and refund information registered on DigiBills."
      onClose={onClose}
    >
      <Detail label="Return ID" value={item.return_id} />
      <Detail label="Invoice ID" value={item.invoice_id} />
      <Detail label="Customer ID" value={item.customer_id} />
      <Detail label="Status" value={item.status} />
      <Detail
        label="Return Amount"
        value={formatAmount(item.return_amount)}
      />
      <Detail
        label="Refund Amount"
        value={formatAmount(item.refund_amount)}
      />
      <Detail
        label="Refund Method"
        value={item.refund_method || "Not specified"}
      />
      <Detail
        label="Reason"
        value={item.reason || "No reason provided"}
      />
      <Detail
        label="Requested"
        value={formatDate(item.requested_at)}
      />
      <Detail
        label="Processed"
        value={
          item.processed_at
            ? formatDate(item.processed_at)
            : "Not processed"
        }
      />

      {processError && (
        <div className="returns-process-error">
          {processError}
        </div>
      )}

      {item.status === "requested" && (
        <div className="returns-process-panel">
          <label>
            Refund Method
            <select
              value={refundMethod}
              onChange={(event) =>
                setRefundMethod(event.target.value)
              }
              disabled={processingReturn}
            >
              <option value="original">
                Original Payment Method
              </option>
              <option value="cash">Cash</option>
              <option value="bank_transfer">
                Bank Transfer
              </option>
              <option value="upi">UPI</option>
            </select>
          </label>

          <button
            type="button"
            className="primary-button"
            onClick={onProcess}
            disabled={processingReturn}
          >
            {processingReturn
              ? "Processing..."
              : "Process Return"}
          </button>
        </div>
      )}
    </DetailsModal>
  );
}

function PurchaseReturnModal({
  item,
  formatAmount,
  formatDate,
  onClose,
  processingReturn,
  processError,
  onProcess,
}: {
  item: PurchaseReturn;
  formatAmount: (value: string | number) => string;
  formatDate: (value: string) => string;
  onClose: () => void;
  processingReturn: boolean;
  processError: string;
  onProcess: () => void;
}) {
  return (
    <DetailsModal
      title="Supplier Return Details"
      subtitle="Purchase return information registered on DigiBills."
      onClose={onClose}
    >
      <Detail label="Return ID" value={item.return_id} />
      <Detail
        label="Purchase Order ID"
        value={item.purchase_order_id}
      />
      <Detail
        label="Supplier ID"
        value={item.supplier_id}
      />
      <Detail
        label="Location ID"
        value={item.location_id}
      />
      <Detail label="Status" value={item.status} />
      <Detail
        label="Return Amount"
        value={formatAmount(item.return_amount)}
      />
      <Detail
        label="Reason"
        value={item.reason || "No reason provided"}
      />
      <Detail
        label="Requested"
        value={formatDate(item.requested_at)}
      />
      <Detail
        label="Processed"
        value={
          item.processed_at
            ? formatDate(item.processed_at)
            : "Not processed"
        }
      />

      {processError && (
        <div className="returns-process-error">
          {processError}
        </div>
      )}

      {item.status === "requested" && (
        <div className="returns-process-panel">
          <button
            type="button"
            className="primary-button"
            onClick={onProcess}
            disabled={processingReturn}
          >
            {processingReturn
              ? "Processing..."
              : "Process Return"}
          </button>
        </div>
      )}
    </DetailsModal>
  );
}

function RefundModal({
  item,
  formatAmount,
  formatDate,
  onClose,
}: {
  item: Payment;
  formatAmount: (value: string | number) => string;
  formatDate: (value: string) => string;
  onClose: () => void;
}) {
  return (
    <DetailsModal
      title="Payment Refund Details"
      subtitle="Payment and refund information registered on DigiBills."
      onClose={onClose}
    >
      <Detail label="Payment ID" value={item.payment_id} />
      <Detail label="Invoice ID" value={item.invoice_id} />
      <Detail
        label="Payment Method"
        value={item.payment_method}
      />
      <Detail
        label="Payment Amount"
        value={formatAmount(item.amount)}
      />
      <Detail
        label="Refund Amount"
        value={formatAmount(item.refund_amount)}
      />
      <Detail
        label="Refund Status"
        value={item.refund_status || "Not specified"}
      />
      <Detail
        label="Transaction Reference"
        value={
          item.transaction_reference || "Not specified"
        }
      />
      <Detail
        label="Paid At"
        value={formatDate(item.paid_at)}
      />
    </DetailsModal>
  );
}

function DetailsModal({
  title,
  subtitle,
  onClose,
  children,
}: {
  title: string;
  subtitle: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <div
      className="modal-backdrop"
      onClick={onClose}
    >
      <div
        className="returns-details-modal"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <h2>{title}</h2>
            <p>{subtitle}</p>
          </div>

          <button
            type="button"
            className="icon-button"
            onClick={onClose}
          >
            ×
          </button>
        </div>

        <div className="user-details-grid">
          {children}
        </div>
      </div>
    </div>
  );
}

function Detail({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
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
  value: number | string;
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
