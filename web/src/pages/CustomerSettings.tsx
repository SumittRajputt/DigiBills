import { useEffect, useState } from "react";
import { LockKeyhole, ShieldCheck } from "lucide-react";
import { apiFetch } from "../api";

type AccountUser = {
  id: string;
  email: string | null;
  phone_number: string | null;
  status: string;
  is_phone_verified: boolean;
};

type CustomerProfile = {
  id: string;
  user_id: string;
  name: string | null;
  email: string | null;
  phone: string | null;
};

type PasswordForm = {
  current_password: string;
  new_password: string;
  confirm_password: string;
};

export default function CustomerSettings() {
  const [user, setUser] = useState<AccountUser | null>(null);
  const [customer, setCustomer] =
    useState<CustomerProfile | null>(null);

  const [passwordForm, setPasswordForm] =
    useState<PasswordForm>({
      current_password: "",
      new_password: "",
      confirm_password: "",
    });

  const [loading, setLoading] = useState(true);
  const [changingPassword, setChangingPassword] =
    useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function loadSettings() {
    try {
      setLoading(true);
      setError("");

      const [userData, customerData] =
        await Promise.all([
          apiFetch<AccountUser>("/auth/me"),
          apiFetch<CustomerProfile>("/customers/me"),
        ]);

      setUser(userData);
      setCustomer(customerData);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load settings."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSettings();
  }, []);

  async function changePassword() {
    setError("");
    setSuccess("");

    if (
      !passwordForm.current_password ||
      !passwordForm.new_password ||
      !passwordForm.confirm_password
    ) {
      setError("Please fill in all password fields.");
      return;
    }

    if (
      passwordForm.new_password !==
      passwordForm.confirm_password
    ) {
      setError("New passwords do not match.");
      return;
    }

    if (passwordForm.new_password.length < 8) {
      setError(
        "New password must be at least 8 characters."
      );
      return;
    }

    try {
      setChangingPassword(true);

      await apiFetch<{ message: string }>(
        "/auth/change-password",
        {
          method: "PUT",
          body: JSON.stringify({
            current_password:
              passwordForm.current_password,
            new_password: passwordForm.new_password,
          }),
        }
      );

      setSuccess("Password changed successfully.");

      setPasswordForm({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to change password."
      );
    } finally {
      setChangingPassword(false);
    }
  }

  if (loading) {
    return (
      <section className="dashboard customer-dashboard-page">
        <div className="table-state">
          Loading settings...
        </div>
      </section>
    );
  }

  return (
    <section className="dashboard customer-dashboard-page customer-settings-page">
      <div className="page-heading customer-settings-heading">
        <div>
          <h1>Settings</h1>
          <p>
            Manage your account and security settings.
          </p>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {success && (
        <div className="success-message">
          {success}
        </div>
      )}

      <div className="settings-grid customer-settings-grid">
        <div className="panel customer-settings-panel">
          <div className="panel-header">
            <div>
              <h3>Account Information</h3>
              <span>
                Your DigiBills account information
              </span>
            </div>
          </div>

          <div className="settings-fields">
            <div className="settings-field">
              <span>Email</span>
              <strong>
                {user?.email ||
                  customer?.email ||
                  "Not provided"}
              </strong>
            </div>

            <div className="settings-field">
              <span>Phone Number</span>
              <strong>
                {user?.phone_number ||
                  customer?.phone ||
                  "Not provided"}
              </strong>
            </div>

            <div className="settings-field">
              <span>Account Status</span>
              <strong className="settings-value-capitalize">
                {user?.status || "—"}
              </strong>
            </div>

            <div className="settings-field">
              <span>Phone Verification</span>
              <strong>
                {user?.is_phone_verified
                  ? "Verified"
                  : "Not verified"}
              </strong>
            </div>

            <div className="settings-field">
              <span>Customer ID</span>
              <strong>
                {customer?.id || "—"}
              </strong>
            </div>
          </div>
        </div>

        <div className="panel customer-settings-panel">
          <div className="panel-header">
            <div>
              <h3>
                <LockKeyhole size={18} />
                Security
              </h3>
              <span>
                Change your account password
              </span>
            </div>

            <ShieldCheck size={22} />
          </div>

          <div className="customer-settings-password-form">
            <label>
              Current Password
              <input
                type="password"
                value={passwordForm.current_password}
                onChange={(event) =>
                  setPasswordForm({
                    ...passwordForm,
                    current_password:
                      event.target.value,
                  })
                }
                autoComplete="current-password"
              />
            </label>

            <label>
              New Password
              <input
                type="password"
                value={passwordForm.new_password}
                onChange={(event) =>
                  setPasswordForm({
                    ...passwordForm,
                    new_password:
                      event.target.value,
                  })
                }
                autoComplete="new-password"
              />
            </label>

            <label>
              Confirm New Password
              <input
                type="password"
                value={passwordForm.confirm_password}
                onChange={(event) =>
                  setPasswordForm({
                    ...passwordForm,
                    confirm_password:
                      event.target.value,
                  })
                }
                autoComplete="new-password"
              />
            </label>

            <button
              type="button"
              className="primary-button"
              onClick={changePassword}
              disabled={changingPassword}
            >
              {changingPassword
                ? "Changing Password..."
                : "Change Password"}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
