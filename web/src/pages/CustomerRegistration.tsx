import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiFetch } from "../api";

type RegistrationResponse = {
  id: string;
  phone_number: string;
  email?: string | null;
  status: string;
  is_phone_verified: boolean;
  roles: string[];
};

export default function CustomerRegistration() {
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<RegistrationResponse | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      const response = await apiFetch<RegistrationResponse>(
        "/auth/register",
        {
          method: "POST",
          body: JSON.stringify({
            full_name: fullName.trim(),
            phone_number: phoneNumber.trim(),
            email: email.trim() || null,
            password,
            confirm_password: confirmPassword,
          }),
        },
      );

      setSuccess(response);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to create your customer account.",
      );
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div className="registration-page">
        <div className="registration-card registration-success-card">
          <div className="registration-brand">
            <div className="registration-brand-icon">✣</div>
            <span>DigiBills</span>
          </div>

          <div className="registration-success-icon">✓</div>

          <div className="registration-success-content">
            <h1>Registration submitted</h1>

            <p>
              Your DigiBills customer account has been created
              successfully.
            </p>

            <div className="registration-result-grid">
              <div>
                <span>Phone</span>
                <strong>{success.phone_number}</strong>
              </div>

              <div>
                <span>Account Status</span>
                <strong>{success.status}</strong>
              </div>

              <div>
                <span>Account Type</span>
                <strong>Customer</strong>
              </div>
            </div>
          </div>

          <button
            type="button"
            className="registration-primary-button"
            onClick={() => navigate("/login")}
          >
            Go to Sign In
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="registration-page">
      <div className="registration-card">
        <div className="registration-brand">
          <div className="registration-brand-icon">✣</div>
          <span>DigiBills</span>
        </div>

        <div className="registration-header">
          <h1>Create your DigiBills customer account</h1>
          <p>
            Register to manage your invoices, payments, warranties
            and products in one place.
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <section className="registration-section">
            <h2>Personal details</h2>

            <div className="registration-grid">
              <label className="registration-full-width">
                <span>Full Name</span>
                <input
                  type="text"
                  value={fullName}
                  onChange={(event) =>
                    setFullName(event.target.value)
                  }
                  placeholder="Enter your full name"
                  minLength={2}
                  maxLength={150}
                  required
                />
              </label>

              <label>
                <span>Phone Number</span>
                <input
                  type="tel"
                  value={phoneNumber}
                  onChange={(event) =>
                    setPhoneNumber(event.target.value)
                  }
                  placeholder="Enter phone number"
                  minLength={10}
                  maxLength={20}
                  required
                />
              </label>

              <label>
                <span>Email <small>(Optional)</small></span>
                <input
                  type="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  placeholder="you@example.com"
                />
              </label>
            </div>
          </section>

          <section className="registration-section">
            <h2>Account security</h2>

            <div className="registration-grid">
              <label>
                <span>Password</span>
                <input
                  type="password"
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  placeholder="Create a password"
                  minLength={8}
                  maxLength={72}
                  required
                />
              </label>

              <label>
                <span>Confirm Password</span>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(event) =>
                    setConfirmPassword(event.target.value)
                  }
                  placeholder="Confirm your password"
                  minLength={8}
                  maxLength={72}
                  required
                />
              </label>
            </div>
          </section>

          {error && (
            <div className="registration-error">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="registration-primary-button"
            disabled={loading}
          >
            {loading
              ? "Creating Customer Account..."
              : "Create Customer Account"}
          </button>
        </form>

        <div className="registration-footer">
          Already have an account?{" "}
          <Link to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
