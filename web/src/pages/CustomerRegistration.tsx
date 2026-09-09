import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Eye,
  EyeOff,
  Mail,
  Phone,
  UserRound,
  LockKeyhole,
  ArrowLeft,
} from "lucide-react";
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

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);

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

    if (!acceptedTerms) {
      setError("Please accept the Terms & Conditions to continue.");
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
      <div className="customer-registration-page">
        <div className="customer-registration-success">
          <div className="customer-registration-success-brand">
            <span>✣</span>
            DigiBills
          </div>

          <div className="customer-registration-success-icon">
            ✓
          </div>

          <h1>Registration submitted</h1>

          <p>
            Your DigiBills customer account has been created
            successfully.
          </p>

          <div className="customer-registration-result">
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

          <button
            type="button"
            className="customer-registration-submit"
            onClick={() => navigate("/login/customer")}
          >
            Go to Sign In
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="customer-registration-page">
      <div className="customer-registration-shell">

        <div className="customer-registration-visual">
          <div className="customer-registration-glow customer-registration-glow-one" />
          <div className="customer-registration-glow customer-registration-glow-two" />

          <div className="customer-registration-visual-content">
            <div className="customer-registration-brand">
              <span className="customer-registration-brand-mark">
                ✣
              </span>
              <span>DigiBills</span>
            </div>

            <div className="customer-registration-message">
              <h2>
                Your Bills.
                <br />
                Always With You.
              </h2>

              <p>
                Join DigiBills to manage all your bills,
                payments and purchases in one place.
              </p>
            </div>

            <div className="customer-registration-card-art">
              <div className="customer-registration-paper">
                <div className="customer-registration-paper-dot-row">
                  <i />
                  <i />
                  <i />
                </div>

                <div className="customer-registration-paper-title">
                  INVOICE
                </div>

                <div className="customer-registration-paper-line long" />
                <div className="customer-registration-paper-line" />
                <div className="customer-registration-paper-line medium" />

                <div className="customer-registration-paper-total">
                  <small>Total</small>
                  <strong>₹4,299</strong>
                </div>
              </div>

              <div className="customer-registration-phone-art">
                <div className="customer-registration-phone-notch" />

                <div className="customer-registration-phone-logo">
                  ✣
                </div>

                <strong>DigiBills</strong>

                <span>
                  Your bills, always with you
                </span>

                <div className="customer-registration-phone-check">
                  ✓
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="customer-registration-card">
          <button
            type="button"
            className="customer-registration-back"
            onClick={() => navigate("/login/customer")}
          >
            <ArrowLeft size={17} />
            Back
          </button>

          <div className="customer-registration-top-brand">
            <span>✣</span>
            DigiBills
          </div>

          <div className="customer-registration-heading">
            <h1>Create Your Account</h1>

            <p>
              Join DigiBills to manage all your bills
              <br className="desktop-only" />
              in one place.
            </p>
          </div>

          <form onSubmit={handleSubmit}>

            <label className="customer-registration-field">
              <span>Full Name</span>

              <div className="customer-registration-input">
                <UserRound size={18} />

                <input
                  type="text"
                  value={fullName}
                  onChange={(event) =>
                    setFullName(event.target.value)
                  }
                  placeholder="Enter your full name"
                  minLength={2}
                  maxLength={150}
                  autoComplete="name"
                  required
                />
              </div>
            </label>

            <label className="customer-registration-field">
              <span>Mobile Number</span>

              <div className="customer-registration-input">
                <Phone size={18} />

                <input
                  type="tel"
                  value={phoneNumber}
                  onChange={(event) =>
                    setPhoneNumber(event.target.value)
                  }
                  placeholder="Enter mobile number"
                  minLength={10}
                  maxLength={20}
                  autoComplete="tel"
                  required
                />
              </div>
            </label>

            <label className="customer-registration-field">
              <span>
                Email <small>(Optional)</small>
              </span>

              <div className="customer-registration-input">
                <Mail size={18} />

                <input
                  type="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  placeholder="you@example.com"
                  autoComplete="email"
                />
              </div>
            </label>

            <label className="customer-registration-field">
              <span>Password</span>

              <div className="customer-registration-input">
                <LockKeyhole size={18} />

                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  placeholder="Create a password"
                  minLength={8}
                  maxLength={72}
                  autoComplete="new-password"
                  required
                />

                <button
                  type="button"
                  className="customer-registration-eye"
                  onClick={() =>
                    setShowPassword((current) => !current)
                  }
                  aria-label={
                    showPassword
                      ? "Hide password"
                      : "Show password"
                  }
                >
                  {showPassword ? (
                    <EyeOff size={18} />
                  ) : (
                    <Eye size={18} />
                  )}
                </button>
              </div>
            </label>

            <label className="customer-registration-field">
              <span>Confirm Password</span>

              <div className="customer-registration-input">
                <LockKeyhole size={18} />

                <input
                  type={
                    showConfirmPassword
                      ? "text"
                      : "password"
                  }
                  value={confirmPassword}
                  onChange={(event) =>
                    setConfirmPassword(event.target.value)
                  }
                  placeholder="Confirm your password"
                  minLength={8}
                  maxLength={72}
                  autoComplete="new-password"
                  required
                />

                <button
                  type="button"
                  className="customer-registration-eye"
                  onClick={() =>
                    setShowConfirmPassword(
                      (current) => !current,
                    )
                  }
                  aria-label={
                    showConfirmPassword
                      ? "Hide password"
                      : "Show password"
                  }
                >
                  {showConfirmPassword ? (
                    <EyeOff size={18} />
                  ) : (
                    <Eye size={18} />
                  )}
                </button>
              </div>
            </label>

            <label className="customer-registration-terms">
              <input
                type="checkbox"
                checked={acceptedTerms}
                onChange={(event) =>
                  setAcceptedTerms(event.target.checked)
                }
              />

              <span className="customer-registration-checkbox">
                {acceptedTerms ? "✓" : ""}
              </span>

              <span>
                I agree to{" "}
                <button
                  type="button"
                  className="customer-registration-terms-link"
                  onClick={(event) => {
                    event.preventDefault();
                    setError(
                      "Terms & Conditions page will be available soon.",
                    );
                  }}
                >
                  Terms & Conditions
                </button>
              </span>
            </label>

            {error && (
              <div className="registration-error customer-registration-error">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="customer-registration-submit"
              disabled={loading}
            >
              {loading ? "Creating Account..." : "Register"}
            </button>
          </form>

          <div className="customer-registration-footer">
            Already have an account?{" "}
            <Link to="/login/customer">Login</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
