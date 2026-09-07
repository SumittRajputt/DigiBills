import { useEffect, useState } from "react";
import { Mail, Phone, ShieldCheck, UserRound } from "lucide-react";
import { apiFetch } from "../api";

type CustomerProfileData = {
  customer_id: string;
  full_name: string;
  phone_number: string;
  email: string | null;
  status: string;
};

export default function CustomerProfile() {
  const [customer, setCustomer] =
    useState<CustomerProfileData | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadProfile() {
    try {
      setLoading(true);
      setError("");

      const result =
        await apiFetch<CustomerProfileData>("/customers/me");

      setCustomer(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load your profile."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProfile();
  }, []);

  if (loading) {
    return (
      <section className="dashboard customer-profile-page">
        <div className="page-heading">
          <span className="page-eyebrow">CUSTOMER ACCOUNT</span>
          <h1>My Profile</h1>
          <p>Loading your profile...</p>
        </div>

        <div className="panel">
          <div style={{ padding: "28px 20px" }}>
            Loading profile...
          </div>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="dashboard customer-profile-page">
        <div className="page-heading">
          <span className="page-eyebrow">CUSTOMER ACCOUNT</span>
          <h1>My Profile</h1>
          <p>Unable to load your customer profile.</p>
        </div>

        <div className="panel">
          <div className="customer-profile-error">
            {error}
          </div>
        </div>
      </section>
    );
  }

  if (!customer) {
    return (
      <section className="dashboard customer-profile-page">
        <div className="page-heading">
          <span className="page-eyebrow">CUSTOMER ACCOUNT</span>
          <h1>My Profile</h1>
          <p>Customer profile not found.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="dashboard customer-profile-page">
      <div className="page-heading">
        <span className="page-eyebrow">CUSTOMER ACCOUNT</span>
        <h1>My Profile</h1>
        <p>View your DigiBills customer information.</p>
      </div>

      <div className="customer-profile-layout">
        <div className="panel customer-profile-card">
          <div className="customer-profile-header">
            <div className="customer-profile-avatar">
              <UserRound size={28} />
            </div>

            <div>
              <h2>{customer.full_name}</h2>
              <span>Customer ID: {customer.customer_id}</span>
            </div>

            <span
              className={`customer-profile-status ${customer.status}`}
            >
              <ShieldCheck size={14} />
              {customer.status}
            </span>
          </div>

          <div className="customer-profile-fields">
            <div className="customer-profile-field">
              <div className="customer-profile-field-icon">
                <UserRound size={17} />
              </div>

              <div>
                <span>Full Name</span>
                <strong>{customer.full_name}</strong>
              </div>
            </div>

            <div className="customer-profile-field">
              <div className="customer-profile-field-icon">
                <Phone size={17} />
              </div>

              <div>
                <span>Phone Number</span>
                <strong>{customer.phone_number}</strong>
              </div>
            </div>

            <div className="customer-profile-field">
              <div className="customer-profile-field-icon">
                <Mail size={17} />
              </div>

              <div>
                <span>Email Address</span>
                <strong>
                  {customer.email || "Not provided"}
                </strong>
              </div>
            </div>

            <div className="customer-profile-field">
              <div className="customer-profile-field-icon">
                <ShieldCheck size={17} />
              </div>

              <div>
                <span>Account Status</span>
                <strong>
                  {customer.status}
                </strong>
              </div>
            </div>
          </div>
        </div>

        <div className="panel customer-profile-info">
          <div className="panel-header">
            <div>
              <h3>Account Information</h3>
              <span>Your registered DigiBills details</span>
            </div>
          </div>

          <div className="customer-profile-id-box">
            <span>Customer ID</span>
            <strong>{customer.customer_id}</strong>
          </div>

          <p>
            This profile is linked to your authenticated
            DigiBills customer account.
          </p>
        </div>
      </div>
    </section>
  );
}
