import { useEffect, useState } from "react";
import { Check, CreditCard } from "lucide-react";

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
  const [cancelling, setCancelling] = useState(false);
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
          // 404 simply means the customer has no active subscription.
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

  function formatPrice(plan: CustomerPlan) {
    if (plan.billing_type === "monthly") {
      return {
        amount: plan.monthly_price,
        suffix: "/month",
      };
    }

    if (plan.billing_type === "yearly") {
      return {
        amount: plan.yearly_price,
        suffix: "/year",
      };
    }

    return {
      amount: plan.per_bill_price,
      suffix: "/bill",
    };
  }

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
      month: "short",
      year: "numeric",
    });
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

      setSuccess(
        `${plan.name} subscription started successfully.`
      );
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
  const currentPlan = currentSubscription
    ? plans.find(
        (plan) => plan.id === currentSubscription.plan_id
      )
    : null;

  return (
    <section className="dashboard customer-dashboard-page customer-subscription-page">
      <div className="page-heading customer-subscription-heading">
        <div>
          <span className="page-eyebrow">SUBSCRIPTION</span>
          <h1>Choose Your Plan</h1>
          <p>
            Select the DigiBills customer plan that works best
            for you.
          </p>
        </div>
      </div>

      {loading && (
        <div className="settings-status">
          Loading subscription plans...
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

      {!loading && currentSubscription && (
        <div className="panel customer-current-subscription">
          <div className="customer-current-subscription-header">
            <div>
              <span className="page-eyebrow">CURRENT PLAN</span>
              <h2>
                {currentPlan?.name ?? currentSubscription.plan_id}
              </h2>
            </div>

            <span className="customer-subscription-status">
              {currentSubscription.status}
            </span>
          </div>

          {currentPlan && (
            <p>
              {currentPlan.description}
            </p>
          )}

          <div className="customer-current-subscription-details">
            <div>
              <strong>Started</strong>
              <span>
                {formatDate(currentSubscription.started_at)}
              </span>
            </div>

            <div>
              <strong>Period ends</strong>
              <span>
                {formatDate(
                  currentSubscription.current_period_end
                )}
              </span>
            </div>

            {currentSubscription.trial_ends_at && (
              <div>
                <strong>Trial ends</strong>
                <span>
                  {formatDate(
                    currentSubscription.trial_ends_at
                  )}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {!loading && !error && plans.length === 0 && (
        <div className="panel">
          <p>No subscription plans are currently available.</p>
        </div>
      )}

      {!loading && plans.length > 0 && !currentSubscription && (
        <div className="customer-subscription-grid">
          {plans.map((plan) => {
            const price = formatPrice(plan);
            const features = parseFeatures(plan.features);
            const isCreating = creatingPlan === plan.plan_id;

            return (
              <div
                className="customer-subscription-card"
                key={plan.plan_id}
              >
                <div className="customer-subscription-card-header">
                  <div className="customer-subscription-icon">
                    <CreditCard size={20} />
                  </div>

                  <div>
                    <span className="customer-subscription-badge">
                      {plan.billing_type.replace("_", " ")}
                    </span>

                    <h2>{plan.name}</h2>
                  </div>
                </div>

                <p className="customer-subscription-description">
                  {plan.description}
                </p>

                <div className="customer-subscription-price">
                  <span>₹{price.amount}</span>
                  <small>{price.suffix}</small>
                </div>

                {plan.trial_days > 0 && (
                  <div className="customer-subscription-trial">
                    {plan.trial_days}-day free trial
                  </div>
                )}

                {features.length > 0 && (
                  <div className="customer-subscription-features">
                    {features.map((feature, index) => (
                      <div key={`${plan.plan_id}-${index}`}>
                        <Check size={16} />
                        <span>{feature}</span>
                      </div>
                    ))}
                  </div>
                )}

                <button
                  type="button"
                  className="primary-button customer-subscription-button"
                  disabled={creatingPlan !== ""}
                  onClick={() => void choosePlan(plan)}
                >
                  {isCreating ? "Starting..." : "Choose Plan"}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
