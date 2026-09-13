import { useEffect, useState } from "react";
import {
  CheckCircle2,
  Clock3,
  LockKeyhole,
  ShieldCheck,
  Smartphone,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api";

type SecurityUser = {
  phone_number: string;
  email: string | null;
  status: string;
  is_phone_verified: boolean;
  last_login_at: string | null;
};

export default function CustomerAccountSecurity() {
  const navigate = useNavigate();

  const [user, setUser] = useState<SecurityUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadSecurity() {
      try {
        setLoading(true);

        const result = await apiFetch<SecurityUser>("/auth/me");

        setUser(result);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    }

    loadSecurity();
  }, []);

  function formatLastLogin(value: string | null) {
    if (!value) return "Not available";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "Not available";
    }

    return date.toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  if (loading) {
    return (
      <section className="dashboard customer-dashboard-page customer-security-page">
        <div className="table-state">
          Loading security information...
        </div>
      </section>
    );
  }

  return (
    <section className="dashboard customer-dashboard-page customer-security-page">
      <div className="page-heading customer-security-heading">
        <div>
          <h1>Account Security</h1>
          <p>
            Review your account protection and security information.
          </p>
        </div>
      </div>

      <div className="customer-security-grid">
        <div className="panel customer-security-panel">
          <div className="panel-header">
            <div>
              <h3>
                <ShieldCheck size={18} />
                Security Overview
              </h3>
              <span>
                Current security status of your account
              </span>
            </div>
          </div>

          <div className="customer-security-status-list">
            <div className="customer-security-status-item">
              <div className="customer-security-status-icon">
                <CheckCircle2 size={18} />
              </div>

              <div>
                <span>Account Status</span>
                <strong className="customer-security-success">
                  {user?.status
                    ? user.status.charAt(0).toUpperCase() +
                      user.status.slice(1)
                    : "Unknown"}
                </strong>
              </div>
            </div>

            <div className="customer-security-status-item">
              <div className="customer-security-status-icon">
                <Smartphone size={18} />
              </div>

              <div>
                <span>Phone Verification</span>
                <strong
                  className={
                    user?.is_phone_verified
                      ? "customer-security-success"
                      : "customer-security-warning"
                  }
                >
                  {user?.is_phone_verified
                    ? "Verified"
                    : "Not verified"}
                </strong>
              </div>
            </div>

            <div className="customer-security-status-item">
              <div className="customer-security-status-icon">
                <LockKeyhole size={18} />
              </div>

              <div>
                <span>Password Protection</span>
                <strong className="customer-security-success">
                  Protected
                </strong>
              </div>
            </div>

            <div className="customer-security-status-item">
              <div className="customer-security-status-icon">
                <Clock3 size={18} />
              </div>

              <div>
                <span>Last Login</span>
                <strong>
                  {formatLastLogin(user?.last_login_at ?? null)}
                </strong>
              </div>
            </div>
          </div>
        </div>

        <div className="panel customer-security-panel">
          <div className="panel-header">
            <div>
              <h3>
                <LockKeyhole size={18} />
                Password Security
              </h3>
              <span>
                Keep your account password up to date
              </span>
            </div>
          </div>

          <div className="customer-security-action">
            <div className="customer-security-action-icon">
              <LockKeyhole size={22} />
            </div>

            <div className="customer-security-action-content">
              <strong>Password protection</strong>
              <span>
                Your account is protected with a password.
                Change it regularly to keep your account secure.
              </span>
            </div>

            <button
              type="button"
              className="primary-button"
              onClick={() => navigate("/customer/settings")}
            >
              Change Password
            </button>
          </div>
        </div>
      </div>

      <div className="panel customer-security-info-panel">
        <div className="panel-header">
          <div>
            <h3>Account Protection</h3>
            <span>
              Security information associated with your customer account
            </span>
          </div>
        </div>

        <div className="customer-security-info-grid">
          <div>
            <span>Phone Number</span>
            <strong>{user?.phone_number || "Not provided"}</strong>
          </div>

          <div>
            <span>Email Address</span>
            <strong>{user?.email || "Not provided"}</strong>
          </div>

          <div>
            <span>Phone Verification</span>
            <strong>
              {user?.is_phone_verified
                ? "Verified"
                : "Not verified"}
            </strong>
          </div>
        </div>
      </div>
    </section>
  );
}
