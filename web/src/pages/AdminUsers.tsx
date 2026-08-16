import { useEffect, useMemo, useState } from "react";
import {
  Search,
  Users,
  ShieldCheck,
  UserRound,
  X,
  Plus,
  Trash2,
} from "lucide-react";
import { apiFetch } from "../api";

type User = {
  id: string;
  phone_number: string;
  email: string | null;
  status: string;
  is_phone_verified: boolean;
  roles: string[];
  last_login_at: string | null;
  created_at: string;
};

type Role = {
  id: string;
  name: string;
  description: string;
};

export default function AdminUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [selectedRole, setSelectedRole] = useState("");
  const [loading, setLoading] = useState(true);
  const [rolesLoading, setRolesLoading] = useState(true);
  const [savingRole, setSavingRole] = useState(false);
  const [error, setError] = useState("");
  const [roleError, setRoleError] = useState("");

  async function loadUsers() {
    try {
      setLoading(true);
      setError("");

      const data = await apiFetch<User[]>("/users");
      setUsers(data);

      if (selectedUser) {
        const refreshed = data.find(
          (user) => user.id === selectedUser.id
        );

        if (refreshed) {
          setSelectedUser(refreshed);
        }
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load users."
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadRoles() {
    try {
      setRolesLoading(true);

      const data = await apiFetch<Role[]>("/roles");
      setRoles(data);
    } catch (err) {
      setRoleError(
        err instanceof Error
          ? err.message
          : "Unable to load roles."
      );
    } finally {
      setRolesLoading(false);
    }
  }

  useEffect(() => {
    loadUsers();
    loadRoles();
  }, []);

  const filteredUsers = useMemo(() => {
    const normalizedQuery = query.toLowerCase().trim();

    return users.filter((user) => {
      const matchesSearch =
        !normalizedQuery ||
        user.phone_number
          .toLowerCase()
          .includes(normalizedQuery) ||
        (user.email || "")
          .toLowerCase()
          .includes(normalizedQuery) ||
        user.roles.some((role) =>
          role.toLowerCase().includes(normalizedQuery)
        );

      const matchesStatus =
        statusFilter === "all" ||
        user.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [users, query, statusFilter]);

  const counts = {
    all: users.length,
    active: users.filter(
      (user) => user.status === "active"
    ).length,
    inactive: users.filter(
      (user) => user.status === "inactive"
    ).length,
  };

  const availableRoles = roles.filter(
    (role) =>
      !selectedUser?.roles.includes(role.name)
  );

  function formatDate(value: string) {
    return new Date(value).toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  function formatRole(role: string) {
    return role
      .split("_")
      .map(
        (part) =>
          part.charAt(0).toUpperCase() +
          part.slice(1)
      )
      .join(" ");
  }

  function selectUser(user: User) {
    setSelectedUser(user);
    setSelectedRole("");
    setRoleError("");
  }

  function closeDetails() {
    if (savingRole) return;

    setSelectedUser(null);
    setSelectedRole("");
    setRoleError("");
  }

  async function addRole() {
    if (!selectedUser || !selectedRole) return;

    try {
      setSavingRole(true);
      setRoleError("");

      await apiFetch<User>(
        `/users/${selectedUser.id}/roles`,
        {
          method: "POST",
          body: JSON.stringify({
            role_name: selectedRole,
          }),
        }
      );

      setSelectedRole("");
      await loadUsers();
    } catch (err) {
      setRoleError(
        err instanceof Error
          ? err.message
          : "Unable to add role."
      );
    } finally {
      setSavingRole(false);
    }
  }

  async function removeRole(roleName: string) {
    if (!selectedUser) return;

    try {
      setSavingRole(true);
      setRoleError("");

      await apiFetch<User>(
        `/users/${selectedUser.id}/roles/${encodeURIComponent(
          roleName
        )}`,
        {
          method: "DELETE",
        }
      );

      await loadUsers();
    } catch (err) {
      setRoleError(
        err instanceof Error
          ? err.message
          : "Unable to remove role."
      );
    } finally {
      setSavingRole(false);
    }
  }

  return (
    <section className="dashboard admin-users-page">
      <div className="admin-users-header">
        <div>
          <h1>Users</h1>
          <p>
            Manage DigiBills platform users and
            their access.
          </p>
        </div>
      </div>

      <div className="user-stats-grid">
        <div className="stat-card">
          <div className="stat-icon blue">
            <Users />
          </div>

          <div>
            <span>Total Users</span>
            <strong>{counts.all}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">
            <ShieldCheck />
          </div>

          <div>
            <span>Active Users</span>
            <strong>{counts.active}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon purple">
            <UserRound />
          </div>

          <div>
            <span>Inactive Users</span>
            <strong>{counts.inactive}</strong>
          </div>
        </div>
      </div>

      <div className="users-panel">
        <div className="users-panel-header">
          <h3>User Directory</h3>

          <div className="retailer-filters">
            <div className="users-search">
              <Search size={15} />

              <input
                value={query}
                onChange={(event) =>
                  setQuery(event.target.value)
                }
                placeholder="Search users..."
              />
            </div>

            <select
              value={statusFilter}
              onChange={(event) =>
                setStatusFilter(
                  event.target.value
                )
              }
            >
              <option value="all">
                All Status
              </option>
              <option value="active">
                Active
              </option>
              <option value="inactive">
                Inactive
              </option>
            </select>
          </div>
        </div>

        {loading && (
          <div className="table-state">
            Loading users...
          </div>
        )}

        {error && (
          <div className="table-state negative">
            {error}
          </div>
        )}

        {!loading &&
          !error &&
          filteredUsers.length === 0 && (
            <div className="table-state">
              No users found.
            </div>
          )}

        {!loading &&
          !error &&
          filteredUsers.length > 0 && (
            <div className="users-table-wrap">
              <table className="users-table">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Phone</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Phone Verified</th>
                    <th>Last Login</th>
                    <th>Created</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredUsers.map((user) => (
                    <tr
                      key={user.id}
                      onClick={() =>
                        selectUser(user)
                      }
                      style={{
                        cursor: "pointer",
                      }}
                    >
                      <td>
                        <div className="user-cell">
                          <div className="user-table-avatar">
                            {user.roles.includes(
                              "super_admin"
                            )
                              ? "SA"
                              : user.roles.includes(
                                  "retailer_owner"
                                )
                              ? "RO"
                              : user.roles.includes(
                                  "customer"
                                )
                              ? "CU"
                              : "US"}
                          </div>

                          <div>
                            <strong>
                              {user.email ||
                                "No email"}
                            </strong>

                            <small>
                              {user.id}
                            </small>
                          </div>
                        </div>
                      </td>

                      <td>
                        {user.phone_number}
                      </td>

                      <td>
                        <div className="role-list">
                          {user.roles.length > 0
                            ? user.roles.map(
                                (role) => (
                                  <span
                                    className="role-badge"
                                    key={role}
                                  >
                                    {formatRole(
                                      role
                                    )}
                                  </span>
                                )
                              )
                            : (
                              <span className="action-muted">
                                No role
                              </span>
                            )}
                        </div>
                      </td>

                      <td>
                        <span
                          className={`status-badge ${user.status}`}
                        >
                          {user.status}
                        </span>
                      </td>

                      <td>
                        <span
                          className={
                            user.is_phone_verified
                              ? "verified"
                              : "not-verified"
                          }
                        >
                          {user.is_phone_verified
                            ? "Verified"
                            : "Not verified"}
                        </span>
                      </td>

                      <td>
                        {user.last_login_at
                          ? formatDate(
                              user.last_login_at
                            )
                          : "Never"}
                      </td>

                      <td>
                        {formatDate(
                          user.created_at
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </div>

      {selectedUser && (
        <div
          className="modal-backdrop"
          onClick={closeDetails}
        >
          <div
            className="user-details-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="modal-header">
              <div>
                <h2>User Details</h2>
                <p>
                  Manage this user's platform
                  access.
                </p>
              </div>

              <button
                className="icon-button"
                type="button"
                onClick={closeDetails}
                disabled={savingRole}
              >
                <X size={18} />
              </button>
            </div>

            <div className="users-modal-section">
              <div className="users-modal-section-title">
                <span>1.</span>
                <div>
                  <h3>User Information</h3>
                  <p>Contact and account verification details.</p>
                </div>
              </div>

              <div className="users-info-grid">
                <div className="users-info-card">
                  <span>Email</span>
                  <strong>
                    {selectedUser.email || "No email"}
                  </strong>
                </div>

                <div className="users-info-card">
                  <span>Phone</span>
                  <strong>{selectedUser.phone_number}</strong>
                </div>

                <div className="users-info-card">
                  <span>Status</span>
                  <strong>
                    <em className={`users-status ${selectedUser.status}`}>
                      {formatRole(selectedUser.status)}
                    </em>
                  </strong>
                </div>

                <div className="users-info-card">
                  <span>Phone Verification</span>
                  <strong>
                    <em
                      className={`users-status ${
                        selectedUser.is_phone_verified
                          ? "verified"
                          : "not-verified"
                      }`}
                    >
                      {selectedUser.is_phone_verified
                        ? "Verified"
                        : "Not verified"}
                    </em>
                  </strong>
                </div>
              </div>
            </div>

            <div className="users-modal-section users-roles-section">
              <div className="users-modal-section-title">
                <span>2.</span>
                <div>
                  <h3>Roles</h3>
                  <p>Roles control what this user can access.</p>
                </div>
              </div>

              <div className="users-current-roles">
                {selectedUser.roles.length === 0 ? (
                  <div className="users-empty-role">
                    No roles assigned.
                  </div>
                ) : (
                  selectedUser.roles.map((role) => (
                    <div
                      className="users-role-card"
                      key={role}
                    >
                      <div className="users-role-name">
                        <span className="users-role-icon">
                          <UserRound size={16} />
                        </span>
                        <strong>{formatRole(role)}</strong>
                      </div>

                      <button
                        type="button"
                        className="users-remove-button"
                        disabled={savingRole}
                        onClick={() => removeRole(role)}
                      >
                        <Trash2 size={14} />
                        Remove
                      </button>
                    </div>
                  ))
                )}
              </div>

              <div className="users-add-role">
                <div className="users-add-role-heading">
                  <strong>Add New Role</strong>
                  <span>Assign another access role to this user.</span>
                </div>

                <div className="users-add-role-controls">
                  <select
                    value={selectedRole}
                    onChange={(event) =>
                      setSelectedRole(event.target.value)
                    }
                    disabled={rolesLoading || savingRole}
                  >
                    <option value="">
                      {rolesLoading
                        ? "Loading roles..."
                        : "Select a role"}
                    </option>

                    {availableRoles.map((role) => (
                      <option
                        value={role.name}
                        key={role.id}
                      >
                        {formatRole(role.name)}
                      </option>
                    ))}
                  </select>

                  <button
                    type="button"
                    className="users-add-role-button"
                    disabled={
                      !selectedRole ||
                      savingRole ||
                      rolesLoading
                    }
                    onClick={addRole}
                  >
                    <Plus size={15} />
                    {savingRole ? "Saving..." : "Add Role"}
                  </button>
                </div>

                {roleError && (
                  <div className="users-role-error">
                    {roleError}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
