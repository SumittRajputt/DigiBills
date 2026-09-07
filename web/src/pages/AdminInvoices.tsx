import {
  Search,
  Receipt,
  CheckCircle,
  Clock,
  XCircle,
  Plus,
} from "lucide-react";
import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { apiFetch } from "../api";

type Customer = {
  id: string;
  customer_id: string;
  full_name: string;
  phone_number: string;
  email: string | null;
  status: string;
};

type InventoryLocation = {
  id: string;
  name: string;
  location_type: string;
  address: string | null;
  is_active: boolean;
};

type ProductVariant = {
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

type ProductUnit = {
  id: string;
  product_variant_id: string;
  serial_number: string;
  status: string;
};

type InvoiceDetailResponse = Invoice & {
  items: Array<{
    id: string;
    invoice_id: string;
    product_variant_id: string;
    product_name: string;
    sku: string | null;
    quantity: number;
    unit_price: string;
    unit_cost: string | null;
    discount_amount: string;
    tax_rate: string;
    taxable_amount: string;
    tax_amount: string;
    line_total: string;
    created_at: string;
  }>;
};

type Invoice = {
  id: string;
  invoice_id: string;
  retailer_id: string;
  employee_id: string | null;
  customer_id: string;
  invoice_number: string | null;
  invoice_date: string;
  subtotal: string;
  discount_amount: string;
  tax_amount: string;
  customer_bill_charge: string;
  total_amount: string;
  payment_status: string;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export default function AdminInvoices() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search);

  const [status, setStatus] = useState("all");
  const [paymentStatus, setPaymentStatus] =
    useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedInvoice, setSelectedInvoice] =
    useState<Invoice | null>(null);

  const [existingPaymentAmount, setExistingPaymentAmount] =
    useState("");

  const [existingPaymentMethod, setExistingPaymentMethod] =
    useState("cash");

  const [existingPaymentLoading, setExistingPaymentLoading] =
    useState(false);

  const [existingPaymentError, setExistingPaymentError] =
    useState("");
  const [showCreateForm, setShowCreateForm] =
    useState(false);

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [locations, setLocations] =
    useState<InventoryLocation[]>([]);
  const [variants, setVariants] =
    useState<ProductVariant[]>([]);
  const [productUnits, setProductUnits] =
    useState<ProductUnit[]>([]);

  const [createCustomerId, setCreateCustomerId] =
    useState("");
  const [customerSearch, setCustomerSearch] =
    useState("");
  const [showCustomerRegistration, setShowCustomerRegistration] =
    useState(false);
  const [newCustomerName, setNewCustomerName] =
    useState("");
  const [newCustomerPhone, setNewCustomerPhone] =
    useState("");
  const [newCustomerEmail, setNewCustomerEmail] =
    useState("");
  const [customerRegistrationLoading, setCustomerRegistrationLoading] =
    useState(false);
  const [createLocationId, setCreateLocationId] =
    useState("");
  const [createSku, setCreateSku] = useState("");
  const [createQuantity, setCreateQuantity] =
    useState("1");
  const [createUnitPrice, setCreateUnitPrice] =
    useState("");
  const [createDiscount, setCreateDiscount] =
    useState("0");
  const [createNotes, setCreateNotes] =
    useState("");

  const [createPaymentStatus, setCreatePaymentStatus] =
    useState("unpaid");

  const [createPaymentMethod, setCreatePaymentMethod] =
    useState("cash");

  const [createPaymentAmount, setCreatePaymentAmount] =
    useState("");

  const [createTransactionReference, setCreateTransactionReference] =
    useState("");
  const [serialNumbers, setSerialNumbers] =
    useState<string[]>([]);
  const [createLoading, setCreateLoading] =
    useState(false);
  const [createError, setCreateError] =
    useState("");

  async function loadInvoices() {
    try {
      setLoading(true);
      setError("");

      const result =
        await apiFetch<Invoice[]>("/invoices");

      setInvoices(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load invoices."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadInvoices();
  }, []);

  useEffect(() => {
    if (!showCreateForm || !createSku) {
      setProductUnits([]);
      setSerialNumbers([]);
      return;
    }

    const variant = variants.find(
      (item) => item.sku === createSku
    );

    if (!variant || !variant.requires_serial_number) {
      setProductUnits([]);
      setSerialNumbers([]);
      return;
    }

    async function loadProductUnits() {
      try {
        setCreateError("");

        const result = await apiFetch<ProductUnit[]>(
          `/product-units/variant/${variant!.id}`
        );

        setProductUnits(result);
      } catch (err) {
        setCreateError(
          err instanceof Error
            ? err.message
            : "Unable to load product units."
        );
        setProductUnits([]);
      }
    }

    loadProductUnits();
  }, [showCreateForm, createSku, variants]);

  useEffect(() => {
    if (!showCreateForm) {
      return;
    }

    async function loadCreateInvoiceData() {
      try {
        setCreateError("");

        const [customerResult, locationResult, variantResult] =
          await Promise.all([
            apiFetch<Customer[]>("/customers"),
            apiFetch<InventoryLocation[]>("/inventory-locations"),
            apiFetch<ProductVariant[]>("/product-variants"),
          ]);

        setCustomers(
          customerResult.filter(
            (customer) => customer.status === "active"
          )
        );

        setLocations(
          locationResult.filter(
            (location) => location.is_active
          )
        );

        setVariants(
          variantResult.filter(
            (variant) => variant.status === "active"
          )
        );
      } catch (err) {
        setCreateError(
          err instanceof Error
            ? err.message
            : "Unable to load invoice form data."
        );
      }
    }

    loadCreateInvoiceData();
  }, [showCreateForm]);

  const matchedCustomers = useMemo(() => {
    const query = customerSearch.trim().toLowerCase();

    if (!query) {
      return [];
    }

    return customers.filter((customer) =>
      customer.customer_id.toLowerCase().includes(query) ||
      customer.phone_number.toLowerCase().includes(query) ||
      customer.full_name.toLowerCase().includes(query)
    );
  }, [customerSearch, customers]);

  const selectedCustomer = customers.find(
    (customer) => customer.customer_id === createCustomerId
  );

  const calculatedInvoiceTotal = useMemo(() => {
    const quantity = Number(createQuantity);
    const unitPrice = Number(createUnitPrice);
    const discount = Number(createDiscount);

    if (
      !Number.isFinite(quantity) ||
      quantity <= 0 ||
      !Number.isFinite(unitPrice) ||
      unitPrice <= 0
    ) {
      return 0;
    }

    const subtotal = quantity * unitPrice;
    const invoiceDiscount = Number.isFinite(discount) && discount >= 0
      ? discount
      : 0;

    return Math.max(subtotal - invoiceDiscount, 0);
  }, [
    createQuantity,
    createUnitPrice,
    createDiscount,
  ]);

  async function handleRegisterCustomer() {
    const fullName = newCustomerName.trim();
    const phoneNumber = newCustomerPhone.trim();
    const email = newCustomerEmail.trim();

    if (!fullName) {
      setCreateError("Customer name is required.");
      return;
    }

    if (!phoneNumber) {
      setCreateError("Customer phone number is required.");
      return;
    }

    try {
      setCustomerRegistrationLoading(true);
      setCreateError("");

      const customer = await apiFetch<Customer>("/customers/register-for-invoice", {
        method: "POST",
        body: JSON.stringify({
          full_name: fullName,
          phone_number: phoneNumber,
          email: email || null,
        }),
      });

      setCustomers((current) => [
        ...current.filter(
          (item) => item.customer_id !== customer.customer_id
        ),
        customer,
      ]);

      setCreateCustomerId(customer.customer_id);
      setCustomerSearch(customer.customer_id);

      setNewCustomerName("");
      setNewCustomerPhone("");
      setNewCustomerEmail("");
      setShowCustomerRegistration(false);
    } catch (err) {
      setCreateError(
        err instanceof Error
          ? err.message
          : "Unable to register customer."
      );
    } finally {
      setCustomerRegistrationLoading(false);
    }
  }

  async function handleCreateInvoice() {
    const selectedVariant = variants.find(
      (variant) => variant.sku === createSku
    );

    if (
      !createCustomerId ||
      !createLocationId ||
      !selectedVariant
    ) {
      setCreateError(
        "Customer, location and product are required."
      );
      return;
    }

    const quantity = Number(createQuantity);
    const unitPrice = Number(createUnitPrice);
    const discount = Number(createDiscount);

    if (!Number.isInteger(quantity) || quantity <= 0) {
      setCreateError("Quantity must be greater than 0.");
      return;
    }

    if (!Number.isFinite(unitPrice) || unitPrice <= 0) {
      setCreateError("Unit price must be greater than 0.");
      return;
    }

    if (!Number.isFinite(discount) || discount < 0) {
      setCreateError("Discount cannot be negative.");
      return;
    }

    if (
      createPaymentStatus === "partial" ||
      createPaymentStatus === "paid"
    ) {
      const paymentAmount = Number(
        createPaymentAmount
      );

      if (
        !Number.isFinite(paymentAmount) ||
        paymentAmount <= 0
      ) {
        setCreateError(
          "Payment amount must be greater than 0."
        );
        return;
      }

      if (
        calculatedInvoiceTotal > 0 &&
        paymentAmount > calculatedInvoiceTotal
      ) {
        setCreateError(
          "Payment amount cannot exceed the invoice total."
        );
        return;
      }

      if (
        createPaymentStatus === "partial" &&
        calculatedInvoiceTotal > 0 &&
        paymentAmount >= calculatedInvoiceTotal
      ) {
        setCreateError(
          "For a partial payment, the amount must be less than the invoice total."
        );
        return;
      }
    }

    let productUnitIds: string[] = [];

    if (selectedVariant.requires_serial_number) {
      const normalizedSerialNumbers = serialNumbers
        .slice(0, quantity)
        .map((serial) => serial.trim());

      if (
        normalizedSerialNumbers.length !== quantity ||
        normalizedSerialNumbers.some(
          (serial) => !serial
        )
      ) {
        setCreateError(
          `Please enter all ${quantity} IMEI/serial numbers.`
        );
        return;
      }

      const uniqueSerialNumbers = new Set(
        normalizedSerialNumbers.map((serial) =>
          serial.toLowerCase()
        )
      );

      if (
        uniqueSerialNumbers.size !==
        normalizedSerialNumbers.length
      ) {
        setCreateError(
          "Duplicate IMEI/serial numbers are not allowed."
        );
        return;
      }
    }

    try {
      setCreateLoading(true);
      setCreateError("");

      if (selectedVariant.requires_serial_number) {
        const normalizedSerialNumbers = serialNumbers
          .slice(0, quantity)
          .map((serial) => serial.trim());

        const createdUnits = await Promise.all(
          normalizedSerialNumbers.map(
            (serialNumber) =>
              apiFetch<ProductUnit>("/product-units", {
                method: "POST",
                body: JSON.stringify({
                  product_variant_id: selectedVariant.id,
                  serial_number: serialNumber,
                  status: "in_stock",
                }),
              })
          )
        );

        productUnitIds = createdUnits.map(
          (unit) => unit.id
        );
      }

      const createdInvoice = await apiFetch<InvoiceDetailResponse>(
        "/invoices",
        {
          method: "POST",
          body: JSON.stringify({
            customer_id: createCustomerId,
            location_id: createLocationId,
            discount_amount: discount.toFixed(2),
            notes: createNotes.trim() || null,
            items: [
              {
                sku: selectedVariant.sku,
                quantity,
                product_unit_ids: productUnitIds,
                unit_price: unitPrice.toFixed(2),
                discount_amount: "0.00",
              },
            ],
          }),
        }
      );

      if (
        createPaymentStatus === "paid" ||
        createPaymentStatus === "partial"
      ) {
        const paymentAmount = Number(
          createPaymentAmount || createdInvoice.total_amount
        );

        if (
          !Number.isFinite(paymentAmount) ||
          paymentAmount <= 0
        ) {
          throw new Error(
            "Payment amount must be greater than 0."
          );
        }

        if (
          paymentAmount >
          Number(createdInvoice.total_amount)
        ) {
          throw new Error(
            "Payment amount cannot exceed the invoice total."
          );
        }

        await apiFetch("/payments", {
          method: "POST",
          body: JSON.stringify({
            invoice_id: createdInvoice.invoice_id,
            amount: paymentAmount.toFixed(2),
            payment_method: createPaymentMethod,
            transaction_reference:
              createTransactionReference.trim() || null,
            notes: null,
          }),
        });
      }

      setShowCreateForm(false);
      setCreateCustomerId("");
      setCustomerSearch("");
      setCreateLocationId("");
      setCreateSku("");
      setCreateQuantity("1");
      setCreateUnitPrice("");
      setCreateDiscount("0");
      setCreateNotes("");
      setCreatePaymentStatus("unpaid");
      setCreatePaymentMethod("cash");
      setCreatePaymentAmount("");
      setCreateTransactionReference("");
      setSerialNumbers([]);
      setProductUnits([]);

      await loadInvoices();
    } catch (err) {
      setCreateError(
        err instanceof Error
          ? err.message
          : "Unable to create invoice."
      );
    } finally {
      setCreateLoading(false);
    }
  }

  async function handleExistingInvoicePayment() {
    if (!selectedInvoice) {
      return;
    }

    const amount = Number(existingPaymentAmount);

    if (!Number.isFinite(amount) || amount <= 0) {
      setExistingPaymentError(
        "Payment amount must be greater than 0."
      );
      return;
    }

    const invoiceTotal = Number(
      selectedInvoice.total_amount
    );

    if (amount > invoiceTotal) {
      setExistingPaymentError(
        "Payment amount cannot exceed the invoice total."
      );
      return;
    }

    if (
      selectedInvoice.payment_status === "paid"
    ) {
      setExistingPaymentError(
        "This invoice is already fully paid."
      );
      return;
    }

    try {
      setExistingPaymentLoading(true);
      setExistingPaymentError("");

      await apiFetch("/payments", {
        method: "POST",
        body: JSON.stringify({
          invoice_id: selectedInvoice.invoice_id,
          amount: amount.toFixed(2),
          payment_method: existingPaymentMethod,
          transaction_reference: null,
          notes: null,
        }),
      });

      setExistingPaymentAmount("");
      setExistingPaymentMethod("cash");
      setSelectedInvoice(null);

      await loadInvoices();
    } catch (err) {
      setExistingPaymentError(
        err instanceof Error
          ? err.message
          : "Unable to record payment."
      );
    } finally {
      setExistingPaymentLoading(false);
    }
  }

  const filteredInvoices = useMemo(() => {
    const query = search.trim().toLowerCase();

    return invoices.filter((invoice) => {
      const invoiceId = String(
        invoice.invoice_id ?? ""
      ).toLowerCase();

      const invoiceNumber = String(
        invoice.invoice_number ?? ""
      ).toLowerCase();

      const retailerId = String(
        invoice.retailer_id ?? ""
      ).toLowerCase();

      const customerId = String(
        invoice.customer_id ?? ""
      ).toLowerCase();

      const invoiceStatus = String(
        invoice.status ?? ""
      ).toLowerCase();

      const invoicePaymentStatus = String(
        invoice.payment_status ?? ""
      ).toLowerCase();

      const matchesSearch =
        !query ||
        invoiceId.includes(query) ||
        invoiceNumber.includes(query) ||
        retailerId.includes(query) ||
        customerId.includes(query);

      const matchesStatus =
        status === "all" ||
        invoiceStatus === status.toLowerCase();

      const matchesPayment =
        paymentStatus === "all" ||
        invoicePaymentStatus === paymentStatus.toLowerCase();

      return (
        matchesSearch &&
        matchesStatus &&
        matchesPayment
      );
    });
  }, [
    invoices,
    search,
    status,
    paymentStatus,
  ]);

  const counts = {
    all: invoices.length,
    active: invoices.filter(
      (invoice) => invoice.status === "active"
    ).length,
    paid: invoices.filter(
      (invoice) =>
        invoice.payment_status === "paid"
    ).length,
    unpaid: invoices.filter(
      (invoice) =>
        invoice.payment_status === "unpaid"
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

  function formatMoney(value: string) {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(Number(value));
  }

  return (
    <section className="dashboard admin-invoices-page">
      <div className="admin-invoices-header">
        <div>
          <div className="page-eyebrow">
            <span>ADMINISTRATION</span>
          </div>
          <h1>Invoices</h1>
          <p>
            Manage invoices, payment status and billing records across DigiBills.
          </p>
        </div>

        <button
          type="button"
          className="primary-button"
          onClick={() => setShowCreateForm(true)}
        >
          <Plus size={16} />
          Create Invoice
        </button>
      </div>

      <div className="invoice-stats-grid">
        <MiniStat
          icon={<Receipt />}
          title="Total Invoices"
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
          icon={<Clock />}
          title="Paid"
          value={counts.paid}
          tone="purple"
        />

        <MiniStat
          icon={<XCircle />}
          title="Unpaid"
          value={counts.unpaid}
          tone="red"
        />
      </div>

      <div className="invoices-panel">
        <div className="invoices-panel-header">
          <div>
            <h3>Invoice Directory</h3>
            <span>
              {filteredInvoices.length} of {invoices.length} invoices
            </span>
          </div>

          <div className="invoices-toolbar">
            <div className="invoices-search">
              <Search size={16} />

              <input
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search invoices..."
              />
            </div>

            <select
              value={paymentStatus}
              onChange={(event) =>
                setPaymentStatus(
                  event.target.value
                )
              }
            >
              <option value="all">
                All Payments
              </option>
              <option value="paid">Paid</option>
              <option value="partial">
                Partial
              </option>
              <option value="unpaid">
                Unpaid
              </option>
            </select>

            <select
              value={status}
              onChange={(event) =>
                setStatus(event.target.value)
              }
            >
              <option value="all">
                All Status
              </option>
              <option value="active">
                Active
              </option>
              <option value="inactive">
                Inactive
              </option>
            </select>
          </div>
        </div>

        {loading && (
          <div className="table-state">
            Loading invoices...
          </div>
        )}

        {!loading && error && (
          <div className="table-state negative">
            {error}
          </div>
        )}

        {!loading && !error && (
          <div className="invoices-table-wrap">
            <table className="invoices-table">
              <thead>
                <tr>
                  <th>Invoice</th>
                  <th>Retailer</th>
                  <th>Customer</th>
                  <th>Date</th>
                  <th>Total</th>
                  <th>Payment</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {filteredInvoices.length > 0 ? (
                  filteredInvoices.map((invoice) => (
                    <tr
                      key={invoice.id}
                      onClick={() =>
                        setSelectedInvoice(invoice)
                      }
                      style={{
                        cursor: "pointer",
                      }}
                    >
                      <td>
                        <div className="invoice-cell">
                          <div className="invoice-avatar">
                            #
                          </div>

                          <div>
                            <strong>
                              {invoice.invoice_number ||
                                invoice.invoice_id}
                            </strong>

                            <small>
                              {invoice.invoice_id}
                            </small>
                          </div>
                        </div>
                      </td>

                      <td>
                        <small>
                          {invoice.retailer_id}
                        </small>
                      </td>

                      <td>
                        <small>
                          {invoice.customer_id}
                        </small>
                      </td>

                      <td>
                        {formatDate(
                          invoice.invoice_date
                        )}
                      </td>

                      <td>
                        <strong>
                          {formatMoney(
                            invoice.total_amount
                          )}
                        </strong>
                      </td>

                      <td>
                        <span
                          className={`status-badge ${invoice.payment_status}`}
                        >
                          {invoice.payment_status}
                        </span>
                      </td>

                      <td>
                        <span
                          className={`status-badge ${invoice.status}`}
                        >
                          {invoice.status}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td
                      colSpan={7}
                      style={{
                        textAlign: "center",
                        padding: "48px 20px",
                      }}
                    >
                      No invoices found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showCreateForm && (
        <div
          className="modal-backdrop"
          onClick={() => setShowCreateForm(false)}
        >
          <div
            className="invoice-details-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="modal-header">
              <div>
                <h2>Create Invoice</h2>
                <p>
                  Create a new invoice for a customer.
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() => setShowCreateForm(false)}
              >
                ×
              </button>
            </div>

            <div className="invoice-details-content">
              {createError && (
                <div className="table-state negative">
                  {createError}
                </div>
              )}

              <div className="invoice-detail-group">
                <div className="invoice-detail-heading">
                  <span className="section-number">1.</span>
                  <div>
                    <h3>Customer & Location</h3>
                    <p>
                      Select who the invoice is for and where the stock
                      will be issued from.
                    </p>
                  </div>
                </div>

                <div className="invoice-detail-grid">
                  <div className="invoice-detail-card customer-search-card">
                    <span>Customer</span>

                    <input
                      type="text"
                      value={customerSearch}
                      onChange={(event) => {
                        setCustomerSearch(event.target.value);
                        setCreateCustomerId("");
                      }}
                      placeholder="Search Customer ID, phone or name..."
                    />

                    {customerSearch.trim() && !selectedCustomer && (
                      <div className="customer-search-results">
                        {matchedCustomers.length > 0 ? (
                          <>
                            {matchedCustomers.slice(0, 5).map((customer) => (
                              <button
                                key={customer.customer_id}
                                type="button"
                                className="customer-search-result"
                                onClick={() => {
                                  setCreateCustomerId(customer.customer_id);
                                  setCustomerSearch(customer.customer_id);
                                }}
                              >
                                <strong>{customer.full_name}</strong>
                                <small>
                                  {customer.customer_id} · {customer.phone_number}
                                </small>
                              </button>
                            ))}

                            <button
                              type="button"
                              className="customer-register-result"
                              onClick={() => {
                                setShowCustomerRegistration(true);
                                setCreateError("");
                              }}
                            >
                              + Register New Customer
                            </button>
                          </>
                        ) : (
                          <>
                            <div className="customer-search-empty">
                              No customer found.
                            </div>

                            <button
                              type="button"
                              className="customer-register-result"
                              onClick={() => {
                                setShowCustomerRegistration(true);
                                setCreateError("");
                              }}
                            >
                              + Register New Customer
                            </button>
                          </>
                        )}
                      </div>
                    )}

                    {selectedCustomer && (
                      <div className="selected-customer-card">
                        <div>
                          <strong>{selectedCustomer.full_name}</strong>
                          <small>
                            {selectedCustomer.customer_id} ·{" "}
                            {selectedCustomer.phone_number}
                          </small>
                        </div>

                        <button
                          type="button"
                          className="customer-clear-button"
                          onClick={() => {
                            setCreateCustomerId("");
                            setCustomerSearch("");
                          }}
                        >
                          Change
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="invoice-detail-card">
                    <span>Inventory Location</span>
                    <select
                      value={createLocationId}
                      onChange={(event) =>
                        setCreateLocationId(event.target.value)
                      }
                    >
                      <option value="">
                        Select location
                      </option>

                      {locations.map((location) => (
                        <option
                          key={location.id}
                          value={location.id}
                        >
                          {location.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>



              <div className="invoice-detail-group">
                <div className="invoice-detail-heading">
                  <span className="section-number">2.</span>
                  <div>
                    <h3>Product</h3>
                    <p>
                      Select the product variant to add to the invoice.
                    </p>
                  </div>
                </div>

                <div className="invoice-detail-grid">
                  <div className="invoice-detail-card">
                    <span>Product / SKU</span>
                    <select
                      value={createSku}
                      onChange={(event) => {
                        const sku = event.target.value;
                        setCreateSku(sku);
                        setSerialNumbers([]);

                        const variant = variants.find(
                          (item) => item.sku === sku
                        );

                        setCreateUnitPrice(
                          variant?.selling_price || ""
                        );

                        setProductUnits([]);
                      }}
                    >
                      <option value="">
                        Select product
                      </option>

                      {variants.map((variant) => (
                        <option
                          key={variant.id}
                          value={variant.sku}
                        >
                          {variant.variant_name} — {variant.sku}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="invoice-detail-card">
                    <span>Quantity</span>
                    <input
                      type="number"
                      min="1"
                      value={createQuantity}
                      onChange={(event) =>
                        setCreateQuantity(event.target.value)
                      }
                    />
                  </div>

                  <div className="invoice-detail-card">
                    <span>Unit Price</span>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={createUnitPrice}
                      onChange={(event) =>
                        setCreateUnitPrice(event.target.value)
                      }
                    />
                  </div>

                  <div className="invoice-detail-card">
                    <span>Discount</span>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={createDiscount}
                      onChange={(event) =>
                        setCreateDiscount(event.target.value)
                      }
                    />
                  </div>
                </div>
              </div>

              {(() => {
                const selectedVariant = variants.find(
                  (item) => item.sku === createSku
                );

                if (!selectedVariant?.requires_serial_number) {
                  return null;
                }

                const quantity = Math.max(
                  1,
                  Number(createQuantity) || 1
                );

                function updateSerialNumber(
                  index: number,
                  value: string
                ) {
                  setSerialNumbers((current) => {
                    const next = [...current];

                    while (next.length < quantity) {
                      next.push("");
                    }

                    next[index] = value;

                    return next.slice(0, quantity);
                  });
                }

                return (
                  <div className="invoice-detail-group">
                    <div className="invoice-detail-heading">
                      <span className="section-number">
                        3.
                      </span>

                      <div>
                        <h3>Product Unit</h3>
                        <p>
                          Enter the IMEI or serial number for each
                          product being sold.
                        </p>
                      </div>
                    </div>

                    <div className="invoice-detail-grid">
                      {Array.from(
                        { length: quantity },
                        (_, index) => (
                          <div
                            className="invoice-detail-card"
                            key={index}
                          >
                            <span>
                              {quantity === 1
                                ? "IMEI / Serial Number"
                                : `IMEI / Serial Number ${index + 1}`}
                            </span>

                            <input
                              type="text"
                              value={serialNumbers[index] || ""}
                              onChange={(event) =>
                                updateSerialNumber(
                                  index,
                                  event.target.value
                                )
                              }
                              placeholder={
                                quantity === 1
                                  ? "Enter IMEI or serial number"
                                  : `Enter serial number ${index + 1}`
                              }
                              autoComplete="off"
                            />
                          </div>
                        )
                      )}
                    </div>
                  </div>
                );
              })()}

              <div className="invoice-detail-group">
                <div className="invoice-detail-heading">
                  <span className="section-number">
                    {variants.find(
                      (item) => item.sku === createSku
                    )?.requires_serial_number
                      ? "5."
                      : "4."}
                  </span>
                  <div>
                    <h3>Payment</h3>
                    <p>
                      Select the payment status and payment method for this invoice.
                    </p>
                  </div>
                </div>

                <div className="invoice-detail-grid">
                  <div className="invoice-detail-card">
                    <span>Payment Status</span>
                    <select
                      value={createPaymentStatus}
                      onChange={(event) => {
                        const value = event.target.value;
                        setCreatePaymentStatus(value);

                        if (value === "unpaid") {
                          setCreatePaymentAmount("");
                          setCreateTransactionReference("");
                        }
                      }}
                    >
                      <option value="unpaid">
                        Unpaid
                      </option>
                      <option value="partial">
                        Partially Paid
                      </option>
                      <option value="paid">
                        Paid
                      </option>
                    </select>
                  </div>

                  {(createPaymentStatus === "paid" ||
                    createPaymentStatus === "partial") && (
                    <>
                      <div className="invoice-detail-card">
                        <span>Payment Method</span>
                        <select
                          value={createPaymentMethod}
                          onChange={(event) =>
                            setCreatePaymentMethod(event.target.value)
                          }
                        >
                          <option value="cash">
                            Cash
                          </option>
                          <option value="upi">
                            UPI
                          </option>
                          <option value="card">
                            Card
                          </option>
                          <option value="bank_transfer">
                            Bank Transfer
                          </option>
                          <option value="other">
                            Other
                          </option>
                        </select>
                      </div>

                      <div className="invoice-detail-card">
                        <span>
                          {createPaymentStatus === "partial"
                            ? "Amount Received"
                            : "Payment Amount"}
                        </span>
                        <input
                          type="number"
                          min="0.01"
                          step="0.01"
                          max={
                            calculatedInvoiceTotal > 0
                              ? calculatedInvoiceTotal
                              : undefined
                          }
                          value={createPaymentAmount}
                          onChange={(event) =>
                            setCreatePaymentAmount(event.target.value)
                          }
                          placeholder={
                            calculatedInvoiceTotal > 0
                              ? calculatedInvoiceTotal.toFixed(2)
                              : "Enter payment amount"
                          }
                        />
                      </div>

                      <div className="invoice-detail-card">
                        <span>Invoice Total</span>
                        <strong>
                          ₹{calculatedInvoiceTotal.toFixed(2)}
                        </strong>
                      </div>

                      <div className="invoice-detail-card">
                        <span>Transaction Reference</span>
                        <input
                          type="text"
                          value={createTransactionReference}
                          onChange={(event) =>
                            setCreateTransactionReference(event.target.value)
                          }
                          placeholder="Optional transaction reference"
                        />
                      </div>
                    </>
                  )}
                </div>

                {createPaymentStatus === "partial" &&
                  Number(createPaymentAmount) > 0 &&
                  calculatedInvoiceTotal > 0 && (
                    <div className="invoice-payment-summary">
                      <div>
                        <span>Paid Now</span>
                        <strong>
                          ₹{Number(createPaymentAmount).toFixed(2)}
                        </strong>
                      </div>

                      <div>
                        <span>Remaining</span>
                        <strong>
                          ₹{Math.max(
                            calculatedInvoiceTotal -
                              Number(createPaymentAmount),
                            0
                          ).toFixed(2)}
                        </strong>
                      </div>
                    </div>
                  )}
              </div>

              <div className="invoice-detail-group">
                <div className="invoice-detail-heading">
                  <span className="section-number">
                    {variants.find(
                      (item) => item.sku === createSku
                    )?.requires_serial_number
                      ? "4."
                      : "3."}
                  </span>
                  <div>
                    <h3>Notes</h3>
                    <p>Optional information for this invoice.</p>
                  </div>
                </div>

                <div className="invoice-notes">
                  <textarea
                    value={createNotes}
                    onChange={(event) =>
                      setCreateNotes(event.target.value)
                    }
                    placeholder="Add invoice notes..."
                    rows={4}
                  />
                </div>
              </div>
            </div>

            <div className="invoice-form-footer">
              <button
                type="button"
                className="secondary-button"
                onClick={() => setShowCreateForm(false)}
              >
                Cancel
              </button>

              <button
                type="button"
                className="primary-button"
                disabled={
                  createLoading ||
                  !createCustomerId ||
                  !createLocationId ||
                  !createSku ||
                  (
                    variants.find(
                      (variant) => variant.sku === createSku
                    )?.requires_serial_number === true &&
                    (
                      serialNumbers.length !== Number(createQuantity) ||
                      serialNumbers.some(
                        (serial) => !serial.trim()
                      )
                    )
                  )
                }
                onClick={handleCreateInvoice}
              >
                {createLoading
                  ? "Creating..."
                  : "Create Invoice"}
              </button>
            </div>
          </div>
        </div>
      )}



      {showCustomerRegistration && (
        <div
          className="customer-registration-modal-backdrop"
          onClick={() => {
            setShowCustomerRegistration(false);
            setNewCustomerName("");
            setNewCustomerPhone("");
            setNewCustomerEmail("");
          }}
        >
          <div
            className="customer-registration-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="customer-registration-modal-header">
              <div>
                <h2>Register New Customer</h2>
                <p>
                  Create the customer profile before continuing with this invoice.
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() => {
                  setShowCustomerRegistration(false);
                  setNewCustomerName("");
                  setNewCustomerPhone("");
                  setNewCustomerEmail("");
                }}
              >
                ×
              </button>
            </div>

            <div className="customer-registration-modal-content">
              <div className="customer-registration-modal-form">

                <label>
                  <span>Full Name *</span>
                  <input
                    type="text"
                    value={newCustomerName}
                    onChange={(event) =>
                      setNewCustomerName(event.target.value)
                    }
                    placeholder="Enter customer name"
                    autoFocus
                  />
                </label>

                <label>
                  <span>Phone Number *</span>
                  <input
                    type="tel"
                    value={newCustomerPhone}
                    onChange={(event) =>
                      setNewCustomerPhone(event.target.value)
                    }
                    placeholder="Enter phone number"
                  />
                </label>

                <label>
                  <span>Email</span>
                  <input
                    type="email"
                    value={newCustomerEmail}
                    onChange={(event) =>
                      setNewCustomerEmail(event.target.value)
                    }
                    placeholder="Enter email address (optional)"
                  />
                </label>

              </div>

              {createError && (
                <div className="customer-registration-modal-error">
                  {createError}
                </div>
              )}
            </div>

            <div className="customer-registration-modal-footer">
              <button
                type="button"
                className="secondary-button"
                onClick={() => {
                  setShowCustomerRegistration(false);
                  setNewCustomerName("");
                  setNewCustomerPhone("");
                  setNewCustomerEmail("");
                }}
              >
                Cancel
              </button>

              <button
                type="button"
                className="primary-button"
                onClick={handleRegisterCustomer}
                disabled={
                  customerRegistrationLoading ||
                  !newCustomerName.trim() ||
                  !newCustomerPhone.trim()
                }
              >
                {customerRegistrationLoading
                  ? "Registering..."
                  : "Register Customer"}
              </button>
            </div>
          </div>
        </div>
      )}

      {selectedInvoice && (
        <div
          className="modal-backdrop"
          onClick={() =>
            setSelectedInvoice(null)
          }
        >
          <div
            className="invoice-details-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="modal-header">
              <div>
                <h2>Invoice Details</h2>
                <p>
                  Invoice information registered
                  on DigiBills.
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() =>
                  setSelectedInvoice(null)
                }
              >
                ×
              </button>
            </div>

            <div className="invoice-details-content">

              <div className="invoice-detail-group">
                <div className="invoice-detail-heading">
                  <span className="section-number">1.</span>
                  <div>
                    <h3>Invoice Information</h3>
                    <p>Core identification and ownership details.</p>
                  </div>
                </div>

                <div className="invoice-detail-grid">
                  <div className="invoice-detail-card">
                    <span>Invoice ID</span>
                    <strong>{selectedInvoice.invoice_id}</strong>
                  </div>

                  <div className="invoice-detail-card">
                    <span>Invoice Number</span>
                    <strong>{selectedInvoice.invoice_number || "—"}</strong>
                  </div>

                  <div className="invoice-detail-card">
                    <span>Retailer</span>
                    <strong>{selectedInvoice.retailer_id}</strong>
                  </div>

                  <div className="invoice-detail-card">
                    <span>Customer</span>
                    <strong>{selectedInvoice.customer_id}</strong>
                  </div>

                  <div className="invoice-detail-card">
                    <span>Invoice Date</span>
                    <strong>{formatDate(selectedInvoice.invoice_date)}</strong>
                  </div>
                </div>
              </div>

              <div className="invoice-detail-group">
                <div className="invoice-detail-heading">
                  <span className="section-number">2.</span>
                  <div>
                    <h3>Financial Summary</h3>
                    <p>Breakdown of the invoice amount.</p>
                  </div>
                </div>

                <div className="invoice-amount-grid">
                  <div className="invoice-detail-card">
                    <span>Subtotal</span>
                    <strong>{formatMoney(selectedInvoice.subtotal)}</strong>
                  </div>

                  <div className="invoice-detail-card">
                    <span>Discount</span>
                    <strong>{formatMoney(selectedInvoice.discount_amount)}</strong>
                  </div>

                  <div className="invoice-detail-card">
                    <span>GST Included</span>
                    <strong>{formatMoney(selectedInvoice.tax_amount)}</strong>
                  </div>

                  <div className="invoice-total-card">
                    <span>Total Amount</span>
                    <strong>{formatMoney(selectedInvoice.total_amount)}</strong>
                  </div>
                </div>
              </div>

              <div className="invoice-detail-group">
                <div className="invoice-detail-heading">
                  <span className="section-number">3.</span>
                  <div>
                    <h3>Payment & Status</h3>
                    <p>Current payment and invoice state.</p>
                  </div>
                </div>

                <div className="invoice-detail-grid">
                  <div className="invoice-detail-card">
                    <span>Payment Status</span>
                    <strong className={`invoice-status-value ${selectedInvoice.payment_status}`}>
                      {selectedInvoice.payment_status}
                    </strong>
                  </div>

                  <div className="invoice-detail-card">
                    <span>Invoice Status</span>
                    <strong className={`invoice-status-value ${selectedInvoice.status}`}>
                      {selectedInvoice.status}
                    </strong>
                  </div>
                </div>
              </div>

              <div className="invoice-detail-group">
                <div className="invoice-detail-heading">
                  <span className="section-number">4.</span>
                  <div>
                    <h3>Record Payment</h3>
                    <p>
                      Record a payment against this existing invoice.
                    </p>
                  </div>
                </div>

                {existingPaymentError && (
                  <div className="table-state negative">
                    {existingPaymentError}
                  </div>
                )}

                <div className="invoice-detail-grid">
                  <div className="invoice-detail-card">
                    <span>Payment Method</span>
                    <select
                      value={existingPaymentMethod}
                      onChange={(event) =>
                        setExistingPaymentMethod(
                          event.target.value
                        )
                      }
                      disabled={existingPaymentLoading}
                    >
                      <option value="cash">Cash</option>
                      <option value="upi">UPI</option>
                      <option value="card">Card</option>
                      <option value="bank_transfer">
                        Bank Transfer
                      </option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <div className="invoice-detail-card">
                    <span>Amount Received</span>
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      max={Number(
                        selectedInvoice.total_amount
                      )}
                      value={existingPaymentAmount}
                      onChange={(event) =>
                        setExistingPaymentAmount(
                          event.target.value
                        )
                      }
                      placeholder="Enter amount"
                      disabled={existingPaymentLoading}
                    />
                  </div>

                  <div className="invoice-detail-card">
                    <span>Invoice Total</span>
                    <strong>
                      {formatMoney(
                        selectedInvoice.total_amount
                      )}
                    </strong>
                  </div>

                  <div className="invoice-detail-card">
                    <span>Remaining After Payment</span>
                    <strong>
                      {formatMoney(
                        Math.max(
                          Number(
                            selectedInvoice.total_amount
                          ) -
                            Number(
                              existingPaymentAmount || 0
                            ),
                          0
                        ).toFixed(2)
                      )}
                    </strong>
                  </div>
                </div>

                <div
                  style={{
                    display: "flex",
                    justifyContent: "flex-end",
                    marginTop: "16px",
                  }}
                >
                  <button
                    type="button"
                    className="primary-button"
                    onClick={
                      handleExistingInvoicePayment
                    }
                    disabled={
                      existingPaymentLoading ||
                      selectedInvoice.payment_status === "paid"
                    }
                  >
                    {existingPaymentLoading
                      ? "Recording..."
                      : "Record Payment"}
                  </button>
                </div>
              </div>

              <div className="invoice-notes">
                <span>Notes</span>
                <p>
                  {selectedInvoice.notes || "No notes available for this invoice."}
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
