import { FormEvent, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  Eye,
  EyeOff,
  LockKeyhole,
} from "lucide-react";
import { apiFetch } from "../api";

export default function CustomerResetPassword() {
  const [searchParams] = useSearchParams();
  const token = useMemo(
    () => searchParams.get("token")?.trim() ?? "",
    [searchParams]
  );

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!token) {
      setError("This password reset link is missing or invalid.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      await apiFetch<{ message: string }>("/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({
          token,
          new_password: password,
          confirm_password: confirmPassword,
        }),
      });

      setSuccess(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to reset your password. The link may have expired."
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
              Securely protect your account and keep access to your bills,
              payments, warranties and purchases.
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
                  <LockKeyhole size={22} />
                </div>

                <h1>Create New Password</h1>

                <p>
                  Choose a strong new password for your DigiBills account.
                </p>
              </div>

              <form onSubmit={handleSubmit}>
                <label className="customer-forgot-field">
                  <span>New Password</span>

                  <div className="customer-forgot-input-wrap">
                    <LockKeyhole size={18} />

                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      placeholder="Enter your new password"
                      autoComplete="new-password"
                      required
                      minLength={8}
                    />

                    <button
                      type="button"
                      aria-label={
                        showPassword ? "Hide password" : "Show password"
                      }
                      onClick={() => setShowPassword((value) => !value)}
                      className="customer-reset-password-toggle"
                    >
                      {showPassword ? (
                        <EyeOff size={18} />
                      ) : (
                        <Eye size={18} />
                      )}
                    </button>
                  </div>
                </label>

                <label className="customer-forgot-field">
                  <span>Confirm New Password</span>

                  <div className="customer-forgot-input-wrap">
                    <LockKeyhole size={18} />

                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(event) =>
                        setConfirmPassword(event.target.value)
                      }
                      placeholder="Confirm your new password"
                      autoComplete="new-password"
                      required
                      minLength={8}
                    />

                    <button
                      type="button"
                      aria-label={
                        showConfirmPassword
                          ? "Hide password"
                          : "Show password"
                      }
                      onClick={() =>
                        setShowConfirmPassword((value) => !value)
                      }
                      className="customer-reset-password-toggle"
                    >
                      {showConfirmPassword ? (
                        <EyeOff size={18} />
                      ) : (
                        <Eye size={18} />
                      )}
                    </button>
                  </div>
                </label>

                <p className="customer-reset-password-hint">
                  Use at least 8 characters.
                </p>

                {error && (
                  <div className="customer-forgot-error">{error}</div>
                )}

                <button
                  type="submit"
                  className="customer-forgot-submit"
                  disabled={loading}
                >
                  {loading ? "Resetting Password..." : "Reset Password"}
                </button>
              </form>
            </>
          ) : (
            <div className="customer-forgot-success">
              <div className="customer-forgot-success-icon">
                <CheckCircle2 size={34} />
              </div>

              <h1>Password Updated</h1>

              <p>
                Your DigiBills password has been reset successfully. You can
                now sign in using your new password.
              </p>

              <Link
                to="/login/customer"
                className="customer-forgot-submit customer-forgot-login-link"
              >
                Continue to Login
              </Link>
            </div>
          )}

          {!success && (
            <div className="customer-forgot-footer">
              Remember your password?{" "}
              <Link to="/login/customer">Login</Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
