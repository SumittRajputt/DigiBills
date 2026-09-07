import {
  Search,
  Users,
  CheckCircle,
  XCircle,
  UserPlus,
  RefreshCw,
  X,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { apiFetch } from "../api";

type Employee = {
  id: string;
  employee_id: string;
  user_id: string;
  retailer_id: string;
  name: string;
  phone_number: string;
  email: string | null;
  employee_type: string;
  status: string;
  created_at: string;
};

const ROLE_LABELS: Record<string, string> = {
  retailer_manager: "Retailer Manager",
  cashier: "Cashier",
  inventory_manager: "Inventory Manager",
  salesman: "Salesman",
};

export default function RetailerEmployees() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("all");
  const [status, setStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);

  async function loadEmployees() {
    try {
      setLoading(true);
      setError("");

      const result = await apiFetch<Employee[]>("/employees");
      setEmployees(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load employees."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadEmployees();
  }, []);

  const filteredEmployees = useMemo(() => {
    const query = search.toLowerCase().trim();

    return employees.filter((employee) => {
      const matchesSearch =
        !query ||
        employee.name.toLowerCase().includes(query) ||
        employee.employee_id.toLowerCase().includes(query) ||
        employee.phone_number.includes(query) ||
        (employee.email || "").toLowerCase().includes(query);

      const matchesRole =
        role === "all" ||
        employee.employee_type === role;

      const matchesStatus =
        status === "all" ||
        employee.status.toLowerCase() === status;

      return matchesSearch && matchesRole && matchesStatus;
    });
  }, [employees, search, role, status]);

  const activeCount = employees.filter(
    (employee) => employee.status.toLowerCase() === "active"
  ).length;

  const inactiveCount = employees.filter(
    (employee) => employee.status.toLowerCase() === "inactive"
  ).length;

  function formatDate(value: string) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "—";
    }

    return date.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  async function handleEmployeeCreated() {
    setShowAddModal(false);
    await loadEmployees();
  }

  return (
    <section className="dashboard retailer-employees-page">
      <div className="retailer-employees-header">
        <div>
          <div className="page-eyebrow">
            <span>RETAILER MANAGEMENT</span>
          </div>

          <h1>Employees</h1>

          <p>
            Manage the employees who help operate your
            DigiBills retailer account.
          </p>
        </div>

        <div className="retailer-employees-header-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={loadEmployees}
            disabled={loading}
          >
            <RefreshCw size={14} />
            Refresh
          </button>

          <button
            type="button"
            className="primary-button"
            onClick={() => setShowAddModal(true)}
          >
            <UserPlus size={15} />
            Add Employee
          </button>
        </div>
      </div>

      <div className="employee-stats-grid">
        <MiniEmployeeStat
          icon={<Users />}
          title="Total Employees"
          value={employees.length}
          tone="blue"
        />

        <MiniEmployeeStat
          icon={<CheckCircle />}
          title="Active"
          value={activeCount}
          tone="green"
        />

        <MiniEmployeeStat
          icon={<XCircle />}
          title="Inactive"
          value={inactiveCount}
          tone="red"
        />
      </div>

      <div className="employees-panel">
        <div className="employees-panel-header">
          <div>
            <h3>All Employees</h3>

            <span>
              {filteredEmployees.length} of{" "}
              {employees.length} employees
            </span>
          </div>

          <div className="employees-toolbar">
            <div className="employees-search">
              <Search size={16} />

              <input
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search employees..."
              />
            </div>

            <select
              value={role}
              onChange={(event) =>
                setRole(event.target.value)
              }
            >
              <option value="all">All Roles</option>
              <option value="retailer_manager">
                Retailer Manager
              </option>
              <option value="cashier">Cashier</option>
              <option value="inventory_manager">
                Inventory Manager
              </option>
              <option value="salesman">Salesman</option>
            </select>

            <select
              value={status}
              onChange={(event) =>
                setStatus(event.target.value)
              }
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </div>

        {loading && (
          <div className="table-state">
            Loading employees...
          </div>
        )}

        {!loading && error && (
          <div className="table-state negative">
            {error}
          </div>
        )}

        {!loading &&
          !error &&
          filteredEmployees.length === 0 && (
            <div className="table-state">
              No employees found.
            </div>
          )}

        {!loading &&
          !error &&
          filteredEmployees.length > 0 && (
            <div className="employees-table-wrap">
              <table className="employees-table">
                <thead>
                  <tr>
                    <th>Employee</th>
                    <th>Employee ID</th>
                    <th>Contact</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Joined</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredEmployees.map((employee) => (
                    <tr key={employee.id}>
                      <td>
                        <div className="employee-name-cell">
                          <div className="employee-avatar">
                            {employee.name
                              .charAt(0)
                              .toUpperCase()}
                          </div>

                          <div>
                            <strong>{employee.name}</strong>
                          </div>
                        </div>
                      </td>

                      <td>
                        <span className="employee-id">
                          {employee.employee_id}
                        </span>
                      </td>

                      <td>
                        <div className="employee-contact">
                          <span>{employee.phone_number}</span>
                          {employee.email && (
                            <small>{employee.email}</small>
                          )}
                        </div>
                      </td>

                      <td>
                        <span className="employee-role-badge">
                          {ROLE_LABELS[
                            employee.employee_type
                          ] || employee.employee_type}
                        </span>
                      </td>

                      <td>
                        <span
                          className={`employee-status-badge ${
                            employee.status.toLowerCase()
                          }`}
                        >
                          <span />
                          {employee.status}
                        </span>
                      </td>

                      <td>{formatDate(employee.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </div>

      {showAddModal && (
        <AddEmployeeModal
          onClose={() => setShowAddModal(false)}
          onCreated={handleEmployeeCreated}
        />
      )}
    </section>
  );
}

function AddEmployeeModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [employeeType, setEmployeeType] =
    useState("cashier");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");
    setSubmitting(true);

    try {
      await apiFetch<Employee>("/employees", {
        method: "POST",
        body: JSON.stringify({
          name: name.trim(),
          phone_number: phoneNumber.trim(),
          email: email.trim() || null,
          password,
          employee_type: employeeType,
        }),
      });

      await onCreated();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to create employee."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="employee-modal-backdrop">
      <div className="employee-modal">
        <div className="employee-modal-header">
          <div>
            <span className="page-eyebrow">
              EMPLOYEE MANAGEMENT
            </span>
            <h2>Add Employee</h2>
            <p>
              Create a new employee account for your
              retailer.
            </p>
          </div>

          <button
            type="button"
            className="employee-modal-close"
            onClick={onClose}
            disabled={submitting}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        <form
          className="employee-form"
          onSubmit={handleSubmit}
        >
          <div className="employee-form-grid">
            <label>
              Employee name
              <input
                type="text"
                value={name}
                onChange={(event) =>
                  setName(event.target.value)
                }
                placeholder="Enter full name"
                required
              />
            </label>

            <label>
              Phone number
              <input
                type="tel"
                value={phoneNumber}
                onChange={(event) =>
                  setPhoneNumber(event.target.value)
                }
                placeholder="Enter phone number"
                required
              />
            </label>

            <label>
              Email
              <span className="optional-label">
                Optional
              </span>
              <input
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="employee@example.com"
              />
            </label>

            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                placeholder="Minimum 8 characters"
                minLength={8}
                required
              />
            </label>

            <label className="employee-form-full">
              Employee role
              <select
                value={employeeType}
                onChange={(event) =>
                  setEmployeeType(event.target.value)
                }
                required
              >
                <option value="cashier">Cashier</option>
                <option value="retailer_manager">
                  Retailer Manager
                </option>
                <option value="inventory_manager">
                  Inventory Manager
                </option>
                <option value="salesman">Salesman</option>
              </select>
            </label>
          </div>

          {error && (
            <div className="login-error employee-form-error">
              {error}
            </div>
          )}

          <div className="employee-form-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={onClose}
              disabled={submitting}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="primary-button"
              disabled={submitting}
            >
              {submitting
                ? "Creating..."
                : "Create Employee"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function MiniEmployeeStat({
  icon,
  title,
  value,
  tone,
}: {
  icon: React.ReactNode;
  title: string;
  value: number;
  tone: "blue" | "green" | "red";
}) {
  return (
    <div className="employee-stat-card">
      <div className={`employee-stat-icon ${tone}`}>
        {icon}
      </div>

      <div>
        <span>{title}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}
