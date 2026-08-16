import { FormEvent, useEffect, useState } from "react";
import {
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import {
  Bell,
  ChevronDown,
  CircleHelp,
  LayoutDashboard,
  LogOut,
  Search,
  ShieldCheck,
  Store,
  UserRound,
} from "lucide-react";

import AdminDashboard from "./dashboards/AdminDashboard";
import AdminAuditLogs from "./pages/AdminAuditLogs";
import RetailerDashboard from "./dashboards/RetailerDashboard";
import CustomerDashboard from "./dashboards/CustomerDashboard";
import AdminRetailers from "./pages/AdminRetailers";
import AdminUsers from "./pages/AdminUsers";
import AdminCustomers from "./pages/AdminCustomers";
import AdminProducts from "./pages/AdminProducts";
import AdminInvoices from "./pages/AdminInvoices";
import AdminPayments from "./pages/AdminPayments";
import AdminWarranty from "./pages/AdminWarranty";
import AdminReports from "./pages/AdminReports";
import AdminReturns from "./pages/AdminReturns";
import { apiFetch } from "./api";

type Role = "super_admin" | "retailer_owner" | "customer";

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
};

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("digibills_token");

    if (!token) {
      setLoading(false);
      return;
    }

    apiFetch<User>("/auth/me")
      .then((currentUser) => {
        setUser(currentUser);
      })
      .catch(() => {
        localStorage.removeItem("digibills_token");
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
        path="/login"
        element={
          user ? (
            <NavigateToRole user={user} />
          ) : (
            <LoginPage onLogin={setUser} />
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
              <RetailerDashboard />
            </DashboardFrame>
          </ProtectedRoute>
        }
      />

      <Route
        path="/customer/*"
        element={
          <ProtectedRoute user={user} role="customer">
            <DashboardFrame role="customer" user={user!}>
              <CustomerDashboard />
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

function LoginPage({ onLogin }: { onLogin: (user: User) => void }) {
  const navigate = useNavigate();

  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

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
          phone_number: phoneNumber,
          password,
        }),
      });

      localStorage.setItem(
        "digibills_token",
        tokenResponse.access_token
      );

      const user = await apiFetch<User>("/auth/me");

      onLogin(user);
      navigate(getRolePath(user), { replace: true });
    } catch {
      localStorage.removeItem("digibills_token");
      setError("Invalid phone number or password.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="brand large">
          <span className="brand-mark">✣</span> DigiBills
        </div>

        <h1>Welcome back</h1>
        <p>Sign in to continue to your DigiBills account.</p>

        <form onSubmit={handleSubmit}>
          <label>
            Phone number
            <input
              type="tel"
              value={phoneNumber}
              onChange={(event) => setPhoneNumber(event.target.value)}
              placeholder="Enter phone number"
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter password"
              required
            />
          </label>

          {error && <div className="login-error">{error}</div>}

          <button
            className="login-button"
            type="submit"
            disabled={submitting}
          >
            {submitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
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
      "Purchases",
      "Returns",
      "Suppliers",
      "Warranty",
      "Reports",
      "Settings",
    ],
    customer: [
      "Dashboard",
      "My Profile",
      "My Invoices",
      "My Payments",
      "My Orders",
      "My Returns",
      "My Warranty",
      "My Products",
      "Transfers",
      "Support",
      "Settings",
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
    localStorage.removeItem("digibills_token");
    navigate("/login", { replace: true });
  }

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
                      (item === "Reports & Analytics" && location.pathname === "/admin/reports")
                    )) ||
                  (role !== "super_admin" &&
                    index === 0 &&
                    location.pathname === `/${role === "retailer_owner" ? "retailer" : "customer"}`)
                    ? "active"
                    : ""
                }`}
                type="button"
                onClick={() => {
                  if (role === "super_admin" && item === "Retailers") {
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
                  } else if (role === "super_admin" && item === "Warranty") {
                    navigate("/admin/warranty");
                  } else if (
                    role === "super_admin" &&
                    item === "Reports & Analytics"
                  ) {
                    navigate("/admin/reports");
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

      <main className="main">
        <header className="topbar">
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

        {children}
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
