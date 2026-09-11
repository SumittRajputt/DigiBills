import { FormEvent, useEffect, useState } from "react";
import {
  ArrowLeft,
  Mail,
  Phone,
  Save,
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

export default function CustomerEditProfile() {
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [email, setEmail] = useState("");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadProfile() {
      try {
        setLoading(true);
        setError("");

        const result =
          await apiFetch<CustomerProfileData>("/customers/me");

        setFullName(result.full_name || "");
        setPhoneNumber(result.phone_number || "");
        setEmail(result.email || "");
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

    loadProfile();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!fullName.trim()) {
      setError("Full name is required.");
      return;
    }

    if (!phoneNumber.trim()) {
      setError("Phone number is required.");
      return;
    }

    try {
      setSaving(true);
      setError("");

      await apiFetch<CustomerProfileData>("/customers/me", {
        method: "PUT",
        body: JSON.stringify({
          full_name: fullName.trim(),
          phone_number: phoneNumber.trim(),
          email: email.trim() || null,
        }),
      });

      navigate("/customer/profile");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to update your profile."
      );
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <section className="dashboard customer-edit-profile-screen">
        <div className="customer-mobile-page-header">
          <button
            type="button"
            className="customer-back-button"
            onClick={() => navigate(-1)}
            aria-label="Go back"
          >
            <ArrowLeft size={20} />
          </button>

          <h1>Edit Profile</h1>

          <span className="customer-header-spacer" />
        </div>

        <div className="customer-profile-loading">
          Loading your profile...
        </div>
      </section>
    );
  }

  return (
    <section className="dashboard customer-edit-profile-screen">
      <div className="customer-mobile-page-header">
        <button
          type="button"
          className="customer-back-button"
          onClick={() => navigate("/customer/profile")}
          aria-label="Go back"
        >
          <ArrowLeft size={20} />
        </button>

        <h1>Edit Profile</h1>

        <span className="customer-header-spacer" />
      </div>

      <form
        className="customer-edit-profile-card"
        onSubmit={handleSubmit}
      >
        <div className="customer-edit-profile-intro">
          <div className="customer-edit-profile-icon">
            <UserRound size={22} />
          </div>

          <div>
            <h2>Personal Information</h2>
            <p>Keep your profile information up to date.</p>
          </div>
        </div>

        {error && (
          <div className="customer-edit-profile-error" role="alert">
            {error}
          </div>
        )}

        <div className="customer-edit-profile-fields">
          <label className="customer-edit-profile-field">
            <span>Full Name</span>

            <div className="customer-edit-profile-input-wrap">
              <UserRound size={17} />
              <input
                type="text"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Enter your full name"
                autoComplete="name"
              />
            </div>
          </label>

          <label className="customer-edit-profile-field">
            <span>Phone Number</span>

            <div className="customer-edit-profile-input-wrap">
              <Phone size={17} />
              <input
                type="tel"
                value={phoneNumber}
                onChange={(event) =>
                  setPhoneNumber(event.target.value)
                }
                placeholder="Enter your phone number"
                autoComplete="tel"
              />
            </div>
          </label>

          <label className="customer-edit-profile-field">
            <span>Email Address</span>

            <div className="customer-edit-profile-input-wrap">
              <Mail size={17} />
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="Enter your email address"
                autoComplete="email"
              />
            </div>
          </label>
        </div>

        <div className="customer-edit-profile-actions">
          <button
            type="button"
            className="customer-edit-profile-cancel"
            onClick={() => navigate("/customer/profile")}
            disabled={saving}
          >
            Cancel
          </button>

          <button
            type="submit"
            className="customer-primary-button customer-edit-profile-save"
            disabled={saving}
          >
            <Save size={17} />
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </form>
    </section>
  );
}
