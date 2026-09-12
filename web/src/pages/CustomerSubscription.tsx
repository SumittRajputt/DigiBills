import { useEffect, useMemo, useState } from "react";
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

import { apiFetch } from "../api";

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

export default function CustomerSubscription() {
  const [plans, setPlans] = useState<CustomerPlan[]>([]);
  const [currentSubscription, setCurrentSubscription] =
    useState<Subscription | null>(null);

  const [loading, setLoading] = useState(true);
  const [creatingPlan, setCreatingPlan] = useState("");
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
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            plan_id: plan.plan_id,
          }),
        }
      );

      setCurrentSubscription(subscription);

      setSuccess(`${plan.name} subscription started successfully.`);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to create subscription."
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

          <div className="customer-subscription-info-row">
            <div className="customer-subscription-info-icon">
              <Check size={20} />
            </div>

            <div>
              <strong>Subscription Benefits</strong>
              <span>
                Securely keep your bills and warranty records together.
              </span>
            </div>

            <ArrowRight size={20} />
          </div>
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
            >
              <span>Manage Subscription</span>
              <ArrowRight size={23} />
            </button>
          </div>

          <div className="customer-subscription-info-row">
            <div className="customer-subscription-info-icon">
              <Check size={20} />
            </div>

            <div>
              <strong>Subscription Benefits</strong>
              <span>
                Your DigiBills subscription is currently active.
              </span>
            </div>

            <ArrowRight size={20} />
          </div>
        </>
      )}

      {!loading && !error && plans.length === 0 && (
        <div className="panel">
          <p>No subscription plans are currently available.</p>
        </div>
      )}
    </section>
  );
}
