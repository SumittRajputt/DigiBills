import { useEffect, useState } from "react";
import { apiFetch } from "../api";
import { Eye, Plus, X } from "lucide-react";

type SupportTicket = {
  id: string;
  ticket_id: string;
  customer_id: string;
  subject: string;
  description: string;
  status: string;
  priority: string;
  category: string | null;
  resolution: string | null;
  created_at: string;
  updated_at: string;
};

type CreateTicketForm = {
  subject: string;
  description: string;
  priority: string;
  category: string;
};

function formatDate(value: string) {
  if (!value) return "—";

  return new Date(value).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function statusClass(value: string) {
  return `customer-support-status customer-support-status-${value
    .toLowerCase()
    .replace(/\s+/g, "-")}`;
}

function priorityClass(value: string) {
  return `customer-support-priority customer-support-priority-${value
    .toLowerCase()
    .replace(/\s+/g, "-")}`;
}

export default function CustomerSupport() {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [selectedTicket, setSelectedTicket] =
    useState<SupportTicket | null>(null);

  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState<CreateTicketForm>({
    subject: "",
    description: "",
    priority: "normal",
    category: "General",
  });

  async function loadTickets() {
    try {
      setLoading(true);
      setError("");

      const data = await apiFetch<SupportTicket[]>(
        "/customer/support"
      );

      setTickets(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load support tickets."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTickets();
  }, []);

  async function createTicket() {
    if (!form.subject.trim() || !form.description.trim()) {
      setError("Subject and description are required.");
      return;
    }

    try {
      setSubmitting(true);
      setError("");

      const data = await apiFetch<SupportTicket>(
        "/customer/support",
        {
          method: "POST",
          body: JSON.stringify({
            subject: form.subject.trim(),
            description: form.description.trim(),
            priority: form.priority,
            category: form.category.trim() || null,
          }),
        }
      );

      setTickets((current) => [data, ...current]);

      setForm({
        subject: "",
        description: "",
        priority: "normal",
        category: "General",
      });

      setShowCreate(false);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to create support ticket."
      );
    } finally {
      setSubmitting(false);
    }
  }

  const openTickets = tickets.filter(
    (ticket) => ticket.status === "open"
  ).length;

  const resolvedTickets = tickets.filter(
    (ticket) =>
      ticket.status === "resolved" ||
      ticket.status === "closed"
  ).length;

  return (
    <section className="dashboard customer-dashboard-page customer-support-page">
      <div className="page-heading customer-support-heading">
        <div>
          <h1>Support</h1>
          <p>
            Create and track your support requests.
          </p>
        </div>

        <button
          type="button"
          className="primary-button"
          onClick={() => {
            setError("");
            setShowCreate(true);
          }}
        >
          <Plus size={17} />
          Create Support Ticket
        </button>
      </div>

      {error && (
        <div className="customer-support-error">
          {error}
        </div>
      )}

      <div className="stats-grid three">
        <div className="stat-card">
          <div>
            <span>Total Tickets</span>
            <strong>{tickets.length}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div>
            <span>Open Tickets</span>
            <strong>{openTickets}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div>
            <span>Resolved</span>
            <strong>{resolvedTickets}</strong>
          </div>
        </div>
      </div>

      <div className="panel customer-support-panel">
        <div className="panel-header">
          <div>
            <h3>Support Tickets</h3>
            <span>
              Your support requests and their current status
            </span>
          </div>
        </div>

        {loading ? (
          <div className="table-state">
            Loading support tickets...
          </div>
        ) : tickets.length === 0 ? (
          <div className="table-state">
            No support tickets found.
          </div>
        ) : (
          <div className="customer-support-table-wrap">
            <table className="data-table customer-support-table">
              <thead>
                <tr>
                  <th>Ticket ID</th>
                  <th>Subject</th>
                  <th>Category</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {tickets.map((ticket) => (
                  <tr key={ticket.id}>
                    <td>
                      <strong>{ticket.ticket_id}</strong>
                    </td>

                    <td>{ticket.subject}</td>

                    <td>
                      {ticket.category || "General"}
                    </td>

                    <td>
                      <span
                        className={priorityClass(
                          ticket.priority
                        )}
                      >
                        {ticket.priority}
                      </span>
                    </td>

                    <td>
                      <span
                        className={statusClass(
                          ticket.status
                        )}
                      >
                        {ticket.status}
                      </span>
                    </td>

                    <td>
                      {formatDate(ticket.created_at)}
                    </td>

                    <td>
                      <button
                        type="button"
                        className="icon-button"
                        title="View ticket"
                        onClick={() =>
                          setSelectedTicket(ticket)
                        }
                      >
                        <Eye size={17} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedTicket && (
        <div
          className="customer-support-modal-backdrop"
          onClick={() => setSelectedTicket(null)}
        >
          <div
            className="customer-support-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="customer-support-modal-header">
              <div>
                <span>SUPPORT TICKET</span>
                <h2>{selectedTicket.ticket_id}</h2>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() =>
                  setSelectedTicket(null)
                }
                aria-label="Close"
              >
                <X size={20} />
              </button>
            </div>

            <div className="customer-support-detail-grid">
              <div>
                <small>Subject</small>
                <strong>
                  {selectedTicket.subject}
                </strong>
              </div>

              <div>
                <small>Category</small>
                <strong>
                  {selectedTicket.category || "General"}
                </strong>
              </div>

              <div>
                <small>Priority</small>
                <strong>
                  {selectedTicket.priority}
                </strong>
              </div>

              <div>
                <small>Status</small>
                <strong>
                  {selectedTicket.status}
                </strong>
              </div>

              <div>
                <small>Created</small>
                <strong>
                  {formatDate(
                    selectedTicket.created_at
                  )}
                </strong>
              </div>

              <div>
                <small>Updated</small>
                <strong>
                  {formatDate(
                    selectedTicket.updated_at
                  )}
                </strong>
              </div>

              <div className="customer-support-detail-full">
                <small>Description</small>
                <strong>
                  {selectedTicket.description}
                </strong>
              </div>

              {selectedTicket.resolution && (
                <div className="customer-support-detail-full">
                  <small>Resolution</small>
                  <strong>
                    {selectedTicket.resolution}
                  </strong>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {showCreate && (
        <div
          className="customer-support-modal-backdrop"
          onClick={() => setShowCreate(false)}
        >
          <div
            className="customer-support-modal customer-support-create-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="customer-support-modal-header">
              <div>
                <span>SUPPORT</span>
                <h2>Create Support Ticket</h2>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() =>
                  setShowCreate(false)
                }
                aria-label="Close"
              >
                <X size={20} />
              </button>
            </div>

            <div className="customer-support-form">
              <label>
                Subject
                <input
                  value={form.subject}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      subject: event.target.value,
                    })
                  }
                  placeholder="What do you need help with?"
                />
              </label>

              <label>
                Category
                <input
                  value={form.category}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      category: event.target.value,
                    })
                  }
                  placeholder="General"
                />
              </label>

              <label>
                Priority
                <select
                  value={form.priority}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      priority: event.target.value,
                    })
                  }
                >
                  <option value="low">Low</option>
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </label>

              <label>
                Description
                <textarea
                  value={form.description}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      description:
                        event.target.value,
                    })
                  }
                  placeholder="Describe your issue..."
                  rows={5}
                />
              </label>

              <div className="customer-support-form-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() =>
                    setShowCreate(false)
                  }
                  disabled={submitting}
                >
                  Cancel
                </button>

                <button
                  type="button"
                  className="primary-button"
                  onClick={createTicket}
                  disabled={submitting}
                >
                  {submitting
                    ? "Submitting..."
                    : "Submit Ticket"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
