import { useEffect, useState } from "react";
import { apiFetch } from "../api";

type User = {
  id: string;
  phone_number: string;
  email?: string | null;
  status: string;
  is_phone_verified: boolean;
  roles: string[];
};

export default function CashierDashboard() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    apiFetch<User>("/auth/me")
      .then(setUser)
      .catch(() => {
        setUser(null);
      });
  }, []);

  return (
    <section className="dashboard">
      <div className="page-heading">
        <span className="page-eyebrow">EMPLOYEE WORKSPACE</span>
        <h1>Cashier Dashboard</h1>
        <p>
          Welcome back{user?.phone_number ? ` · ${user.phone_number}` : ""}.
          Manage your assigned cashier activities from here.
        </p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-label">TODAY'S SALES</span>
          <strong>₹0</strong>
          <span className="stat-meta">Today's cashier sales</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">INVOICES</span>
          <strong>0</strong>
          <span className="stat-meta">Invoices handled today</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">PAYMENTS</span>
          <strong>0</strong>
          <span className="stat-meta">Payments collected today</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">CUSTOMERS</span>
          <strong>0</strong>
          <span className="stat-meta">Customers served today</span>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <div>
            <h3>Cashier Workspace</h3>
            <span>Your assigned cashier operations will appear here.</span>
          </div>
        </div>

        <div
          style={{
            padding: "32px 20px",
            color: "#7d8998",
            fontSize: "13px",
          }}
        >
          Cashier dashboard is ready for implementation.
        </div>
      </div>
    </section>
  );
}
