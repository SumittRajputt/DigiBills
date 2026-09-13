import { useEffect, useState } from "react";
import {
  ArrowLeft,
  Bell,
  CheckCircle2,
  FileText,
  Clock3,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { apiFetch } from "../api";

type CustomerNotification = {
  id: string;
  title: string;
  message: string;
  notification_type: string;
  reference_type?: string | null;
  reference_id?: string | null;
  is_read: boolean;
  created_at: string;
};

export default function CustomerNotificationDetails() {
  const navigate = useNavigate();
  const { notificationId } = useParams();

  const [notification, setNotification] =
    useState<CustomerNotification | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadNotification();
  }, [notificationId]);

  async function loadNotification() {
    if (!notificationId) {
      setError("Notification not found.");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError("");

      const payload = await apiFetch<CustomerNotification[]>(
        "/customer/notifications"
      );

      const found = Array.isArray(payload)
        ? payload.find(
            (item) => String(item.id) === String(notificationId)
          )
        : null;

      if (!found) {
        setError("Notification not found.");
        return;
      }

      setNotification(found);

      if (!found.is_read) {
        try {
          await apiFetch<CustomerNotification>(
            `/customer/notifications/${found.id}/read`,
            {
              method: "PATCH",
            }
          );

          setNotification({
            ...found,
            is_read: true,
          });
        } catch (readError) {
          console.error(
            "Failed to mark notification as read:",
            readError
          );
        }
      }
    } catch (err: any) {
      console.error(
        "Failed to load notification:",
        err
      );

      setError(
        err?.response?.data?.detail ||
          "Unable to load notification right now."
      );
    } finally {
      setLoading(false);
    }
  }

  function formatDate(value: string) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "—";
    }

    return date.toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function formatType(value: string) {
    return value
      .replace(/[_-]+/g, " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function handleRelatedAction() {
    if (
      notification?.reference_type === "invoice" &&
      notification.reference_id
    ) {
      navigate(
        `/customer/invoices/${encodeURIComponent(
          notification.reference_id
        )}`
      );
    }
  }

  if (loading) {
    return (
      <section className="dashboard customer-dashboard-page customer-notification-details-page">
        <div className="table-state">
          Loading notification...
        </div>
      </section>
    );
  }

  if (error || !notification) {
    return (
      <section className="dashboard customer-dashboard-page customer-notification-details-page">
        <div className="customer-notification-details-error">
          <Bell size={24} />
          <strong>
            {error || "Notification not found."}
          </strong>

          <button
            type="button"
            className="secondary-button"
            onClick={() =>
              navigate("/customer/notifications")
            }
          >
            Back to Notifications
          </button>
        </div>
      </section>
    );
  }

  const hasInvoiceReference =
    notification.reference_type === "invoice" &&
    Boolean(notification.reference_id);

  return (
    <section className="dashboard customer-dashboard-page customer-notification-details-page">
      <div className="page-heading customer-notification-details-heading">
        <div>
          <h1>Notification Details</h1>
          <p>
            View the complete information for this notification.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={() =>
            navigate("/customer/notifications")
          }
        >
          <ArrowLeft size={16} />
          Back to Notifications
        </button>
      </div>

      <div className="customer-notification-details-layout">
        <div className="panel customer-notification-details-card">
          <div className="customer-notification-details-hero">
            <div className="customer-notification-details-icon">
              <Bell size={24} />
            </div>

            <div className="customer-notification-details-title">
              <span>
                {formatType(notification.notification_type)}
              </span>
              <h2>
                {notification.title || "Notification"}
              </h2>
            </div>

            <div className="customer-notification-read-badge">
              <CheckCircle2 size={14} />
              Read
            </div>
          </div>

          <div className="customer-notification-details-message">
            <span>MESSAGE</span>
            <p>{notification.message}</p>
          </div>

          <div className="customer-notification-details-meta">
            <div>
              <div className="customer-notification-details-meta-icon">
                <Clock3 size={17} />
              </div>

              <div>
                <span>Date & Time</span>
                <strong>
                  {formatDate(notification.created_at)}
                </strong>
              </div>
            </div>

            <div>
              <div className="customer-notification-details-meta-icon">
                <Bell size={17} />
              </div>

              <div>
                <span>Notification Type</span>
                <strong>
                  {formatType(notification.notification_type)}
                </strong>
              </div>
            </div>
          </div>
        </div>

        {hasInvoiceReference && (
          <div className="panel customer-notification-related-panel">
            <div className="panel-header">
              <div>
                <h3>
                  <FileText size={18} />
                  Related Purchase
                </h3>

                <span>
                  This notification is linked to an invoice.
                </span>
              </div>
            </div>

            <div className="customer-notification-related-content">
              <div>
                <span>Invoice Reference</span>
                <strong>
                  {notification.reference_id}
                </strong>
              </div>

              <button
                type="button"
                className="primary-button"
                onClick={handleRelatedAction}
              >
                View Invoice
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
