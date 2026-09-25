import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowRight,
  CalendarDays,
  Check,
  Cloud,
  CreditCard,
  Crown,
  FileText,
  ShieldCheck,
} from "lucide-react";

import { API_BASE_URL, apiFetch } from "../api";

type CustomerPlan = {
  id: string;
  plan_id: string;
  name: string;
  description: string | null;
  customer_type: string;
  billing_type: string;
  monthly_price: string;
  yearly_price: string;
  per_bill_price: string;
  trial_days: number;
  features: string | null;
  limits: string | null;
  is_active: boolean;
};

interface SubscriptionRazorpayPaymentResponse {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

type CustomerInvoice = {
  id: string;
  invoice_id: string;
  retailer_id: string | null;
  subscription_id: string | null;
  employee_id: string | null;
  customer_id: string;
  invoice_number: string | null;
  invoice_date: string;
  item_names: string[];
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

type RazorpayOrderResponse = {
  invoice_id: string;
  razorpay_order_id: string;
  amount: string;
  currency: string;
};

type Subscription = {
  id: string;
  subscription_id: string;
  plan_id: string;
  retailer_id: string | null;
  customer_id: string | null;
  status: string;
  started_at: string;
  current_period_start: string;
  current_period_end: string;
  trial_ends_at: string | null;
  auto_renew: boolean;
  cancelled_at: string | null;
  created_at: string;
  updated_at: string;
};

const RAZORPAY_SCRIPT_URL =
  "https://checkout.razorpay.com/v1/checkout.js";

const RAZORPAY_KEY_ID =
  import.meta.env.VITE_RAZORPAY_KEY_ID as string | undefined;

async function loadRazorpay(): Promise<boolean> {
  if (window.Razorpay) {
    return true;
  }

  const existingScript =
    document.querySelector<HTMLScriptElement>(
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
    script.onload = () => resolve(Boolean(window.Razorpay));
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

export default function CustomerSubscription() {
  const [plans, setPlans] = useState<CustomerPlan[]>([]);
  const [currentSubscription, setCurrentSubscription] =
    useState<Subscription | null>(null);

  const [loading, setLoading] = useState(true);
  const [creatingPlan, setCreatingPlan] = useState("");
  const [showManageSubscription, setShowManageSubscription] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      setLoading(true);
      setError("");

      try {
        const loadedPlans = await apiFetch<CustomerPlan[]>(
          "/subscriptions/plans?customer_type=customer"
        );

        if (!cancelled) {
          setPlans(loadedPlans.filter((plan) => plan.is_active));
        }

        try {
          const subscription = await apiFetch<Subscription>(
            "/subscriptions/me"
          );

          if (!cancelled) {
            setCurrentSubscription(subscription);
          }
        } catch {
          if (!cancelled) {
            setCurrentSubscription(null);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load subscription plans."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadData();

    return () => {
      cancelled = true;
    };
  }, []);

  function parseFeatures(features: string | null): string[] {
    if (!features) {
      return [];
    }

    try {
      const parsed = JSON.parse(features);

      if (Array.isArray(parsed)) {
        return parsed.map(String);
      }

      return [];
    } catch {
      return [];
    }
  }

  function formatDate(value: string | null) {
    if (!value) {
      return "—";
    }

    return new Date(value).toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "long",
      year: "numeric",
    });
  }

  function getPrice(plan: CustomerPlan) {
    if (plan.billing_type === "monthly") {
      return {
        amount: plan.monthly_price,
        suffix: "/ month",
      };
    }

    if (plan.billing_type === "yearly") {
      return {
        amount: plan.yearly_price,
        suffix: "/ year",
      };
    }

    return {
      amount: plan.per_bill_price,
      suffix: "/ bill",
    };
  }

  async function choosePlan(plan: CustomerPlan) {
    setCreatingPlan(plan.plan_id);
    setError("");
    setSuccess("");

    try {
      const subscription = await apiFetch<Subscription>(
        "/subscriptions",
        {
          method: "POST",
          body: JSON.stringify({
            plan_id: plan.plan_id,
          }),
        }
      );

      setCurrentSubscription(subscription);

      const invoices = await apiFetch<CustomerInvoice[]>(
        "/customer/invoices"
      );

      const subscriptionInvoice = invoices.find(
        (invoice) =>
          invoice.subscription_id === subscription.id &&
          ["unpaid", "partial"].includes(
            invoice.payment_status.toLowerCase()
          )
      );

      if (!subscriptionInvoice) {
        if (subscription.status === "trialing") {
          setSuccess(
            `${plan.name} subscription started with a ${plan.trial_days}-day free trial.`
          );
          return;
        }

        throw new Error(
          "Subscription invoice was not found."
        );
      }

      if (!RAZORPAY_KEY_ID) {
        throw new Error(
          "Razorpay is not configured in the customer app."
        );
      }

      const razorpayLoaded = await loadRazorpay();

      if (!razorpayLoaded || !window.Razorpay) {
        throw new Error(
          "Unable to load Razorpay Checkout."
        );
      }

      const RazorpayCheckout = window.Razorpay;

      const order = await apiFetch<RazorpayOrderResponse>(
        `/subscriptions/invoices/${encodeURIComponent(
          subscriptionInvoice.invoice_id
        )}/razorpay-order`,
        {
          method: "POST",
        }
      );

      await new Promise<void>((resolve, reject) => {
        const checkout = new RazorpayCheckout({
          key: RAZORPAY_KEY_ID,
          amount: Math.round(
            Number(order.amount) * 100
          ),
          currency: order.currency,
          name: "DigiBills",
          description: `${plan.name} subscription`,
          order_id: order.razorpay_order_id,

          handler: async (
            response: SubscriptionRazorpayPaymentResponse
          ) => {
            try {
              await apiFetch(
                `/subscriptions/invoices/${encodeURIComponent(
                  subscriptionInvoice.invoice_id
                )}/verify-razorpay-payment`,
                {
                  method: "POST",
                  body: JSON.stringify({
                    razorpay_order_id:
                      response.razorpay_order_id,
                    razorpay_payment_id:
                      response.razorpay_payment_id,
                    razorpay_signature:
                      response.razorpay_signature,
                  }),
                }
              );

              const refreshedSubscription =
                await apiFetch<Subscription>(
                  "/subscriptions/me"
                );

              setCurrentSubscription(
                refreshedSubscription
              );

              setSuccess(
                `${plan.name} subscription activated successfully.`
              );

              resolve();
            } catch (err) {
              reject(err);
            }
          },

          modal: {
            ondismiss: () => {
              reject(
                new Error(
                  "Payment was cancelled. Your subscription is still pending payment."
                )
              );
            },
          },

          theme: {
            color: "#2563eb",
          },
        });

        checkout.open();
      });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to complete subscription payment."
      );
    } finally {
      setCreatingPlan("");
    }
  }

  const currentPlan = useMemo(() => {
    if (!currentSubscription) {
      return null;
    }

    return (
      plans.find(
        (plan) =>
          plan.id === currentSubscription.plan_id ||
          plan.plan_id === currentSubscription.plan_id
      ) ?? null
    );
  }, [plans, currentSubscription]);

  const purchasePlan = useMemo(() => {
    if (plans.length === 0) {
      return null;
    }

    return (
      plans.find((plan) => plan.billing_type === "yearly") ??
      plans[0]
    );
  }, [plans]);

  const purchasePrice = purchasePlan
    ? getPrice(purchasePlan)
    : null;

  const purchaseFeatures = purchasePlan
    ? parseFeatures(purchasePlan.features)
    : [];

  const benefitFeatures =
    purchaseFeatures.length > 0
      ? purchaseFeatures.slice(0, 3)
      : [
          "Keep all your bills safe",
          "Track warranties easily",
          "Access anytime, anywhere",
        ];

  const benefitIcons = [FileText, ShieldCheck, Cloud];

  return (
    <section className="dashboard customer-dashboard-page customer-subscription-page">
      <div className="customer-subscription-final-heading">
        <div>
          <span className="page-eyebrow">SUBSCRIPTION</span>
          <h1>Subscription</h1>
          <p>
            {currentSubscription
              ? "Manage your DigiBills subscription."
              : "Get more with DigiBills."}
          </p>
        </div>
      </div>

      {loading && (
        <div className="settings-status">
          Loading subscription...
        </div>
      )}

      {error && (
        <div className="settings-status settings-status-error">
          {error}
        </div>
      )}

      {success && (
        <div className="settings-status">
          {success}
        </div>
      )}

      {!loading && !error && purchasePlan && !currentSubscription && (
        <>
          <div className="customer-subscription-purchase-card">
            <div className="customer-subscription-purchase-main">
              <div className="customer-subscription-purchase-copy">
                <div className="customer-subscription-crown">
                  <Crown size={30} strokeWidth={2.2} />
                </div>

                <div>
                  <span className="customer-subscription-mini-label">
                    DIGIBILLS
                  </span>

                  <h2>
                    {purchasePlan.name || "DigiBills Pro"}
                  </h2>

                  <p>
                    Store, manage and access all your bills,
                    warranties and more — in one place.
                  </p>
                </div>
              </div>

              <div className="customer-subscription-purchase-price">
                <strong>₹{purchasePrice?.amount}</strong>
                <span>{purchasePrice?.suffix}</span>
              </div>

              <button
                type="button"
                className="customer-subscription-buy-button"
                disabled={creatingPlan !== ""}
                onClick={() => void choosePlan(purchasePlan)}
              >
                {creatingPlan === purchasePlan.plan_id
                  ? "Subscribing..."
                  : "Subscribe Now"}
                <ArrowRight size={21} />
              </button>
            </div>

            <div className="customer-subscription-benefits">
              {benefitFeatures.map((feature, index) => {
                const Icon = benefitIcons[index];

                return (
                  <div
                    className="customer-subscription-benefit"
                    key={`${purchasePlan.plan_id}-benefit-${index}`}
                  >
                    <span>
                      <Icon size={19} />
                    </span>

                    <strong>{feature}</strong>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="customer-subscription-your-heading">
            <h2>Your Subscription</h2>
          </div>

          <div className="customer-subscription-empty-card">
            <div className="customer-subscription-empty-icon">
              <Crown size={30} />
            </div>

            <h3>No Active Subscription</h3>

            <p>
              Subscribe to DigiBills Pro to unlock all features.
            </p>

            <button
              type="button"
              className="customer-subscription-empty-button"
              disabled={creatingPlan !== ""}
              onClick={() => void choosePlan(purchasePlan)}
            >
              {creatingPlan === purchasePlan.plan_id
                ? "Subscribing..."
                : "Subscribe Now"}
              <ArrowRight size={20} />
            </button>
          </div>

          <details className="customer-subscription-benefits">
            <summary className="customer-subscription-info-row">
              <div className="customer-subscription-info-icon">
                <Check size={20} />
              </div>

              <div>
                <strong>Subscription Benefits</strong>
                <span>
                  See what you get with your DigiBills subscription.
                </span>
              </div>

              <ArrowRight size={20} />
            </summary>

            <div className="customer-subscription-benefits-list">
              <div>
                <Check size={17} />
                <div>
                  <strong>Unlimited Bill Access</strong>
                  <span>Access your digital bills anytime.</span>
                </div>
              </div>

              <div>
                <Check size={17} />
                <div>
                  <strong>Digital Warranty Records</strong>
                  <span>Keep your E-Warranty records safely in DigiBills.</span>
                </div>
              </div>

              <div>
                <Check size={17} />
                <div>
                  <strong>Purchase History</strong>
                  <span>View your complete purchase and billing records.</span>
                </div>
              </div>

              <div>
                <Check size={17} />
                <div>
                  <strong>Payment Records</strong>
                  <span>Keep track of payments associated with your bills.</span>
                </div>
              </div>

              <div>
                <Check size={17} />
                <div>
                  <strong>Bill Transfer</strong>
                  <span>Transfer eligible bills to another customer when required.</span>
                </div>
              </div>

              <div>
                <Check size={17} />
                <div>
                  <strong>Priority Support</strong>
                  <span>Get support for your DigiBills account and records.</span>
                </div>
              </div>
            </div>
          </details>
        </>
      )}

      {!loading && !error && currentSubscription && (
        <>
          <div className="customer-subscription-active-card">
            <div className="customer-subscription-active-top">
              <div className="customer-subscription-active-brand">
                <div className="customer-subscription-active-crown">
                  <Crown size={30} />
                </div>

                <div>
                  <h2>
                    DigiBills Pro
                  </h2>

                  <p>Your Active Subscription</p>
                </div>
              </div>

              <span className="customer-subscription-active-status">
                <span />
                {currentSubscription.status === "trialing" ? "Trial Active" : currentSubscription.status || "Active"}
              </span>
            </div>

            <div className="customer-subscription-active-details">
              <div className="customer-subscription-active-plan">
                <span>Plan</span>

                <strong>
                  DigiBills Pro
                </strong>

                <p>
                  {currentPlan?.description ||
                    "All the features you need for your business."}
                </p>
              </div>

              <div className="customer-subscription-active-divider" />

              <div className="customer-subscription-active-meta">
                <div>
                  <CalendarDays size={27} />

                  <div>
                    <span>Next Billing Date</span>
                    <strong>
                      {formatDate(
                        currentSubscription.current_period_end
                      )}
                    </strong>
                  </div>
                </div>

                <div>
                  <CreditCard size={27} />

                  <div>
                    <span>Billing Cycle</span>
                    <strong>
                      {currentPlan?.billing_type === "monthly"
                        ? "Monthly"
                        : currentPlan?.billing_type === "yearly"
                          ? "Yearly"
                          : "Per Bill"}
                    </strong>
                  </div>
                </div>
              </div>
            </div>

            <button
              type="button"
              className="customer-subscription-manage-button"
              onClick={() => setShowManageSubscription(true)}
            >
              <span>Manage Subscription</span>
              <ArrowRight size={23} />
            </button>
          </div>

          <details className="customer-subscription-benefits">
            <summary className="customer-subscription-info-row">
              <div className="customer-subscription-info-icon">
                <Check size={20} />
              </div>

              <div>
                <strong>Subscription Benefits</strong>
                <span>
                  Your DigiBills subscription includes these benefits.
                </span>
              </div>

              <ArrowRight size={20} />
            </summary>

            <div className="customer-subscription-benefits-list">
              <div>
                <Check size={17} />
                <div>
                  <strong>Unlimited Bill Access</strong>
                  <span>Access your digital bills anytime.</span>
                </div>
              </div>

              <div>
                <Check size={17} />
                <div>
                  <strong>Digital Warranty Records</strong>
                  <span>Keep your E-Warranty records safely in DigiBills.</span>
                </div>
              </div>

              <div>
                <Check size={17} />
                <div>
                  <strong>Purchase History</strong>
                  <span>View your complete purchase and billing records.</span>
                </div>
              </div>

              <div>
                <Check size={17} />
                <div>
                  <strong>Payment Records</strong>
                  <span>Keep track of payments associated with your bills.</span>
                </div>
              </div>

              <div>
                <Check size={17} />
                <div>
                  <strong>Bill Transfer</strong>
                  <span>Transfer eligible bills to another customer when required.</span>
                </div>
              </div>

              <div>
                <Check size={17} />
                <div>
                  <strong>Priority Support</strong>
                  <span>Get support for your DigiBills account and records.</span>
                </div>
              </div>
            </div>
          </details>
        </>
      )}

      {!loading && !error && plans.length === 0 && (
        <div className="panel">
          <p>No subscription plans are currently available.</p>
        </div>
      )}

      {showManageSubscription && currentSubscription && (
        <div
          className="customer-subscription-manage-overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="manage-subscription-title"
          onClick={(event) => {
            if (event.target === event.currentTarget) {
              setShowManageSubscription(false);
            }
          }}
        >
          <div className="customer-subscription-manage-panel">
            <div className="customer-subscription-manage-header">
              <div>
                <span>Subscription Management</span>
                <h2 id="manage-subscription-title">DigiBills Pro</h2>
              </div>

              <button
                type="button"
                className="customer-subscription-manage-close"
                aria-label="Close subscription management"
                onClick={() => setShowManageSubscription(false)}
              >
                ×
              </button>
            </div>

            <div className="customer-subscription-manage-status">
              <span />
              {currentSubscription.status === "trialing"
                ? "Trial Active"
                : currentSubscription.status || "Active"}
            </div>

            <div className="customer-subscription-manage-grid">
              <div>
                <span>Current Plan</span>
                <strong>DigiBills Pro</strong>
              </div>

              <div>
                <span>Billing Cycle</span>
                <strong>
                  {currentPlan?.billing_type === "monthly"
                    ? "Monthly"
                    : currentPlan?.billing_type === "yearly"
                      ? "Yearly"
                      : "Per Bill"}
                </strong>
              </div>

              <div>
                <span>Subscription Started</span>
                <strong>{formatDate(currentSubscription.started_at)}</strong>
              </div>

              <div>
                <span>Next Billing Date</span>
                <strong>
                  {formatDate(currentSubscription.current_period_end)}
                </strong>
              </div>

              <div>
                <span>Auto Renewal</span>
                <strong>
                  {currentSubscription.auto_renew ? "Enabled" : "Disabled"}
                </strong>
              </div>

              <div>
                <span>Subscription ID</span>
                <strong>{currentSubscription.subscription_id}</strong>
              </div>
            </div>

            <div className="customer-subscription-manage-benefits">
              <div className="customer-subscription-manage-benefits-title">
                <Check size={19} />
                <strong>Included Benefits</strong>
              </div>

              <div className="customer-subscription-manage-benefits-list">
                <div>
                  <Check size={16} />
                  <span>Unlimited Bill Access</span>
                </div>

                <div>
                  <Check size={16} />
                  <span>Digital Warranty Records</span>
                </div>

                <div>
                  <Check size={16} />
                  <span>Purchase History</span>
                </div>

                <div>
                  <Check size={16} />
                  <span>Payment Records</span>
                </div>

                <div>
                  <Check size={16} />
                  <span>Bill Transfer</span>
                </div>

                <div>
                  <Check size={16} />
                  <span>Priority Support</span>
                </div>
              </div>
            </div>

            <div className="customer-subscription-manage-note">
              <ShieldCheck size={18} />
              <span>
                Your subscription is active. Subscription cancellation is not
                available while the subscription is active.
              </span>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
