import { Save, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { apiFetch } from "../api";

type Retailer = {
  id: string;
  retailer_id: string;
  owner_user_id: string;
  business_name: string;
  business_type: string | null;
  phone_number: string;
  email: string | null;
  address: string | null;
  status: string;
  approved_at: string | null;
  approved_by: string | null;
  rejection_reason: string | null;
  created_at: string;
  updated_at: string;
};

type AccountUser = {
  id: string;
  phone_number: string;
  email: string | null;
  status: string;
};


export default function RetailerSettings() {
  const [retailer, setRetailer] =
    useState<Retailer | null>(null);

  const [accountUser, setAccountUser] =
    useState<AccountUser | null>(null);

  const [businessName, setBusinessName] = useState("");
  const [businessType, setBusinessType] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");

  const [activeTab, setActiveTab] = useState<
    "business" | "account"
  >("business");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordChanging, setPasswordChanging] = useState(false);

  async function loadSettings() {
    try {
      setLoading(true);
      setError("");
      setSuccess("");

      const [result, currentUser] = await Promise.all([
        apiFetch<Retailer>("/retailers/me"),
        apiFetch<AccountUser>("/auth/me"),
      ]);

      setRetailer(result);
      setAccountUser(currentUser);
      setBusinessName(result.business_name || "");
      setBusinessType(result.business_type || "");
      setPhoneNumber(result.phone_number || "");
      setEmail(result.email || "");
      setAddress(result.address || "");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load retailer settings."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSettings();
  }, []);

  async function changePassword() {
    if (!currentPassword) {
      setError("Current password is required.");
      return;
    }

    if (!newPassword) {
      setError("New password is required.");
      return;
    }

    if (newPassword.length < 6) {
      setError("New password must be at least 6 characters.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match.");
      return;
    }

    try {
      setPasswordChanging(true);
      setError("");
      setSuccess("");

      await apiFetch<{ message: string }>(
        "/auth/change-password",
        {
          method: "PUT",
          body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword,
          }),
        }
      );

      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");

      setSuccess("Password changed successfully.");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to change password."
      );
    } finally {
      setPasswordChanging(false);
    }
  }

  async function saveSettings() {
    if (!businessName.trim()) {
      setError("Business name is required.");
      return;
    }

    if (!phoneNumber.trim()) {
      setError("Phone number is required.");
      return;
    }

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      const updated =
        await apiFetch<Retailer>("/retailers/me", {
          method: "PUT",
          body: JSON.stringify({
            business_name: businessName.trim(),
            business_type: businessType.trim() || null,
            phone_number: phoneNumber.trim(),
            email: email.trim() || null,
            address: address.trim() || null,
          }),
        });

      setRetailer(updated);
      setBusinessName(updated.business_name || "");
      setBusinessType(updated.business_type || "");
      setPhoneNumber(updated.phone_number || "");
      setEmail(updated.email || "");
      setAddress(updated.address || "");

      setSuccess(
        "Business settings saved successfully."
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to save retailer settings."
      );
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="settings-page">
        <div className="settings-card">
          <p>Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="settings-page">
      <div className="settings-page-header">
        <div>
          <h1>Business Settings</h1>
          <p>
            Manage your retailer business profile and
            account information.
          </p>
        </div>

        <div className="settings-header-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={loadSettings}
            disabled={saving}
          >
            <RefreshCw size={15} />
            Refresh
          </button>

          {activeTab === "business" && (
            <button
              type="button"
              className="primary-button"
              onClick={saveSettings}
              disabled={saving}
            >
              <Save size={15} />
              {saving ? "Saving..." : "Save Changes"}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="settings-status settings-status-error">
          {error}
        </div>
      )}

      {success && (
        <div className="settings-status settings-status-success">
          {success}
        </div>
      )}

      <div className="settings-layout">
        <aside className="settings-menu">
          <button
            type="button"
            className={`settings-menu-item ${
              activeTab === "business" ? "active" : ""
            }`}
            onClick={() => setActiveTab("business")}
          >
            Business Profile
          </button>

          <button
            type="button"
            className={`settings-menu-item ${
              activeTab === "account" ? "active" : ""
            }`}
            onClick={() => setActiveTab("account")}
          >
            Account Information
          </button>
        </aside>

        {activeTab === "business" ? (
          <section className="settings-card">
            <div className="settings-section-header">
              <div>
                <h2>Business Profile</h2>
                <p>
                  Update the information associated with
                  your retailer account.
                </p>
              </div>
            </div>

            <div className="settings-form-grid">
              <label>
                Business Name
                <input
                  type="text"
                  value={businessName}
                  onChange={(event) =>
                    setBusinessName(event.target.value)
                  }
                  placeholder="Business name"
                />
              </label>

              <label>
                Business Type
                <input
                  type="text"
                  value={businessType}
                  onChange={(event) =>
                    setBusinessType(event.target.value)
                  }
                  placeholder="e.g. Mobile Retailer"
                />
              </label>

              <label>
                Phone Number
                <input
                  type="tel"
                  value={phoneNumber}
                  onChange={(event) =>
                    setPhoneNumber(event.target.value)
                  }
                  placeholder="Phone number"
                />
              </label>

              <label>
                Email
                <input
                  type="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  placeholder="business@example.com"
                />
              </label>

              <label className="settings-full-width">
                Business Address
                <textarea
                  rows={4}
                  value={address}
                  onChange={(event) =>
                    setAddress(event.target.value)
                  }
                  placeholder="Business address"
                />
              </label>
            </div>

            {retailer && (
              <div className="settings-info-grid">
                <div>
                  <span>Retailer ID</span>
                  <strong>{retailer.retailer_id}</strong>
                </div>

                <div>
                  <span>Account Status</span>
                  <strong>{retailer.status}</strong>
                </div>

                <div>
                  <span>Account Created</span>
                  <strong>
                    {new Date(
                      retailer.created_at
                    ).toLocaleDateString("en-IN")}
                  </strong>
                </div>

                <div>
                  <span>Last Updated</span>
                  <strong>
                    {new Date(
                      retailer.updated_at
                    ).toLocaleDateString("en-IN")}
                  </strong>
                </div>
              </div>
            )}
          </section>
        ) : (
          <section className="settings-card">
            <div className="settings-section-header">
              <div>
                <h2>Account Information</h2>
                <p>
                  Manage the login and account information
                  associated with your DigiBills account.
                </p>
              </div>
            </div>

            {accountUser && (
              <div className="settings-form-grid">
                <label>
                  Phone Number
                  <input
                    type="tel"
                    value={accountUser.phone_number}
                    readOnly
                  />
                </label>

                <label>
                  Email Address
                  <input
                    type="email"
                    value={accountUser.email || ""}
                    placeholder="No email registered"
                    readOnly
                  />
                </label>

                <label>
                  Account Status
                  <input
                    type="text"
                    value={accountUser.status}
                    readOnly
                  />
                </label>

                <label>
                  Password
                  <input
                    type="password"
                    value="********"
                    readOnly
                  />
                </label>
              </div>
            )}

            <div className="settings-password-section">
              <div className="settings-section-header">
                <div>
                  <h3>Change Password</h3>
                  <p>
                    Update the password used to sign in to
                    your DigiBills account.
                  </p>
                </div>
              </div>

              <div className="settings-form-grid">
                <label>
                  Current Password
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(event) =>
                      setCurrentPassword(event.target.value)
                    }
                    placeholder="Enter current password"
                    autoComplete="current-password"
                  />
                </label>

                <label>
                  New Password
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(event) =>
                      setNewPassword(event.target.value)
                    }
                    placeholder="Enter new password"
                    autoComplete="new-password"
                  />
                </label>

                <label>
                  Confirm New Password
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(event) =>
                      setConfirmPassword(event.target.value)
                    }
                    placeholder="Confirm new password"
                    autoComplete="new-password"
                  />
                </label>
              </div>

              <div className="settings-password-actions">
                <button
                  type="button"
                  className="primary-button"
                  onClick={changePassword}
                  disabled={passwordChanging}
                >
                  <Save size={15} />
                  {passwordChanging
                    ? "Changing..."
                    : "Change Password"}
                </button>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
