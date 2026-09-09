import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Mail, CheckCircle2 } from "lucide-react";
import { apiFetch } from "../api";

export default function CustomerForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");
    setSuccess(false);
    setLoading(true);

    try {
      await apiFetch<{ message: string }>("/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
        }),
      });

      setSuccess(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to process your request. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="customer-forgot-page">
      <div className="customer-forgot-shell">
        <div className="customer-forgot-visual">
          <div className="customer-forgot-glow customer-forgot-glow-one" />
          <div className="customer-forgot-glow customer-forgot-glow-two" />

          <div className="customer-forgot-visual-content">
            <div className="customer-forgot-visual-logo">
              <span className="customer-forgot-logo-mark">✣</span>
              <span>DigiBills</span>
            </div>

            <h2>
              Your Bills.
              <br />
              Always With You.
            </h2>

            <p>
              Securely recover access to your bills, payments, warranties and
              purchases.
            </p>

            <div className="customer-forgot-illustration">
              <div className="customer-forgot-lock">
                <div className="customer-forgot-lock-shackle" />
                <div className="customer-forgot-lock-body">
                  <span />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="customer-forgot-card">
          <Link to="/login/customer" className="customer-forgot-back">
            <ArrowLeft size={17} />
            Back to Login
          </Link>

          <div className="customer-forgot-brand">
            <span>✣</span>
            DigiBills
          </div>

          {!success ? (
            <>
              <div className="customer-forgot-heading">
                <div className="customer-forgot-icon">
                  <Mail size={22} />
                </div>

                <h1>Forgot Password?</h1>

                <p>
                  Enter the email address associated with your account and
                  we'll help you reset your password.
                </p>
              </div>

              <form onSubmit={handleSubmit}>
                <label className="customer-forgot-field">
                  <span>Email Address</span>

                  <div className="customer-forgot-input-wrap">
                    <Mail size={18} />
                    <input
                      type="email"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      placeholder="Enter your email address"
                      autoComplete="email"
                      required
                    />
                  </div>
                </label>

                {error && (
                  <div className="customer-forgot-error">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  className="customer-forgot-submit"
                  disabled={loading}
                >
                  {loading ? "Sending..." : "Send Reset Link"}
                </button>
              </form>
            </>
          ) : (
            <div className="customer-forgot-success">
              <div className="customer-forgot-success-icon">
                <CheckCircle2 size={34} />
              </div>

              <h1>Check Your Email</h1>

              <p>
                If an account exists with <strong>{email}</strong>, a password
                reset link will be sent to that address.
              </p>

              <Link
                to="/login/customer"
                className="customer-forgot-submit customer-forgot-login-link"
              >
                Back to Login
              </Link>
            </div>
          )}

          <div className="customer-forgot-footer">
            Remember your password?{" "}
            <Link to="/login/customer">Login</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
