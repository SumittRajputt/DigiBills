import { FormEvent, useEffect, useState } from "react";
import {
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import {
  ArrowLeft,
  Eye,
  EyeOff,
  LockKeyhole,
  Bell,
  ChevronDown,
  CircleHelp,
  MoreHorizontal,
  Home,
  Headphones,
  FileText,
  LayoutDashboard,
  LogOut,
  Menu,
  Search,
  ShieldCheck,
  Store,
  UserRound,
  UsersRound,
} from "lucide-react";

import AdminDashboard from "./dashboards/AdminDashboard";
import AdminAuditLogs from "./pages/AdminAuditLogs";
import RetailerDashboard from "./dashboards/RetailerDashboard";
import RetailerInventory from "./pages/RetailerInventory";
import RetailerSuppliers from "./pages/RetailerSuppliers";
import RetailerPayments from "./pages/RetailerPayments";
import RetailerSettings from "./pages/RetailerSettings";
import RetailerCustomers from "./pages/RetailerCustomers";
import RetailerEmployees from "./pages/RetailerEmployees";
import RetailerPurchases from "./pages/RetailerPurchases";
import CustomerDashboard from "./dashboards/CustomerDashboard";
import CustomerInvoices from "./pages/CustomerInvoices";
import CustomerPayments from "./pages/CustomerPayments";
import CustomerWarranty from "./pages/CustomerWarranty";
import CustomerTransfers from "./pages/CustomerTransfers";
import CustomerSupport from "./pages/CustomerSupport";
import CustomerSettings from "./pages/CustomerSettings";
import CustomerSubscription from "./pages/CustomerSubscription";
import CustomerProducts from "./pages/CustomerProducts";
import CustomerProfile from "./pages/CustomerProfile";
import CashierDashboard from "./dashboards/CashierDashboard";
import AdminRetailers from "./pages/AdminRetailers";
import AdminUsers from "./pages/AdminUsers";
import AdminCustomers from "./pages/AdminCustomers";
import AdminProducts from "./pages/AdminProducts";
import AdminInvoices from "./pages/AdminInvoices";
import AdminPayments from "./pages/AdminPayments";
import AdminWarranty from "./pages/AdminWarranty";
import AdminReports from "./pages/AdminReports";
import AdminReturns from "./pages/AdminReturns";
import RetailerReturns from "./pages/RetailerReturns";
import RetailerWarranty from "./pages/RetailerWarranty";
import RetailerReports from "./pages/RetailerReports";
import AdminSettings from "./pages/AdminSettings";
import RetailerRegistration from "./pages/RetailerRegistration";
import CustomerRegistration from "./pages/CustomerRegistration";
import CustomerForgotPassword from "./pages/CustomerForgotPassword";
import CustomerResetPassword from "./pages/CustomerResetPassword";
import { apiFetch } from "./api";

type Role =
  | "super_admin"
  | "retailer_owner"
  | "customer"
  | "cashier"
  | "retailer_manager"
  | "inventory_manager"
  | "salesman";

const retailerNavPaths: Record<string, string> = {
  Dashboard: "/retailer",
  Products: "/retailer/products",
  Inventory: "/retailer/inventory",
  Invoices: "/retailer/invoices",
  Payments: "/retailer/payments",
  Customers: "/retailer/customers",
  Employees: "/retailer/employees",
  Purchases: "/retailer/purchases",
  Returns: "/retailer/returns",
  Suppliers: "/retailer/suppliers",
  Warranty: "/retailer/warranty",
  Reports: "/retailer/reports",
  Settings: "/retailer/settings",
};

function RetailerPlaceholder({ title }: { title: string }) {
  return (
    <section className="dashboard retailer-placeholder-page">
      <div className="page-heading">
        <span className="page-eyebrow">RETAILER MANAGEMENT</span>
        <h1>{title}</h1>
        <p>This retailer module is ready for implementation.</p>
      </div>

      <div className="panel">
        <div className="panel-header">
          <div>
            <h3>{title}</h3>
            <span>The navigation route is active.</span>
          </div>
        </div>

        <div style={{ padding: "28px 20px", color: "#7d8998", fontSize: "13px" }}>
          {title} page will be built here.
        </div>
      </div>
    </section>
  );
}

type User = {
  id: string;
  phone_number: string;
  email?: string | null;
  status: string;
  is_phone_verified: boolean;
  roles: string[];
};

const roleMeta = {
  super_admin: {
    label: "Super Admin",
    shortLabel: "Super Admin",
    color: "#1769ff",
    path: "/admin",
  },
  retailer_owner: {
    label: "Retailer",
    shortLabel: "Retailer",
    color: "#11a36a",
    path: "/retailer",
  },
  customer: {
    label: "Customer",
    shortLabel: "Customer",
    color: "#7352d6",
    path: "/customer",
  },
  cashier: {
    label: "Cashier",
    shortLabel: "Cashier",
    color: "#1769ff",
    path: "/employee/cashier",
  },
  retailer_manager: {
    label: "Retailer Manager",
    shortLabel: "Manager",
    color: "#11a36a",
    path: "/employee/manager",
  },
  inventory_manager: {
    label: "Inventory Manager",
    shortLabel: "Inventory",
    color: "#7352d6",
    path: "/employee/inventory",
  },
  salesman: {
    label: "Salesman",
    shortLabel: "Salesman",
    color: "#d97706",
    path: "/employee/salesman",
  },
};

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = sessionStorage.getItem("digibills_token");

    if (!token) {
      setLoading(false);
      return;
    }

    apiFetch<User>("/auth/me")
      .then((currentUser) => {
        setUser(currentUser);
      })
      .catch(() => {
        sessionStorage.removeItem("digibills_token");
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="launcher">
        <div className="launcher-card">
          <div className="brand large">
            <span className="brand-mark">✣</span> DigiBills
          </div>
          <p>Loading your account...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>

      <Route
        path="/retailer-register"
        element={<RetailerRegistration />}
      />

      <Route
        path="/customer-register"
        element={<CustomerRegistration />}
      />

      <Route
        path="/customer-forgot-password"
        element={<CustomerForgotPassword />}
      />

      <Route
        path="/customer-reset-password"
        element={<CustomerResetPassword />}
      />

      <Route
        path="/register"
        element={<AccountTypePage mode="register" />}
      />

      <Route
        path="/login"
        element={
          user ? (
            <NavigateToRole user={user} />
          ) : (
            <AccountTypePage mode="login" />
          )
        }
      />

      <Route
        path="/login/retailer"
        element={
          user ? (
            <NavigateToRole user={user} />
          ) : (
            <LoginPage
              onLogin={setUser}
              accountType="retailer"
            />
          )
        }
      />

      <Route
        path="/login/customer"
        element={
          user ? (
            <NavigateToRole user={user} />
          ) : (
            <LoginPage
              onLogin={setUser}
              accountType="customer"
            />
          )
        }
      />

      <Route
        path="/login/admin"
        element={
          user ? (
            <NavigateToRole user={user} />
          ) : (
            <LoginPage
              onLogin={setUser}
              accountType="admin"
            />
          )
        }
      />

      <Route
        path="/login/employee"
        element={
          user ? (
            <NavigateToRole user={user} />
          ) : (
            <LoginPage
              onLogin={setUser}
              accountType="employee"
            />
          )
        }
      />

      <Route
        path="/admin/*"
        element={
          <ProtectedRoute user={user} role="super_admin">
            <DashboardFrame role="super_admin" user={user!}>
              <Routes>
                <Route
                  index
                  element={<AdminDashboard />}
                />
                <Route
                  path="retailers"
                  element={<AdminRetailers />}
                />
                <Route
                  path="users"
                  element={<AdminUsers />}
                />
                <Route
                  path="customers"
                  element={<AdminCustomers />}
                />
                <Route
                  path="products"
                  element={<AdminProducts />}
                />
                <Route
                  path="invoices"
                  element={<AdminInvoices />}
                />

                <Route
                  path="payments"
                  element={<AdminPayments />}
                />
                <Route
                  path="warranty"
                  element={<AdminWarranty />}
                />
                <Route
                  path="returns"
                  element={<AdminReturns />}
                />
                <Route
                  path="audit-logs"
                  element={<AdminAuditLogs />}
                />
                <Route
                  path="reports"
                  element={<AdminReports />}
                />
                <Route
                  path="settings"
                  element={<AdminSettings />}
                />
              </Routes>
            </DashboardFrame>
          </ProtectedRoute>
        }
      />

      <Route
        path="/retailer/*"
        element={
          <ProtectedRoute user={user} role="retailer_owner">
            <DashboardFrame role="retailer_owner" user={user!}>
              <Routes>
                <Route
                  index
                  element={<RetailerDashboard />}
                />
                <Route
                  path="products"
                  element={<AdminProducts />}
                />
                <Route
                  path="invoices"
                  element={<AdminInvoices />}
                />
                <Route
                  path="inventory"
                  element={<RetailerInventory />}
                />
                <Route
                  path="payments"
                  element={<RetailerPayments />}
                />
                <Route
                  path="customers"
                  element={<RetailerCustomers />}
                />
                <Route
                  path="employees"
                  element={<RetailerEmployees />}
                />
                <Route
                  path="purchases"
                  element={<RetailerPurchases />}
                />
                <Route
                  path="returns"
                  element={<RetailerReturns />}
                />
                <Route
                  path="suppliers"
                  element={<RetailerSuppliers />}
                />
                <Route
                  path="warranty"
                  element={<RetailerWarranty />}
                />
                <Route
                  path="reports"
                  element={<RetailerReports />}
                />
                <Route
                  path="settings"
                  element={<RetailerSettings />}
                />
                <Route
                  path="products"
                  element={<AdminProducts />}
                />
                <Route
                  path="invoices"
                  element={<AdminInvoices />}
                />
              </Routes>
            </DashboardFrame>
          </ProtectedRoute>
        }
      />

      <Route
        path="/employee/cashier"
        element={
          <ProtectedRoute user={user} role="cashier">
            <DashboardFrame role="cashier" user={user!}>
              <CashierDashboard />
            </DashboardFrame>
          </ProtectedRoute>
        }
      />

      <Route
        path="/customer/*"
        element={
          <ProtectedRoute user={user} role="customer">
            <DashboardFrame role="customer" user={user!}>
              <Routes>
                <Route
                  index
                  element={<CustomerDashboard />}
                />
                <Route
                  path="profile"
                  element={<CustomerProfile />}
                />

                <Route
                  path="invoices"
                  element={<CustomerInvoices />}
                />

                <Route
                  path="invoices/:invoiceId"
                  element={<CustomerInvoices />}
                />

                <Route
                  path="payments"
                  element={<CustomerPayments />}
                />

                <Route
                  path="warranty"
                  element={<CustomerWarranty />}
                />

                <Route
                  path="transfers"
                  element={<CustomerTransfers />}
                />

                <Route
                  path="support"
                  element={<CustomerSupport />}
                />

                <Route
                  path="settings"
                  element={<CustomerSettings />}
                />

                <Route
                  path="subscription"
                  element={<CustomerSubscription />}
                />

                <Route
                  path="products"
                  element={<CustomerProducts />}
                />


              </Routes>
            </DashboardFrame>
          </ProtectedRoute>
        }
      />

      <Route
        path="/"
        element={
          user ? (
            <NavigateToRole user={user} />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />

      <Route
        path="*"
        element={
          user ? (
            <NavigateToRole user={user} />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
    </Routes>
  );
}

function AccountTypePage({
  mode,
}: {
  mode: "login" | "register";
}) {
  const navigate = useNavigate();
  const isLogin = mode === "login";

  function handleRetailer() {
    navigate(isLogin ? "/login/retailer" : "/retailer-register");
  }

  function handleCustomer() {
    navigate(isLogin ? "/login/customer" : "/customer-register");
  }

  function handleAdmin() {
    navigate("/login/admin");
  }

  function handleEmployee() {
    navigate("/login/employee");
  }

  return (
    <div className="account-type-page">
      <div className="account-type-card">
        <div className="brand large">
          <span className="brand-mark">✣</span> DigiBills
        </div>

        <div className="account-type-heading">
          <span className="account-type-eyebrow">
            {isLogin ? "ACCOUNT ACCESS" : "GET STARTED"}
          </span>

          <h1>
            {isLogin ? "Welcome back" : "Create your account"}
          </h1>

          <p>
            {isLogin
              ? "Choose how you want to sign in to DigiBills."
              : "Choose the account type that fits you best."}
          </p>
        </div>

        <div className="account-type-options">
          <button
            type="button"
            className="account-type-option retailer"
            onClick={handleRetailer}
          >
            <span className="account-type-icon">
              <Store size={22} strokeWidth={1.8} />
            </span>

            <span className="account-type-content">
              <strong>Retailer</strong>
              <span>
                {isLogin
                  ? "Manage your store and business"
                  : "Create a retailer account"}
              </span>
            </span>

            <span className="account-type-arrow">→</span>
          </button>

          <button
            type="button"
            className="account-type-option customer"
            onClick={handleCustomer}
          >
            <span className="account-type-icon">
              <UserRound size={22} strokeWidth={1.8} />
            </span>

            <span className="account-type-content">
              <strong>Customer</strong>
              <span>
                {isLogin
                  ? "Manage your bills and purchases"
                  : "Create a customer account"}
              </span>
            </span>

            <span className="account-type-arrow">→</span>
          </button>

          {isLogin && (
            <>
              <button
                type="button"
                className="account-type-option admin"
                onClick={handleAdmin}
              >
                <span className="account-type-icon">
                  <ShieldCheck size={22} strokeWidth={1.8} />
                </span>

                <span className="account-type-content">
                  <strong>Admin</strong>
                  <span>Manage DigiBills platform settings</span>
                </span>

                <span className="account-type-arrow">&rarr;</span>
              </button>

              <button
                type="button"
                className="account-type-option employee"
              onClick={handleEmployee}
            >
              <span className="account-type-icon">
                <UsersRound size={22} strokeWidth={1.8} />
              </span>

              <span className="account-type-content">
                <strong>Employee</strong>
                <span>Access your assigned work dashboard</span>
              </span>

              <span className="account-type-arrow">→</span>
              </button>
            </>
          )}
        </div>

        <div className="account-type-footer">
          {isLogin ? (
            <>
              Don't have a DigiBills account?{" "}
              <Link to="/register">Register</Link>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <Link to="/login">Sign in</Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function LoginPage({
  onLogin,
  accountType,
}: {
  onLogin: (user: User) => void;
  accountType: "admin" | "retailer" | "customer" | "employee";
}) {
  const navigate = useNavigate();

  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const isRetailer = accountType === "retailer";
  const isAdmin = accountType === "admin";
  const isEmployee = accountType === "employee";
  const isCustomer = accountType === "customer";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");
    setSubmitting(true);

    try {
      const tokenResponse = await apiFetch<{
        access_token: string;
        token_type: string;
      }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          phone_number: phoneNumber.trim(),
          password,
          account_type: accountType,
        }),
      });

      sessionStorage.setItem(
        "digibills_token",
        tokenResponse.access_token
      );

      const user = await apiFetch<User>("/auth/me");

      onLogin(user);
      navigate(getRolePath(user), { replace: true });
    } catch {
      sessionStorage.removeItem("digibills_token");

      setError(
        isAdmin
          ? "Invalid admin phone number or password."
          : isRetailer
            ? "Invalid retailer phone number or password."
            : isEmployee
              ? "Invalid employee phone number or password."
              : "Invalid customer phone number or password."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className={`login-page account-login-page ${
        isCustomer ? "customer-login-page" : ""
      }`}
    >
      <div className="customer-login-shell">
        {isCustomer && (
          <div className="customer-login-visual">
            <div className="customer-login-glow customer-login-glow-one" />
            <div className="customer-login-glow customer-login-glow-two" />

            <div className="customer-login-visual-content">
              <div className="customer-login-visual-logo">
                <span className="customer-login-visual-logo-mark">✣</span>
                <span>DigiBills</span>
              </div>

              <h2>Your Bills.<br />Always With You.</h2>

              <p>
                Keep your invoices, payments, warranties and purchases
                together in one simple place.
              </p>

              <div className="customer-login-illustration">
                <div className="customer-login-illustration-card">
                  <div className="customer-login-illustration-card-top">
                    <span />
                    <span />
                    <span />
                  </div>

                  <div className="customer-login-illustration-lines">
                    <i />
                    <i />
                    <i />
                    <i />
                  </div>

                  <div className="customer-login-illustration-total">
                    <small>Total</small>
                    <strong>₹24,560</strong>
                  </div>
                </div>

                <div className="customer-login-illustration-phone">
                  <div className="customer-login-phone-notch" />
                  <div className="customer-login-phone-logo">✣</div>
                  <strong>DigiBills</strong>
                  <span>Your bills, always with you</span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="login-card account-login-card customer-login-card">
          <button
            type="button"
            className="login-back-button"
            onClick={() => navigate("/login")}
          >
            <ArrowLeft size={17} />
            Back
          </button>

          <div className="brand large">
            <span className="brand-mark">✣</span>
            DigiBills
          </div>

          <div className="account-login-heading">
            <span
              className={`account-login-badge ${
                isRetailer ? "retailer" : "customer"
              }`}
            >
              <UserRound size={15} />
              {isRetailer ? "Retailer" : "Customer"}
            </span>

            <h1>
              {isRetailer
                ? "Retailer sign in"
                : "Welcome back!"}
            </h1>

            <p>
              {isRetailer
                ? "Sign in to continue to your DigiBills store."
                : "Sign in to manage your bills and purchases."}
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <label className="customer-login-field">
              <span>Email or Mobile Number</span>

              <div className="customer-login-input-wrap">
                <UserRound size={18} />
                <input
                  type="text"
                  value={phoneNumber}
                  onChange={(event) =>
                    setPhoneNumber(event.target.value)
                  }
                  placeholder="Enter mobile number"
                  autoComplete="tel"
                  required
                />
              </div>
            </label>

            <label className="customer-login-field">
              <span>Password</span>

              <div className="customer-login-input-wrap">
                <LockKeyhole size={18} className="customer-login-lock-icon" />

                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  placeholder="Enter password"
                  autoComplete="current-password"
                  required
                />

                <button
                  type="button"
                  className="customer-login-password-toggle"
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

            <div className="customer-login-options">
              <label className="customer-login-remember">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(event) =>
                    setRememberMe(event.target.checked)
                  }
                />
                <span className="customer-login-checkmark">
                  {rememberMe ? "✓" : ""}
                </span>
                <span>Remember me</span>
              </label>

              <button
                type="button"
                className="customer-login-forgot"
                onClick={() => navigate("/customer-forgot-password")}
              >
                Forgot Password?
              </button>
            </div>

            {error && (
              <div className="login-error">
                {error}
              </div>
            )}

            <button
              className={`login-button ${
                isRetailer ? "retailer" : "customer"
              } customer-login-submit`}
              type="submit"
              disabled={submitting}
            >
              {submitting ? "Signing in..." : "Login"}
            </button>
          </form>

          <div className="registration-footer customer-login-register">
            Don't have an account?{" "}
            <Link to="/customer-register">Register</Link>
          </div>
        </div>
      </div>
    </div>
  );
}

function ProtectedRoute({
  user,
  role,
  children,
}: {
  user: User | null;
  role: Role;
  children: React.ReactNode;
}) {
  const location = useLocation();

  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location.pathname }}
      />
    );
  }

  if (!user.roles.includes(role)) {
    return <Navigate to={getRolePath(user)} replace />;
  }

  return <>{children}</>;
}

function NavigateToRole({ user }: { user: User }) {
  return <Navigate to={getRolePath(user)} replace />;
}

function getRolePath(user: User): string {
  if (user.roles.includes("super_admin")) {
    return "/admin";
  }

  if (user.roles.includes("retailer_owner")) {
    return "/retailer";
  }

  if (user.roles.includes("customer")) {
    return "/customer";
  }

  if (user.roles.includes("cashier")) {
    return "/employee/cashier";
  }

  if (user.roles.includes("retailer_manager")) {
    return "/employee/manager";
  }

  if (user.roles.includes("inventory_manager")) {
    return "/employee/inventory";
  }

  if (user.roles.includes("salesman")) {
    return "/employee/salesman";
  }

  return "/login";
}

function DashboardFrame({
  role,
  user,
  children,
}: {
  role: Role;
  user: User;
  children: React.ReactNode;
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const [query, setQuery] = useState("");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const nav = {
    super_admin: [
      "Overview",
      "Retailers",
      "Users",
      "Customers",
      "Products",
      "Invoices",
      "Payments",
      "Returns & Refunds",
      "Warranty",
      "Reports & Analytics",
      "Audit Logs",
      "System Settings",
    ],
    retailer_owner: [
      "Dashboard",
      "Products",
      "Inventory",
      "Invoices",
      "Payments",
      "Customers",
      "Employees",
      "Purchases",
      "Returns",
      "Suppliers",
      "Warranty",
      "Reports",
      "Settings",
    ],
    customer: [
      "My Orders",
      "My Payments",
      "My Products",
      "My Returns",
      "Transfer Bills",
      "Subscription",
      "Support",
      "Settings",
    ],
    cashier: [
      "Dashboard",
      "Invoices",
      "Customers",
      "Payments",
    ],
    retailer_manager: [
      "Dashboard",
      "Products",
      "Inventory",
      "Invoices",
      "Payments",
      "Customers",
      "Employees",
      "Reports",
    ],
    inventory_manager: [
      "Dashboard",
      "Products",
      "Inventory",
      "Purchases",
      "Suppliers",
      "Returns",
    ],
    salesman: [
      "Dashboard",
      "Customers",
      "Subscriptions",
      "Sales",
    ],
  }[role];

  const icons = [
    LayoutDashboard,
    Store,
    UserRound,
    UserRound,
    Store,
    LayoutDashboard,
    LayoutDashboard,
    LayoutDashboard,
    LayoutDashboard,
    ShieldCheck,
    LayoutDashboard,
  ];

  const meta = roleMeta[role];

  function logout() {
    sessionStorage.removeItem("digibills_token");
    navigate("/login", { replace: true });
  }

  function closeMobileMenu() {
    setMobileMenuOpen(false);
  }

  useEffect(() => {
    function openMobileMenu() {
      if (role === "customer") {
        setMobileMenuOpen(true);
      }
    }

    window.addEventListener(
      "digibills:open-mobile-menu",
      openMobileMenu
    );

    return () => {
      window.removeEventListener(
        "digibills:open-mobile-menu",
        openMobileMenu
      );
    };
  }, [role]);

  const initials =
    role === "customer"
      ? getInitials(user.email || user.phone_number)
      : role === "retailer_owner"
        ? "TZ"
        : "SA";

  return (
    <div className="app-shell">
      <aside
        className="sidebar"
        style={{ "--accent": meta.color } as React.CSSProperties}
      >
        <div className="brand">
          <span className="brand-mark">✣</span> DigiBills
        </div>

        <div className="profile-mini">
          <div className="avatar">{initials}</div>

          <div>
            <strong>{meta.label}</strong>
            <small>
              {user.email || user.phone_number}
            </small>
          </div>
        </div>

        <nav>
          {nav.map((item, index) => {
            const Icon = icons[index % icons.length];

            return (
              <button
                key={item}
                className={`nav-item ${
                  (role === "super_admin" &&
                    (
                      (item === "Overview" && location.pathname === "/admin") ||
                      (item === "Retailers" && location.pathname === "/admin/retailers") ||
                      (item === "Users" && location.pathname === "/admin/users") ||
                      (item === "Customers" && location.pathname === "/admin/customers") ||
                      (item === "Products" && location.pathname === "/admin/products") ||
                      (item === "Invoices" && location.pathname === "/admin/invoices") ||
                      (item === "Payments" && location.pathname === "/admin/payments") ||
                      (item === "Returns & Refunds" && location.pathname === "/admin/returns") ||
                      (item === "Warranty" && location.pathname === "/admin/warranty") ||
                      (item === "Reports & Analytics" && location.pathname === "/admin/reports") ||
                      (item === "System Settings" && location.pathname === "/admin/settings")
                    )) ||
                  (
                    role === "retailer_owner" &&
                    location.pathname === retailerNavPaths[item]
                  ) ||
                  (
                    role === "customer" &&
                    (
                      (item === "Dashboard" &&
                        location.pathname === "/customer") ||
                      (item === "My Profile" &&
                        location.pathname === "/customer/profile") ||
                      (item === "My Invoices" &&
                        location.pathname.startsWith("/customer/invoices")) ||
                      (item === "My Payments" &&
                        location.pathname === "/customer/payments") ||
                      (item === "My Warranty" &&
                        location.pathname === "/customer/warranty") ||
                      (item === "Transfer Bills" &&
                        location.pathname === "/customer/transfers") ||
                      (item === "Subscription" &&
                        location.pathname === "/customer/subscription") ||
                      (item === "Support" &&
                        location.pathname === "/customer/support") ||
                      (item === "Settings" &&
                        location.pathname === "/customer/settings")
                    )
                  )
                    ? "active"
                    : ""
                }`}
                type="button"
                onClick={() => {
                  if (
                    role === "retailer_owner" &&
                    retailerNavPaths[item]
                  ) {
                    navigate(retailerNavPaths[item]);
                  } else if (
                    role === "super_admin" &&
                    item === "Retailers"
                  ) {
                    navigate("/admin/retailers");
                  } else if (role === "super_admin" && item === "Users") {
                    navigate("/admin/users");
                  } else if (role === "super_admin" && item === "Customers") {
                    navigate("/admin/customers");
                  } else if (role === "super_admin" && item === "Products") {
                    navigate("/admin/products");
                  } else if (role === "super_admin" && item === "Invoices") {
                    navigate("/admin/invoices");
                  } else if (role === "super_admin" && item === "Payments") {
                    navigate("/admin/payments");
                  } else if (role === "super_admin" && item === "Returns & Refunds") {
                    navigate("/admin/returns");
                  } else if (
                    role === "customer" &&
                    item === "My Orders"
                  ) {
                    navigate("/customer/orders");
                  } else if (
                    role === "customer" &&
                    item === "My Payments"
                  ) {
                    navigate("/customer/payments");
                  } else if (
                    role === "customer" &&
                    item === "My Products"
                  ) {
                    navigate("/customer/products");
                  } else if (
                    role === "customer" &&
                    item === "My Returns"
                  ) {
                    navigate("/customer/returns");
                  } else if (
                    role === "customer" &&
                    item === "Transfer Bills"
                  ) {
                    navigate("/customer/transfers");
                  } else if (
                    role === "customer" &&
                    item === "Subscription"
                  ) {
                    navigate("/customer/subscription");
                  } else if (
                    role === "customer" &&
                    item === "Support"
                  ) {
                    navigate("/customer/support");
                  } else if (
                    role === "customer" &&
                    item === "Settings"
                  ) {
                    navigate("/customer/settings");
                  } else if (role === "super_admin" && item === "Warranty") {
                    navigate("/admin/warranty");
                  } else if (
                    role === "super_admin" &&
                    item === "Reports & Analytics"
                  ) {
                    navigate("/admin/reports");
                  } else if (
                    role === "super_admin" &&
                    item === "System Settings"
                  ) {
                    navigate("/admin/settings");
                  } else if (
                    role === "super_admin" &&
                    item === "Audit Logs"
                  ) {
                    navigate("/admin/audit-logs");
                  } else if (index === 0) {
                    navigate(
                      role === "super_admin"
                        ? "/admin"
                        : role === "retailer_owner"
                          ? "/retailer"
                          : "/customer"
                    );
                  }
                }}
              >
                <Icon size={16} />
                <span>{item}</span>
              </button>
            );
          })}
        </nav>

        <button
          className="nav-item logout"
          type="button"
          onClick={logout}
        >
          <LogOut size={16} />
          Logout
        </button>
      </aside>

      {mobileMenuOpen && (
        <div
          className="mobile-menu-overlay"
          onClick={closeMobileMenu}
          aria-hidden="true"
        />
      )}

      <aside
        className={`mobile-sidebar ${
          mobileMenuOpen ? "mobile-sidebar-open" : ""
        }`}
        aria-label="Mobile navigation"
      >
        <div className="mobile-sidebar-header">
          <div className="brand">
            <span className="brand-mark">✣</span> DigiBills
          </div>

          <button
            className="mobile-menu-close"
            type="button"
            aria-label="Close menu"
            onClick={closeMobileMenu}
          >
            ×
          </button>
        </div>

        <div className="mobile-profile-mini">
          <div className="avatar">{initials}</div>

          <div>
            <strong>{meta.label}</strong>
            <small>{user.email || user.phone_number}</small>
          </div>
        </div>

        <nav className="mobile-nav">
          {nav.map((item, index) => {
            const Icon = icons[index % icons.length];

            const isActive =
              (role === "super_admin" &&
                (
                  (item === "Overview" && location.pathname === "/admin") ||
                  (item === "Retailers" &&
                    location.pathname === "/admin/retailers") ||
                  (item === "Users" &&
                    location.pathname === "/admin/users") ||
                  (item === "Customers" &&
                    location.pathname === "/admin/customers") ||
                  (item === "Products" &&
                    location.pathname === "/admin/products") ||
                  (item === "Invoices" &&
                    location.pathname === "/admin/invoices") ||
                  (item === "Payments" &&
                    location.pathname === "/admin/payments") ||
                  (item === "Returns & Refunds" &&
                    location.pathname === "/admin/returns") ||
                  (item === "Warranty" &&
                    location.pathname === "/admin/warranty") ||
                  (item === "Reports & Analytics" &&
                    location.pathname === "/admin/reports") ||
                  (item === "System Settings" &&
                    location.pathname === "/admin/settings")
                )) ||
              (role === "retailer_owner" &&
                location.pathname === retailerNavPaths[item]) ||
              (role === "customer" &&
                (
                  (item === "Dashboard" &&
                    location.pathname === "/customer") ||
                  (item === "My Profile" &&
                    location.pathname === "/customer/profile") ||
                  (item === "My Invoices" &&
                    location.pathname.startsWith("/customer/invoices")) ||
                  (item === "My Payments" &&
                    location.pathname === "/customer/payments") ||
                  (item === "My Warranty" &&
                    location.pathname === "/customer/warranty") ||
                  (item === "Transfer Bills" &&
                    location.pathname === "/customer/transfers") ||
                  (item === "Subscription" &&
                    location.pathname === "/customer/subscription") ||
                  (item === "Support" &&
                    location.pathname === "/customer/support") ||
                  (item === "Settings" &&
                    location.pathname === "/customer/settings")
                ));

            return (
              <button
                key={item}
                className={`nav-item ${isActive ? "active" : ""}`}
                type="button"
                onClick={() => {
                  if (
                    role === "retailer_owner" &&
                    retailerNavPaths[item]
                  ) {
                    navigate(retailerNavPaths[item]);
                  } else if (
                    role === "super_admin" &&
                    item === "Retailers"
                  ) {
                    navigate("/admin/retailers");
                  } else if (role === "super_admin" && item === "Users") {
                    navigate("/admin/users");
                  } else if (
                    role === "super_admin" &&
                    item === "Customers"
                  ) {
                    navigate("/admin/customers");
                  } else if (
                    role === "super_admin" &&
                    item === "Products"
                  ) {
                    navigate("/admin/products");
                  } else if (
                    role === "super_admin" &&
                    item === "Invoices"
                  ) {
                    navigate("/admin/invoices");
                  } else if (
                    role === "super_admin" &&
                    item === "Payments"
                  ) {
                    navigate("/admin/payments");
                  } else if (
                    role === "super_admin" &&
                    item === "Returns & Refunds"
                  ) {
                    navigate("/admin/returns");
                  } else if (
                    role === "customer" &&
                    item === "My Warranty"
                  ) {
                    navigate("/customer/warranty");
                  } else if (
                    role === "customer" &&
                    item === "Transfer Bills"
                  ) {
                    navigate("/customer/transfers");
                  } else if (
                    role === "customer" &&
                    item === "Subscription"
                  ) {
                    navigate("/customer/subscription");
                  } else if (
                    role === "customer" &&
                    item === "Support"
                  ) {
                    navigate("/customer/support");
                  } else if (
                    role === "customer" &&
                    item === "Settings"
                  ) {
                    navigate("/customer/settings");
                  } else if (
                    role === "super_admin" &&
                    item === "Warranty"
                  ) {
                    navigate("/admin/warranty");
                  } else if (
                    role === "super_admin" &&
                    item === "Reports & Analytics"
                  ) {
                    navigate("/admin/reports");
                  } else if (
                    role === "super_admin" &&
                    item === "System Settings"
                  ) {
                    navigate("/admin/settings");
                  } else if (
                    role === "super_admin" &&
                    item === "Audit Logs"
                  ) {
                    navigate("/admin/audit-logs");
                  } else if (
                    role === "customer" &&
                    item === "My Profile"
                  ) {
                    navigate("/customer/profile");
                  } else if (
                    role === "customer" &&
                    item === "My Invoices"
                  ) {
                    navigate("/customer/invoices");
                  } else if (
                    role === "customer" &&
                    item === "My Payments"
                  ) {
                    navigate("/customer/payments");
                  } else if (index === 0) {
                    navigate(
                      role === "super_admin"
                        ? "/admin"
                        : role === "retailer_owner"
                          ? "/retailer"
                          : "/customer"
                    );
                  }

                  closeMobileMenu();
                }}
              >
                <Icon size={17} />
                <span>{item}</span>
              </button>
            );
          })}
        </nav>

        <button
          className="nav-item logout mobile-logout"
          type="button"
          onClick={logout}
        >
          <LogOut size={17} />
          <span>Logout</span>
        </button>
      </aside>

      <main className="main">
        {!(role === "customer" && location.pathname === "/customer") && (
          <header className="topbar">
            <button
              className="mobile-menu-button"
              type="button"
              aria-label="Open menu"
              onClick={() => setMobileMenuOpen(true)}
            >
              <Menu size={22} />
            </button>

            <div className="search-box">
              <Search size={16} />

              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={
                  role === "customer"
                    ? "Search invoices, orders..."
                    : "Search anything..."
                }
              />
            </div>

            <div className="top-actions">
              <button className="icon-button" type="button">
                <Bell size={18} />
                <span className="notification-dot">3</span>
              </button>

              <button className="icon-button" type="button">
                <CircleHelp size={18} />
              </button>

              <div className="top-avatar">{initials}</div>

              <ChevronDown size={16} />
            </div>
          </header>
        )}

        {children}

        {role === "customer" && (
          <nav
            className="customer-permanent-bottom-nav"
            aria-label="Customer navigation"
          >
            <button
              type="button"
              className={
                location.pathname === "/customer"
                  ? "active"
                  : ""
              }
              onClick={() => navigate("/customer")}
            >
              <Home size={20} />
              <span>Home</span>
            </button>

            <button
              type="button"
              className={
                location.pathname.startsWith("/customer/invoices")
                  ? "active"
                  : ""
              }
              onClick={() => navigate("/customer/invoices")}
            >
              <FileText size={20} />
              <span>Invoices</span>
            </button>

            <button
              type="button"
              className={
                location.pathname.startsWith("/customer/profile")
                  ? "active"
                  : ""
              }
              onClick={() => navigate("/customer/profile")}
            >
              <UserRound size={20} />
              <span>My Profile</span>
            </button>

            <button
              type="button"
              className={
                location.pathname.startsWith("/customer/warranty")
                  ? "active"
                  : ""
              }
              onClick={() => navigate("/customer/warranty")}
            >
              <ShieldCheck size={20} />
              <span>My Warranty</span>
            </button>

            <button
              type="button"
              className="more"
              onClick={() => setMobileMenuOpen(true)}
            >
              <MoreHorizontal size={21} />
              <span>More</span>
            </button>
          </nav>
        )}
      </main>
    </div>
  );
}

function getInitials(value: string): string {
  const parts = value
    .split(/[\s@._-]+/)
    .filter(Boolean);

  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }

  return value.slice(0, 2).toUpperCase();
}

export default App;




