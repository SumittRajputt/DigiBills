import { useEffect, useState } from "react";
import {
  Bell,
  Building2,
  CreditCard,
  FileText,
  Save,
  ShieldCheck,
  Users,
} from "lucide-react";

import { apiFetch } from "../api";

type SettingsSection =
  | "business"
  | "invoice"
  | "billing"
  | "users"
  | "notifications"
  | "security";

type PaymentConfiguration = {
  id: string;
  per_bill_charge: string;
  max_cash_due_invoices: number;
  salesman_commission_percent: string;
};

type PaymentConfigurationForm = {
  perBillCharge: string;
  maxCashDueInvoices: string;
  salesmanCommissionPercent: string;
};


type PlanLimit = {
  unlimited: boolean;
  limit: number | null;
};

type CustomerPlan = {
  id: string;
  plan_id: string;
  name: string;
  description: string | null;
  billing_type: string;
  monthly_price: string;
  yearly_price: string;
  per_bill_price: string;
  trial_days: number;
  features: string[];
  is_active: boolean;
};

type RetailerPlan = {
  id: string;
  plan_id: string;
  name: string;
  description: string | null;
  billing_type: string;
  monthly_price: string;
  yearly_price: string;
  trial_days: number;
  features: string[];
  limits: {
    invoices?: PlanLimit;
    employees?: PlanLimit;
    products?: PlanLimit;
  };
  is_active: boolean;
};

export default function AdminSettings() {
  const [activeSection, setActiveSection] =
    useState<SettingsSection>("business");

  const [businessName, setBusinessName] = useState("DigiBills");
  const [email, setEmail] = useState("support@digibills.com");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");

  const [paymentConfiguration, setPaymentConfiguration] =
    useState<PaymentConfigurationForm>({
      perBillCharge: "9.00",
      maxCashDueInvoices: "20",
      salesmanCommissionPercent: "20.00",
    });

  const [billingLoading, setBillingLoading] = useState(false);
  const [billingSaving, setBillingSaving] = useState(false);
  const [billingError, setBillingError] = useState("");
  const [billingSuccess, setBillingSuccess] = useState("");


  const [retailerPlans, setRetailerPlans] = useState<
    RetailerPlan[]
  >([]);
  const [retailerPlansLoading, setRetailerPlansLoading] =
    useState(false);
  const [retailerPlanSaving, setRetailerPlanSaving] =
    useState<string | null>(null);
  const [retailerPlansError, setRetailerPlansError] =
    useState("");
  const [retailerPlansSuccess, setRetailerPlansSuccess] =
    useState("");

  const [customerPlans, setCustomerPlans] = useState<
    CustomerPlan[]
  >([]);
  const [customerPlansLoading, setCustomerPlansLoading] =
    useState(false);
  const [customerPlanSaving, setCustomerPlanSaving] =
    useState<string | null>(null);
  const [customerPlansError, setCustomerPlansError] =
    useState("");
  const [customerPlansSuccess, setCustomerPlansSuccess] =
    useState("");

  const sections = [
    {
      id: "business" as const,
      label: "Business",
      description: "Business profile and contact details",
      icon: Building2,
    },
    {
      id: "invoice" as const,
      label: "Invoices",
      description: "Invoice numbering and billing defaults",
      icon: FileText,
    },
    {
      id: "billing" as const,
      label: "Subscriptions & Billing",
      description: "Plans, pricing and billing behaviour",
      icon: CreditCard,
    },
    {
      id: "users" as const,
      label: "Users & Roles",
      description: "Roles and access control",
      icon: Users,
    },
    {
      id: "notifications" as const,
      label: "Notifications",
      description: "System notification preferences",
      icon: Bell,
    },
    {
      id: "security" as const,
      label: "Security",
      description: "Security and account controls",
      icon: ShieldCheck,
    },
  ];

  useEffect(() => {
    if (activeSection !== "billing") {
      return;
    }

    let cancelled = false;

    async function loadPaymentConfiguration() {
      setBillingLoading(true);
      setBillingError("");
      setBillingSuccess("");

      try {
        const configuration =
          await apiFetch<PaymentConfiguration>(
            "/admin/payment-configuration"
          );

        if (cancelled) {
          return;
        }

        setPaymentConfiguration({
          perBillCharge: configuration.per_bill_charge,
          maxCashDueInvoices: String(
            configuration.max_cash_due_invoices
          ),
          salesmanCommissionPercent:
            configuration.salesman_commission_percent,
        });
      } catch (error) {
        if (cancelled) {
          return;
        }

        setBillingError(
          error instanceof Error
            ? error.message
            : "Unable to load payment configuration."
        );
      } finally {
        if (!cancelled) {
          setBillingLoading(false);
        }
      }
    }

    void loadPaymentConfiguration();

    return () => {
      cancelled = true;
    };
  }, [activeSection]);

  useEffect(() => {
    if (activeSection !== "billing") {
      return;
    }

    let cancelled = false;

    async function loadRetailerPlans() {
      setRetailerPlansLoading(true);
      setRetailerPlansError("");
      setRetailerPlansSuccess("");

      try {
        const plans = await apiFetch<RetailerPlan[]>(
          "/admin/retailer-plans"
        );

        if (cancelled) {
          return;
        }

        setRetailerPlans(plans);
      } catch (error) {
        if (cancelled) {
          return;
        }

        setRetailerPlansError(
          error instanceof Error
            ? error.message
            : "Unable to load retailer subscription plans."
        );
      } finally {
        if (!cancelled) {
          setRetailerPlansLoading(false);
        }
      }
    }

    void loadRetailerPlans();

    return () => {
      cancelled = true;
    };
  }, [activeSection]);

  useEffect(() => {
    if (activeSection !== "billing") {
      return;
    }

    let cancelled = false;

    async function loadCustomerPlans() {
      setCustomerPlansLoading(true);
      setCustomerPlansError("");
      setCustomerPlansSuccess("");

      try {
        const plans = await apiFetch<CustomerPlan[]>(
          "/admin/customer-plans"
        );

        if (cancelled) {
          return;
        }

        setCustomerPlans(plans);
      } catch (error) {
        if (cancelled) {
          return;
        }

        setCustomerPlansError(
          error instanceof Error
            ? error.message
            : "Unable to load customer subscription plans."
        );
      } finally {
        if (!cancelled) {
          setCustomerPlansLoading(false);
        }
      }
    }

    void loadCustomerPlans();

    return () => {
      cancelled = true;
    };
  }, [activeSection]);

  function updateCustomerPlan(
    planId: string,
    updater: (plan: CustomerPlan) => CustomerPlan
  ) {
    setCustomerPlans((current) =>
      current.map((plan) =>
        plan.plan_id === planId
          ? updater(plan)
          : plan
      )
    );
  }

  async function saveCustomerPlan(plan: CustomerPlan) {
    setCustomerPlanSaving(plan.plan_id);
    setCustomerPlansError("");
    setCustomerPlansSuccess("");

    try {
      const updated = await apiFetch<CustomerPlan>(
        `/admin/customer-plans/${plan.plan_id}`,
        {
          method: "PUT",
          body: JSON.stringify({
            name: plan.name,
            description: plan.description,
            billing_type: plan.billing_type,
            monthly_price: Number(plan.monthly_price),
            yearly_price: Number(plan.yearly_price),
            per_bill_price: Number(plan.per_bill_price),
            trial_days: plan.trial_days,
            features: plan.features,
            is_active: plan.is_active,
          }),
        }
      );

      setCustomerPlans((current) =>
        current.map((item) =>
          item.plan_id === updated.plan_id
            ? updated
            : item
        )
      );

      setCustomerPlansSuccess(
        `${updated.name} updated successfully.`
      );
    } catch (error) {
      setCustomerPlansError(
        error instanceof Error
          ? error.message
          : "Unable to save customer subscription plan."
      );
    } finally {
      setCustomerPlanSaving(null);
    }
  }

  function updateRetailerPlan(
    planId: string,
    updater: (plan: RetailerPlan) => RetailerPlan
  ) {
    setRetailerPlans((current) =>
      current.map((plan) =>
        plan.plan_id === planId
          ? updater(plan)
          : plan
      )
    );
  }

  function updatePlanLimit(
    planId: string,
    limitName:
      | "invoices"
      | "employees"
      | "products",
    updater: (limit: PlanLimit) => PlanLimit
  ) {
    updateRetailerPlan(planId, (plan) => ({
      ...plan,
      limits: {
        ...plan.limits,
        [limitName]: updater(
          plan.limits[limitName] ?? {
            unlimited: true,
            limit: null,
          }
        ),
      },
    }));
  }

  async function saveRetailerPlan(
    plan: RetailerPlan
  ) {
    setRetailerPlanSaving(plan.plan_id);
    setRetailerPlansError("");
    setRetailerPlansSuccess("");

    try {
      const updatedPlan =
        await apiFetch<RetailerPlan>(
          `/admin/retailer-plans/${plan.plan_id}`,
          {
            method: "PUT",
            body: JSON.stringify({
              name: plan.name,
              description: plan.description,
              billing_type: plan.billing_type,
              monthly_price: plan.monthly_price,
              yearly_price: plan.yearly_price,
              trial_days: plan.trial_days,
              features: plan.features,
              limits: plan.limits,
              is_active: plan.is_active,
            }),
          }
        );

      setRetailerPlans((current) =>
        current.map((currentPlan) =>
          currentPlan.plan_id ===
          updatedPlan.plan_id
            ? updatedPlan
            : currentPlan
        )
      );

      setRetailerPlansSuccess(
        `${updatedPlan.name} plan saved successfully.`
      );
    } catch (error) {
      setRetailerPlansError(
        error instanceof Error
          ? error.message
          : `Unable to save ${plan.name} plan.`
      );
    } finally {
      setRetailerPlanSaving(null);
    }
  }

  async function saveSettings() {
    if (activeSection !== "billing") {
      alert("Settings saved locally for this session.");
      return;
    }

    setBillingSaving(true);
    setBillingError("");
    setBillingSuccess("");

    try {
      const configuration =
        await apiFetch<PaymentConfiguration>(
          "/admin/payment-configuration",
          {
            method: "PUT",
            body: JSON.stringify({
              per_bill_charge:
                paymentConfiguration.perBillCharge,
              max_cash_due_invoices:
                Number(
                  paymentConfiguration.maxCashDueInvoices
                ),
              salesman_commission_percent:
                paymentConfiguration.salesmanCommissionPercent,
            }),
          }
        );

      setPaymentConfiguration({
        perBillCharge: configuration.per_bill_charge,
        maxCashDueInvoices: String(
          configuration.max_cash_due_invoices
        ),
        salesmanCommissionPercent:
          configuration.salesman_commission_percent,
      });

      setBillingSuccess(
        "Payment settings saved successfully."
      );
    } catch (error) {
      setBillingError(
        error instanceof Error
          ? error.message
          : "Unable to save payment configuration."
      );
    } finally {
      setBillingSaving(false);
    }
  }

  return (
    <div className="settings-page">
      <div className="page-heading">
        <div>
          <h1>System Settings</h1>
          <p>
            Manage DigiBills configuration, billing, users and
            security.
          </p>
        </div>

        <button
          type="button"
          className="primary-button"
          onClick={saveSettings}
          disabled={
            activeSection === "billing" &&
            (billingLoading || billingSaving)
          }
        >
          <Save size={16} />
          {activeSection === "billing" && billingSaving
            ? "Saving..."
            : "Save changes"}
        </button>
      </div>

      <div className="settings-layout">
        <aside className="settings-menu">
          {sections.map((section) => {
            const Icon = section.icon;

            return (
              <button
                key={section.id}
                type="button"
                className={`settings-menu-item ${
                  activeSection === section.id ? "active" : ""
                }`}
                onClick={() => setActiveSection(section.id)}
              >
                <Icon size={18} />

                <span>
                  <strong>{section.label}</strong>
                  <small>{section.description}</small>
                </span>
              </button>
            );
          })}
        </aside>

        <section className="settings-card">
          {activeSection === "business" && (
            <>
              <div className="settings-section-header">
                <h2>Business Information</h2>
                <p>
                  Configure the basic information displayed
                  throughout DigiBills.
                </p>
              </div>

              <div className="settings-form-grid">
                <label>
                  Business name
                  <input
                    value={businessName}
                    onChange={(event) =>
                      setBusinessName(event.target.value)
                    }
                  />
                </label>

                <label>
                  Support email
                  <input
                    type="email"
                    value={email}
                    onChange={(event) =>
                      setEmail(event.target.value)
                    }
                  />
                </label>

                <label>
                  Support phone
                  <input
                    value={phone}
                    onChange={(event) =>
                      setPhone(event.target.value)
                    }
                    placeholder="Enter support phone"
                  />
                </label>

                <label className="full-width">
                  Business address
                  <textarea
                    value={address}
                    onChange={(event) =>
                      setAddress(event.target.value)
                    }
                    placeholder="Enter business address"
                    rows={4}
                  />
                </label>
              </div>
            </>
          )}

          {activeSection === "invoice" && (
            <>
              <div className="settings-section-header">
                <h2>Invoice Settings</h2>
                <p>
                  Configure how invoices are generated and
                  presented.
                </p>
              </div>

              <div className="settings-form-grid">
                <label>
                  Invoice prefix
                  <input defaultValue="INV-" />
                </label>

                <label>
                  Default payment terms
                  <select defaultValue="Due immediately">
                    <option>Due immediately</option>
                    <option>7 days</option>
                    <option>15 days</option>
                    <option>30 days</option>
                  </select>
                </label>

                <label>
                  Currency
                  <select defaultValue="INR">
                    <option>INR</option>
                    <option>USD</option>
                    <option>EUR</option>
                  </select>
                </label>

                <label>
                  Default tax rate
                  <input
                    type="number"
                    defaultValue="0"
                    min="0"
                  />
                </label>
              </div>
            </>
          )}

          {activeSection === "billing" && (
            <>
              <div className="settings-section-header">
                <h2>Subscriptions & Billing</h2>
                <p>
                  Manage DigiBills payment rules, customer
                  subscriptions and salesman commissions.
                </p>
              </div>

              {billingLoading && (
                <div className="settings-status">
                  Loading payment configuration...
                </div>
              )}

              {billingError && (
                <div className="settings-status settings-status-error">
                  {billingError}
                </div>
              )}

              {billingSuccess && (
                <div className="settings-status settings-status-success">
                  {billingSuccess}
                </div>
              )}

              <div className="settings-form-grid">
                <label>
                  Customer transfer fee
                  <div className="settings-input-with-prefix">
                    <span>₹</span>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={
                        paymentConfiguration.perBillCharge
                      }
                      onChange={(event) =>
                        setPaymentConfiguration((current) => ({
                          ...current,
                          perBillCharge: event.target.value,
                        }))
                      }
                    />
                  </div>
                  <small>
                    Charged when a customer uses DigiBills
                    instead of a paper bill.
                  </small>
                </label>

                <label>
                  Maximum cash/due invoices
                  <input
                    type="number"
                    min="0"
                    step="1"
                    value={
                      paymentConfiguration.maxCashDueInvoices
                    }
                    onChange={(event) =>
                      setPaymentConfiguration((current) => ({
                        ...current,
                        maxCashDueInvoices:
                          event.target.value,
                      }))
                    }
                  />
                  <small>
                    Number of cash/due DigiBills invoices a
                    retailer can create before payment is
                    required.
                  </small>
                </label>

                <label>
                  Salesman commission
                  <div className="settings-input-with-suffix">
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.01"
                      value={
                        paymentConfiguration.salesmanCommissionPercent
                      }
                      onChange={(event) =>
                        setPaymentConfiguration((current) => ({
                          ...current,
                          salesmanCommissionPercent:
                            event.target.value,
                        }))
                      }
                    />
                    <span>%</span>
                  </div>
                  <small>
                    Commission applied to eligible DigiBills
                    payments and annual subscriptions.
                  </small>
                </label>
              </div>

              <div className="settings-info-grid">
                <div>
                  <strong>Customer subscription plans</strong>
                  <span>
                    Monthly, yearly and pay-per-bill pricing is
                    configured in Customer Subscription Plans below.
                  </span>
                </div>

                <div>
                  <strong>Paper bill</strong>
                  <span>
                    Customers who do not use DigiBills can
                    receive a retailer-issued paper bill.
                  </span>
                </div>

                <div>
                  <strong>Salesman commission</strong>
                  <span>
                    Eligible DigiBills transactions contribute
                    to the configured salesman commission.
                  </span>
                </div>
              </div>

              <div className="retailer-plans-section">
                <div className="settings-section-header retailer-plans-header">
                  <div>
                    <h3>Customer Subscription Plans</h3>
                    <p>
                      Configure pricing and billing settings for
                      customer subscriptions.
                    </p>
                  </div>
                </div>

                {customerPlansLoading && (
                  <div className="settings-status">
                    Loading customer subscription plans...
                  </div>
                )}

                {customerPlansError && (
                  <div className="settings-status settings-status-error">
                    {customerPlansError}
                  </div>
                )}

                {customerPlansSuccess && (
                  <div className="settings-status settings-status-success">
                    {customerPlansSuccess}
                  </div>
                )}

                {!customerPlansLoading &&
                  customerPlans.length > 0 && (
                    <div className="retailer-plan-grid">
                      {customerPlans
                        .sort((a, b) => {
                          const order: Record<string, number> = {
                            "CUS-MONTHLY": 1,
                            "CUS-YEARLY": 2,
                            "CUS-PER-BILL": 3,
                          };

                          return (
                            (order[a.plan_id] ?? 99) -
                            (order[b.plan_id] ?? 99)
                          );
                        })
                        .map((plan) => (
                          <div
                            className={`retailer-plan-card ${
                              plan.is_active ? "" : "inactive"
                            }`}
                            key={plan.plan_id}
                          >
                            <div className="retailer-plan-card-header">
                              <div>
                                <span className="retailer-plan-badge">
                                  {plan.billing_type.replace(
                                    "_",
                                    " "
                                  )}
                                </span>

                                <h4>{plan.name}</h4>

                                <span className="retailer-plan-id">
                                  Customer subscription
                                </span>
                              </div>

                              <label className="retailer-plan-active">
                                <input
                                  type="checkbox"
                                  checked={plan.is_active}
                                  onChange={(event) =>
                                    updateCustomerPlan(
                                      plan.plan_id,
                                      (current) => ({
                                        ...current,
                                        is_active:
                                          event.target.checked,
                                      })
                                    )
                                  }
                                />
                                Active
                              </label>
                            </div>

                            <div className="retailer-plan-fields">
                              <label className="full-width">
                                Plan name
                                <input
                                  type="text"
                                  value={plan.name}
                                  onChange={(event) =>
                                    updateCustomerPlan(
                                      plan.plan_id,
                                      (current) => ({
                                        ...current,
                                        name: event.target.value,
                                      })
                                    )
                                  }
                                />
                              </label>

                              <label className="full-width">
                                Description
                                <input
                                  type="text"
                                  value={plan.description ?? ""}
                                  onChange={(event) =>
                                    updateCustomerPlan(
                                      plan.plan_id,
                                      (current) => ({
                                        ...current,
                                        description:
                                          event.target.value,
                                      })
                                    )
                                  }
                                />
                              </label>

                              <label>
                                Billing type
                                <select
                                  value={plan.billing_type}
                                  onChange={(event) =>
                                    updateCustomerPlan(
                                      plan.plan_id,
                                      (current) => ({
                                        ...current,
                                        billing_type:
                                          event.target.value,
                                      })
                                    )
                                  }
                                >
                                  <option value="monthly">
                                    Monthly
                                  </option>
                                  <option value="yearly">
                                    Yearly
                                  </option>
                                  <option value="per_bill">
                                    Per Bill
                                  </option>
                                </select>
                              </label>

                              <label>
                                Trial days
                                <input
                                  type="number"
                                  min="0"
                                  step="1"
                                  value={plan.trial_days}
                                  onChange={(event) =>
                                    updateCustomerPlan(
                                      plan.plan_id,
                                      (current) => ({
                                        ...current,
                                        trial_days:
                                          Number(
                                            event.target.value
                                          ),
                                      })
                                    )
                                  }
                                />
                              </label>

                              <label>
                                Monthly price
                                <div className="settings-input-with-prefix">
                                  <span>₹</span>
                                  <input
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    value={plan.monthly_price}
                                    onChange={(event) =>
                                      updateCustomerPlan(
                                        plan.plan_id,
                                        (current) => ({
                                          ...current,
                                          monthly_price:
                                            event.target.value,
                                        })
                                      )
                                    }
                                  />
                                </div>
                              </label>

                              <label>
                                Yearly price
                                <div className="settings-input-with-prefix">
                                  <span>₹</span>
                                  <input
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    value={plan.yearly_price}
                                    onChange={(event) =>
                                      updateCustomerPlan(
                                        plan.plan_id,
                                        (current) => ({
                                          ...current,
                                          yearly_price:
                                            event.target.value,
                                        })
                                      )
                                    }
                                  />
                                </div>
                              </label>

                              <label>
                                Per-bill price
                                <div className="settings-input-with-prefix">
                                  <span>₹</span>
                                  <input
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    value={plan.per_bill_price}
                                    onChange={(event) =>
                                      updateCustomerPlan(
                                        plan.plan_id,
                                        (current) => ({
                                          ...current,
                                          per_bill_price:
                                            event.target.value,
                                        })
                                      )
                                    }
                                  />
                                </div>
                              </label>
                            </div>

                            <div className="retailer-plan-card-footer">
                              <span>
                                ID: {plan.plan_id}
                              </span>

                              <button
                                type="button"
                                className="primary-button"
                                disabled={
                                  customerPlanSaving ===
                                  plan.plan_id
                                }
                                onClick={() =>
                                  void saveCustomerPlan(plan)
                                }
                              >
                                <Save size={16} />
                                {customerPlanSaving ===
                                plan.plan_id
                                  ? "Saving..."
                                  : "Save Plan"}
                              </button>
                            </div>
                          </div>
                        ))}
                    </div>
                  )}
              </div>

              <div className="retailer-plans-section">
                <div className="settings-section-header retailer-plans-header">
                  <div>
                    <h3>Retailer Subscription Plans</h3>
                    <p>
                      Configure pricing, limits and features for
                      retailer subscriptions.
                    </p>
                  </div>
                </div>

                {retailerPlansLoading && (
                  <div className="settings-status">
                    Loading retailer subscription plans...
                  </div>
                )}

                {retailerPlansError && (
                  <div className="settings-status settings-status-error">
                    {retailerPlansError}
                  </div>
                )}

                {retailerPlansSuccess && (
                  <div className="settings-status settings-status-success">
                    {retailerPlansSuccess}
                  </div>
                )}

                {!retailerPlansLoading &&
                  retailerPlans.length > 0 && (
                    <div className="retailer-plan-grid">
                      {retailerPlans
                        .filter(
                          (plan) =>
                            plan.plan_id === "retailer_basic" ||
                            plan.plan_id === "retailer_plus" ||
                            plan.plan_id === "retailer_pro"
                        )
                        .sort((a, b) => {
                          const order: Record<string, number> = {
                            retailer_basic: 1,
                            retailer_plus: 2,
                            retailer_pro: 3,
                          };

                          return (
                            order[a.plan_id] -
                            order[b.plan_id]
                          );
                        })
                        .map((plan) => (
                          <div
                            className={`retailer-plan-card ${
                              plan.is_active ? "" : "inactive"
                            }`}
                            key={plan.plan_id}
                          >
                            <div className="retailer-plan-card-header">
                              <div>
                                <span className="retailer-plan-badge">
                                  {plan.name}
                                </span>

                                <h4>{plan.name}</h4>

                                <span className="retailer-plan-id">
                                  Retailer subscription
                                </span>
                              </div>

                              <label className="retailer-plan-active">
                                <input
                                  type="checkbox"
                                  checked={plan.is_active}
                                  onChange={(event) =>
                                    updateRetailerPlan(
                                      plan.plan_id,
                                      (current) => ({
                                        ...current,
                                        is_active:
                                          event.target.checked,
                                      })
                                    )
                                  }
                                />

                                <span>Active</span>
                              </label>
                            </div>

                            <div className="retailer-plan-section-block">
                              <div className="retailer-plan-section-title">
                                <span>Pricing</span>
                                <small>
                                  Subscription pricing
                                </small>
                              </div>

                              <div className="retailer-plan-pricing-grid">
                                <label>
                                  <span>Monthly</span>

                                  <div className="retailer-plan-price-input">
                                    <span>₹</span>

                                    <input
                                      type="number"
                                      min="0"
                                      step="0.01"
                                      value={plan.monthly_price}
                                      onChange={(event) =>
                                        updateRetailerPlan(
                                          plan.plan_id,
                                          (current) => ({
                                            ...current,
                                            monthly_price:
                                              event.target.value,
                                          })
                                        )
                                      }
                                    />
                                  </div>
                                </label>

                                <label>
                                  <span>Yearly</span>

                                  <div className="retailer-plan-price-input">
                                    <span>₹</span>

                                    <input
                                      type="number"
                                      min="0"
                                      step="0.01"
                                      value={plan.yearly_price}
                                      onChange={(event) =>
                                        updateRetailerPlan(
                                          plan.plan_id,
                                          (current) => ({
                                            ...current,
                                            yearly_price:
                                              event.target.value,
                                          })
                                        )
                                      }
                                    />
                                  </div>
                                </label>
                              </div>

                              <label className="retailer-plan-trial">
                                <span>Free trial</span>

                                <div className="retailer-plan-small-input">
                                  <input
                                    type="number"
                                    min="0"
                                    step="1"
                                    value={plan.trial_days}
                                    onChange={(event) =>
                                      updateRetailerPlan(
                                        plan.plan_id,
                                        (current) => ({
                                          ...current,
                                          trial_days: Number(
                                            event.target.value
                                          ),
                                        })
                                      )
                                    }
                                  />

                                  <span>days</span>
                                </div>
                              </label>
                            </div>

                            <div className="retailer-plan-section-block">
                              <div className="retailer-plan-section-title">
                                <span>Plan Limits</span>
                                <small>
                                  Set a limit or allow unlimited
                                </small>
                              </div>

                              <div className="retailer-plan-limit-table">
                                {(
                                  [
                                    ["invoices", "Invoices"],
                                    ["employees", "Employees"],
                                    ["products", "Products"],
                                  ] as const
                                ).map(([limitName, label]) => {
                                  const limit =
                                    plan.limits[limitName] ?? {
                                      unlimited: true,
                                      limit: null,
                                    };

                                  return (
                                    <div
                                      className="retailer-plan-limit-row"
                                      key={limitName}
                                    >
                                      <div className="retailer-plan-limit-name">
                                        <span>{label}</span>
                                      </div>

                                      <div className="retailer-plan-limit-value">
                                        {limit.unlimited ? (
                                          <span className="retailer-plan-unlimited-value">
                                            Unlimited
                                          </span>
                                        ) : (
                                          <input
                                            type="number"
                                            min="0"
                                            step="1"
                                            value={
                                              limit.limit ?? ""
                                            }
                                            onChange={(event) =>
                                              updatePlanLimit(
                                                plan.plan_id,
                                                limitName,
                                                (current) => ({
                                                  ...current,
                                                  limit:
                                                    event.target
                                                      .value === ""
                                                      ? null
                                                      : Number(
                                                          event.target
                                                            .value
                                                        ),
                                                })
                                              )
                                            }
                                          />
                                        )}
                                      </div>

                                      <label className="retailer-plan-limit-toggle">
                                        <input
                                          type="checkbox"
                                          checked={limit.unlimited}
                                          onChange={(event) =>
                                            updatePlanLimit(
                                              plan.plan_id,
                                              limitName,
                                              (current) => ({
                                                unlimited:
                                                  event.target.checked,
                                                limit:
                                                  event.target.checked
                                                    ? null
                                                    : current.limit ??
                                                      0,
                                              })
                                            )
                                          }
                                        />

                                        <span>Unlimited</span>
                                      </label>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>

                            <div className="retailer-plan-section-block retailer-plan-features-block">
                              <div className="retailer-plan-section-title">
                                <span>Features</span>
                                <small>
                                  Select included features
                                </small>
                              </div>

                              <div className="retailer-plan-feature-grid">
                                {[
                                  ["billing", "Billing"],
                                  ["inventory", "Inventory"],
                                  ["analytics", "Analytics"],
                                  ["warranty", "Warranty"],
                                  ["reports", "Reports & Analytics"],
                                  [
                                    "customer_management",
                                    "Customer Management",
                                  ],
                                  [
                                    "purchase_management",
                                    "Purchase Management",
                                  ],
                                  [
                                    "returns",
                                    "Returns & Refunds",
                                  ],
                                ].map(([featureId, featureLabel]) => (
                                  <label
                                    className="retailer-plan-feature-option"
                                    key={featureId}
                                  >
                                    <input
                                      type="checkbox"
                                      checked={plan.features.includes(
                                        featureId
                                      )}
                                      onChange={(event) =>
                                        updateRetailerPlan(
                                          plan.plan_id,
                                          (current) => ({
                                            ...current,
                                            features:
                                              event.target.checked
                                                ? [
                                                    ...current.features,
                                                    featureId,
                                                  ]
                                                : current.features.filter(
                                                    (feature) =>
                                                      feature !==
                                                      featureId
                                                  ),
                                          })
                                        )
                                      }
                                    />

                                    <span>{featureLabel}</span>
                                  </label>
                                ))}
                              </div>
                            </div>

                            <div className="retailer-plan-card-footer">
                              <div>
                                <span className="retailer-plan-status-dot" />

                                <span>
                                  {plan.is_active
                                    ? "Available to retailers"
                                    : "Currently inactive"}
                                </span>
                              </div>

                              <button
                                type="button"
                                className="primary-button"
                                onClick={() =>
                                  void saveRetailerPlan(plan)
                                }
                                disabled={retailerPlanSaving === plan.plan_id}
                              >
                                <Save size={16} />

                                {retailerPlanSaving === plan.plan_id
                                  ? "Saving..."
                                  : "Save plan"}
                              </button>
                            </div>
                          </div>
                        ))}
                    </div>
                  )}
              </div>
            </>
          )}

          {activeSection === "users" && (
            <>
              <div className="settings-section-header">
                <h2>Users & Roles</h2>
                <p>
                  Control administrative access and role
                  permissions.
                </p>
              </div>

              <div className="settings-info-grid">
                <div>
                  <strong>Super Admin</strong>
                  <span>
                    Full access to DigiBills administration.
                  </span>
                </div>

                <div>
                  <strong>Retailer Owner</strong>
                  <span>
                    Access to retailer operations and billing.
                  </span>
                </div>

                <div>
                  <strong>Customer</strong>
                  <span>
                    Access to customer invoices and services.
                  </span>
                </div>
              </div>
            </>
          )}

          {activeSection === "notifications" && (
            <>
              <div className="settings-section-header">
                <h2>Notifications</h2>
                <p>
                  Configure important system and billing
                  notifications.
                </p>
              </div>

              <div className="settings-toggle-list">
                <label>
                  <span>
                    <strong>Payment notifications</strong>
                    <small>
                      Notify users when payments are completed.
                    </small>
                  </span>
                  <input type="checkbox" defaultChecked />
                </label>

                <label>
                  <span>
                    <strong>Invoice notifications</strong>
                    <small>
                      Notify customers when invoices are
                      generated.
                    </small>
                  </span>
                  <input type="checkbox" defaultChecked />
                </label>

                <label>
                  <span>
                    <strong>
                      Subscription notifications
                    </strong>
                    <small>
                      Notify users about renewal and expiry
                      events.
                    </small>
                  </span>
                  <input type="checkbox" defaultChecked />
                </label>
              </div>
            </>
          )}

          {activeSection === "security" && (
            <>
              <div className="settings-section-header">
                <h2>Security</h2>
                <p>
                  Manage application-level security controls.
                </p>
              </div>

              <div className="settings-info-grid">
                <div>
                  <strong>Authentication</strong>
                  <span>
                    DigiBills uses authenticated API access.
                  </span>
                </div>

                <div>
                  <strong>Role-based access</strong>
                  <span>
                    Access is restricted according to assigned
                    roles.
                  </span>
                </div>

                <div>
                  <strong>Audit logging</strong>
                  <span>
                    Administrative actions are recorded in
                    audit logs.
                  </span>
                </div>
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
