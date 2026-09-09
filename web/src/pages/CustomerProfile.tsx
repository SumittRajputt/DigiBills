import { useEffect, useState } from "react";
import {
  ArrowLeft,
  Camera,
  Mail,
  Pencil,
  Phone,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api";

type CustomerProfileData = {
  customer_id: string;
  full_name: string;
  phone_number: string;
  email: string | null;
  status: string;
};

export default function CustomerProfile() {
  const navigate = useNavigate();

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

  function getInitials(name: string) {
    const parts = name
      .trim()
      .split(/\s+/)
      .filter(Boolean);

    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }

    return name.slice(0, 2).toUpperCase();
  }

  if (loading) {
    return (
      <section className="dashboard customer-profile-screen">
        <div className="customer-mobile-page-header">
          <button
            type="button"
            className="customer-back-button"
            onClick={() => navigate(-1)}
            aria-label="Go back"
          >
            <ArrowLeft size={20} />
          </button>

          <h1>My Profile</h1>

          <span className="customer-header-spacer" />
        </div>

        <div className="customer-profile-loading">
          Loading your profile...
        </div>
      </section>
    );
  }

  if (error || !customer) {
    return (
      <section className="dashboard customer-profile-screen">
        <div className="customer-mobile-page-header">
          <button
            type="button"
            className="customer-back-button"
            onClick={() => navigate(-1)}
            aria-label="Go back"
          >
            <ArrowLeft size={20} />
          </button>

          <h1>My Profile</h1>

          <span className="customer-header-spacer" />
        </div>

        <div className="customer-profile-error-card">
          <ShieldCheck size={24} />
          <strong>Unable to load profile</strong>
          <span>
            {error || "Customer profile was not found."}
          </span>

          <button
            type="button"
            className="customer-primary-button"
            onClick={loadProfile}
          >
            Try Again
          </button>
        </div>
      </section>
    );
  }

  const initials = getInitials(customer.full_name);

  return (
    <section className="dashboard customer-profile-screen">
      <div className="customer-mobile-page-header">
        <button
          type="button"
          className="customer-back-button"
          onClick={() => navigate(-1)}
          aria-label="Go back"
        >
          <ArrowLeft size={20} />
        </button>

        <h1>My Profile</h1>

        <span className="customer-header-spacer" />
      </div>

      <div className="customer-profile-hero">
        <div className="customer-profile-photo-wrap">
          <div className="customer-profile-photo">
            {initials}
          </div>

          <button
            type="button"
            className="customer-profile-camera"
            aria-label="Change profile photo"
            title="Profile photo"
          >
            <Camera size={14} />
          </button>
        </div>

        <h2>{customer.full_name}</h2>

        <span className="customer-profile-phone">
          {customer.phone_number}
        </span>

        <span className="customer-profile-email">
          {customer.email || "Email not provided"}
        </span>
      </div>

      <div className="customer-profile-details-card">
        <div className="customer-profile-detail-row">
          <div className="customer-profile-detail-icon">
            <UserRound size={17} />
          </div>

          <div className="customer-profile-detail-content">
            <span>Full Name</span>
            <strong>{customer.full_name}</strong>
          </div>

          <button
            type="button"
            className="customer-profile-edit-button"
            aria-label="Edit full name"
            title="Edit full name"
          >
            <Pencil size={16} />
          </button>
        </div>

        <div className="customer-profile-detail-row">
          <div className="customer-profile-detail-icon">
            <Phone size={17} />
          </div>

          <div className="customer-profile-detail-content">
            <span>Phone Number</span>
            <strong>{customer.phone_number}</strong>
          </div>

          <button
            type="button"
            className="customer-profile-edit-button"
            aria-label="Edit phone number"
            title="Edit phone number"
          >
            <Pencil size={16} />
          </button>
        </div>

        <div className="customer-profile-detail-row">
          <div className="customer-profile-detail-icon">
            <Mail size={17} />
          </div>

          <div className="customer-profile-detail-content">
            <span>Email</span>
            <strong>
              {customer.email || "Not provided"}
            </strong>
          </div>

          <button
            type="button"
            className="customer-profile-edit-button"
            aria-label="Edit email"
            title="Edit email"
          >
            <Pencil size={16} />
          </button>
        </div>

        <div className="customer-profile-detail-row customer-profile-status-row">
          <div className="customer-profile-detail-icon customer-profile-status-icon">
            <ShieldCheck size={17} />
          </div>

          <div className="customer-profile-detail-content">
            <span>Account Status</span>
            <strong className="customer-profile-active">
              {customer.status}
            </strong>
          </div>
        </div>
      </div>

      <div className="customer-profile-account-id">
        Customer ID: <strong>{customer.customer_id}</strong>
      </div>
    </section>
  );
}
