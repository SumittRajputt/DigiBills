import { useState } from "react";
import {
  Building2,
  FileText,
  CreditCard,
  Users,
  Bell,
  ShieldCheck,
  Save,
} from "lucide-react";

type SettingsSection =
  | "business"
  | "invoice"
  | "billing"
  | "users"
  | "notifications"
  | "security";

export default function AdminSettings() {
  const [activeSection, setActiveSection] =
    useState<SettingsSection>("business");

  const [businessName, setBusinessName] = useState("DigiBills");
  const [email, setEmail] = useState("support@digibills.com");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");

  const sections = [
    {
      id: "business" as const,
      label: "Business",
      description: "Business profile and contact details",
      icon: Building2,
    },
    {
      id: "invoice" as const,
      label: "Invoices",
      description: "Invoice numbering and billing defaults",
      icon: FileText,
    },
    {
      id: "billing" as const,
      label: "Subscriptions & Billing",
      description: "Plans, pricing and billing behaviour",
      icon: CreditCard,
    },
    {
      id: "users" as const,
      label: "Users & Roles",
      description: "Roles and access control",
      icon: Users,
    },
    {
      id: "notifications" as const,
      label: "Notifications",
      description: "System notification preferences",
      icon: Bell,
    },
    {
      id: "security" as const,
      label: "Security",
      description: "Security and account controls",
      icon: ShieldCheck,
    },
  ];

  function saveSettings() {
    // Frontend-only for now.
    // We will connect this to the backend after the UI is finalized.
    alert("Settings saved locally for this session.");
  }

  return (
    <div className="settings-page">
      <div className="page-heading">
        <div>
          <h1>System Settings</h1>
          <p>
            Manage DigiBills configuration, billing, users and security.
          </p>
        </div>

        <button
          type="button"
          className="primary-button"
          onClick={saveSettings}
        >
          <Save size={16} />
          Save changes
        </button>
      </div>

      <div className="settings-layout">
        <aside className="settings-menu">
          {sections.map((section) => {
            const Icon = section.icon;

            return (
              <button
                key={section.id}
                type="button"
                className={`settings-menu-item ${
                  activeSection === section.id ? "active" : ""
                }`}
                onClick={() => setActiveSection(section.id)}
              >
                <Icon size={18} />

                <span>
                  <strong>{section.label}</strong>
                  <small>{section.description}</small>
                </span>
              </button>
            );
          })}
        </aside>

        <section className="settings-card">
          {activeSection === "business" && (
            <>
              <div className="settings-section-header">
                <h2>Business Information</h2>
                <p>
                  Configure the basic information displayed throughout
                  DigiBills.
                </p>
              </div>

              <div className="settings-form-grid">
                <label>
                  Business name
                  <input
                    value={businessName}
                    onChange={(event) =>
                      setBusinessName(event.target.value)
                    }
                  />
                </label>

                <label>
                  Support email
                  <input
                    type="email"
                    value={email}
                    onChange={(event) =>
                      setEmail(event.target.value)
                    }
                  />
                </label>

                <label>
                  Support phone
                  <input
                    value={phone}
                    onChange={(event) =>
                      setPhone(event.target.value)
                    }
                    placeholder="Enter support phone"
                  />
                </label>

                <label className="full-width">
                  Business address
                  <textarea
                    value={address}
                    onChange={(event) =>
                      setAddress(event.target.value)
                    }
                    placeholder="Enter business address"
                    rows={4}
                  />
                </label>
              </div>
            </>
          )}

          {activeSection === "invoice" && (
            <>
              <div className="settings-section-header">
                <h2>Invoice Settings</h2>
                <p>
                  Configure how invoices are generated and presented.
                </p>
              </div>

              <div className="settings-form-grid">
                <label>
                  Invoice prefix
                  <input defaultValue="INV-" />
                </label>

                <label>
                  Default payment terms
                  <select defaultValue="Due immediately">
                    <option>Due immediately</option>
                    <option>7 days</option>
                    <option>15 days</option>
                    <option>30 days</option>
                  </select>
                </label>

                <label>
                  Currency
                  <select defaultValue="INR">
                    <option>INR</option>
                    <option>USD</option>
                    <option>EUR</option>
                  </select>
                </label>

                <label>
                  Default tax rate
                  <input type="number" defaultValue="0" min="0" />
                </label>
              </div>
            </>
          )}

          {activeSection === "billing" && (
            <>
              <div className="settings-section-header">
                <h2>Subscriptions & Billing</h2>
                <p>
                  Manage subscription behaviour and billing configuration.
                </p>
              </div>

              <div className="settings-info-grid">
                <div>
                  <strong>Subscription plans</strong>
                  <span>
                    Manage customer and retailer subscription plans.
                  </span>
                </div>

                <div>
                  <strong>Trial periods</strong>
                  <span>
                    Configure trial duration for eligible plans.
                  </span>
                </div>

                <div>
                  <strong>Automatic renewal</strong>
                  <span>
                    Control recurring subscription renewal behaviour.
                  </span>
                </div>

                <div>
                  <strong>Per-bill pricing</strong>
                  <span>
                    Configure usage-based billing rules.
                  </span>
                </div>
              </div>
            </>
          )}

          {activeSection === "users" && (
            <>
              <div className="settings-section-header">
                <h2>Users & Roles</h2>
                <p>
                  Control administrative access and role permissions.
                </p>
              </div>

              <div className="settings-info-grid">
                <div>
                  <strong>Super Admin</strong>
                  <span>Full access to DigiBills administration.</span>
                </div>

                <div>
                  <strong>Retailer Owner</strong>
                  <span>Access to retailer operations and billing.</span>
                </div>

                <div>
                  <strong>Customer</strong>
                  <span>Access to customer invoices and services.</span>
                </div>
              </div>
            </>
          )}

          {activeSection === "notifications" && (
            <>
              <div className="settings-section-header">
                <h2>Notifications</h2>
                <p>
                  Configure important system and billing notifications.
                </p>
              </div>

              <div className="settings-toggle-list">
                <label>
                  <span>
                    <strong>Payment notifications</strong>
                    <small>
                      Notify users when payments are completed.
                    </small>
                  </span>
                  <input type="checkbox" defaultChecked />
                </label>

                <label>
                  <span>
                    <strong>Invoice notifications</strong>
                    <small>
                      Notify customers when invoices are generated.
                    </small>
                  </span>
                  <input type="checkbox" defaultChecked />
                </label>

                <label>
                  <span>
                    <strong>Subscription notifications</strong>
                    <small>
                      Notify users about renewal and expiry events.
                    </small>
                  </span>
                  <input type="checkbox" defaultChecked />
                </label>
              </div>
            </>
          )}

          {activeSection === "security" && (
            <>
              <div className="settings-section-header">
                <h2>Security</h2>
                <p>
                  Manage application-level security controls.
                </p>
              </div>

              <div className="settings-info-grid">
                <div>
                  <strong>Authentication</strong>
                  <span>
                    DigiBills uses authenticated API access.
                  </span>
                </div>

                <div>
                  <strong>Role-based access</strong>
                  <span>
                    Access is restricted according to assigned roles.
                  </span>
                </div>

                <div>
                  <strong>Audit logging</strong>
                  <span>
                    Administrative actions are recorded in audit logs.
                  </span>
                </div>
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
