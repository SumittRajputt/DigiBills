import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Store, CheckCircle2 } from "lucide-react";
import { apiFetch } from "../api";

type RegistrationResponse = {
  message: string;
  retailer_id: string;
  status: string;
  user_id: string;
};

export default function RetailerRegistration() {
  const navigate = useNavigate();

  const [businessName, setBusinessName] = useState("");
  const [businessType, setBusinessType] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState<RegistrationResponse | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setSubmitting(true);

    try {
      const response = await apiFetch<RegistrationResponse>(
        "/auth/retailer-register",
        {
          method: "POST",
          body: JSON.stringify({
            business_name: businessName.trim(),
            business_type: businessType.trim(),
            phone_number: phoneNumber.trim(),
            email: email.trim(),
            address: address.trim(),
            password,
            confirm_password: confirmPassword,
          }),
        }
      );

      setSuccess(response);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Unable to complete registration.";

      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  if (success) {
    return (
      <div className="login-page">
        <div className="login-card retailer-registration-card">
          <div className="brand large">
            <span className="brand-mark">✣</span> DigiBills
          </div>

          <div className="registration-success-icon">
            <CheckCircle2 size={46} />
          </div>

          <h1>Registration submitted</h1>

          <p>
            Your retailer account has been created and is waiting for
            administrator approval.
          </p>

          <div className="registration-success-box">
            <strong>Retailer ID</strong>
            <span>{success.retailer_id}</span>

            <strong>Status</strong>
            <span>Pending approval</span>
          </div>

          <p className="registration-note">
            Once your account is approved, you can sign in using your phone
            number and password.
          </p>

          <button
            className="login-button"
            type="button"
            onClick={() => navigate("/login/retailer")}
          >
            Go to Sign in
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="login-page">
      <div className="login-card retailer-registration-card">
        <div className="brand large">
          <span className="brand-mark">✣</span> DigiBills
        </div>

        <div className="registration-heading">
          <div className="registration-icon">
            <Store size={24} />
          </div>

          <div>
            <h1>Register your business</h1>
            <p>Create your DigiBills retailer account.</p>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="registration-section-title">
            Business details
          </div>

          <label>
            Business name
            <input
              type="text"
              value={businessName}
              onChange={(event) => setBusinessName(event.target.value)}
              placeholder="Enter business name"
              required
            />
          </label>

          <label>
            Business type
            <input
              type="text"
              value={businessType}
              onChange={(event) => setBusinessType(event.target.value)}
              placeholder="e.g. Mobile Store, Electronics"
              required
            />
          </label>

          <label>
            Business phone number
            <input
              type="tel"
              value={phoneNumber}
              onChange={(event) => setPhoneNumber(event.target.value)}
              placeholder="Enter phone number"
              required
            />
          </label>

          <label>
            Business email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Enter business email"
              required
            />
          </label>

          <label>
            Business address
            <textarea
              value={address}
              onChange={(event) => setAddress(event.target.value)}
              placeholder="Enter complete business address"
              rows={3}
              required
            />
          </label>

          <div className="registration-section-title">
            Account security
          </div>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Create password"
              minLength={8}
              required
            />
          </label>

          <label>
            Confirm password
            <input
              type="password"
              value={confirmPassword}
              onChange={(event) =>
                setConfirmPassword(event.target.value)
              }
              placeholder="Confirm password"
              minLength={8}
              required
            />
          </label>

          {error && <div className="login-error">{error}</div>}

          <button
            className="login-button"
            type="submit"
            disabled={submitting}
          >
            {submitting ? "Creating account..." : "Register as Retailer"}
          </button>
        </form>

        <div className="registration-footer">
          Already have an account?{" "}
          <Link to="/login/retailer">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
