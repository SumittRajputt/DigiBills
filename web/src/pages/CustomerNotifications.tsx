import { useEffect, useState } from "react";
import { ArrowLeft, Bell, CheckCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";
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

export default function CustomerNotifications() {
  const navigate = useNavigate();

  const [notifications, setNotifications] = useState<
    CustomerNotification[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadNotifications();
  }, []);

  async function loadNotifications() {
    try {
      setLoading(true);
      setError("");

      const payload = await apiFetch<CustomerNotification[]>(
        "/customer/notifications"
      );

      setNotifications(Array.isArray(payload) ? payload : []);
    } catch (err: any) {
      console.error("Failed to load notifications:", err);

      setError(
        err?.response?.data?.detail ||
          "Unable to load notifications right now."
      );
    } finally {
      setLoading(false);
    }
  }

  function formatDate(value: string) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "";
    }

    return date.toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  const unreadCount = notifications.filter(
    (notification) => !notification.is_read
  ).length;

  async function handleNotificationClick(
    notification: CustomerNotification
  ) {
    if (!notification.is_read) {
      try {
        await apiFetch<CustomerNotification>(
          `/customer/notifications/${notification.id}/read`,
          {
            method: "PATCH",
          }
        );

        setNotifications((current) =>
          current.map((item) =>
            item.id === notification.id
              ? { ...item, is_read: true }
              : item
          )
        );
      } catch (error) {
        console.error(
          "Failed to mark notification as read:",
          error
        );
      }
    }

    if (
      notification.reference_type === "invoice" &&
      notification.reference_id
    ) {
      navigate(
        `/customer/invoices/${notification.reference_id}`
      );
    }
  }

  return (
    <section className="customer-notifications-page">
      <div className="customer-notifications-header">
        <button
          type="button"
          className="customer-notifications-back"
          onClick={() => navigate("/customer")}
          aria-label="Back to dashboard"
        >
          <ArrowLeft size={18} />
        </button>

        <div>
          <div className="customer-page-eyebrow">
            Customer Notifications
          </div>

          <h1>
            Notifications
            {unreadCount > 0 && (
              <span className="customer-notifications-count">
                {unreadCount}
              </span>
            )}
          </h1>

          <p>
            Stay updated with your bills, payments and account activity.
          </p>
        </div>
      </div>

      <div className="customer-notifications-panel">
        {loading ? (
          <div className="customer-notifications-empty">
            <Bell size={28} />
            <strong>Loading notifications...</strong>
          </div>
        ) : error ? (
          <div className="customer-notifications-empty">
            <Bell size={28} />
            <strong>{error}</strong>

            <button
              type="button"
              className="customer-notifications-refresh"
              onClick={loadNotifications}
            >
              Try Again
            </button>
          </div>
        ) : notifications.length === 0 ? (
          <div className="customer-notifications-empty">
            <Bell size={32} />
            <strong>No notifications yet</strong>
            <span>
              New updates about your bills, payments and account
              activity will appear here.
            </span>
          </div>
        ) : (
          <div className="customer-notifications-list">
            {notifications.map((notification) => {
              const isClickable =
                notification.reference_type === "invoice" &&
                Boolean(notification.reference_id);

              return (
                <article
                  key={notification.id}
                  className={`customer-notification-item ${
                    !notification.is_read ? "unread" : ""
                  } ${isClickable ? "clickable" : ""}`}
                  onClick={() =>
                    isClickable &&
                    handleNotificationClick(notification)
                  }
                  role={isClickable ? "button" : undefined}
                  tabIndex={isClickable ? 0 : undefined}
                >
                  <div className="customer-notification-icon">
                    <Bell size={18} />
                  </div>

                  <div className="customer-notification-content">
                    <div className="customer-notification-title-row">
                      <strong>
                        {notification.title || "Notification"}
                      </strong>

                      {!notification.is_read && (
                        <span className="customer-notification-unread">
                          New
                        </span>
                      )}
                    </div>

                    <p>{notification.message}</p>

                    {notification.created_at && (
                      <small>
                        {formatDate(notification.created_at)}
                      </small>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>

      {notifications.length > 0 && (
        <div className="customer-notifications-footer">
          <CheckCheck size={16} />
          <span>
            Your latest account notifications are shown above.
          </span>
        </div>
      )}
    </section>
  );
}
