import { FormEvent, useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  Camera,
  Mail,
  Phone,
  Save,
  UserRound,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api";

type CustomerProfileData = {
  customer_id: string;
  full_name: string;
  phone_number: string;
  email: string | null;
  profile_image_url: string | null;
  date_of_birth: string | null;
  status: string;
};

export default function CustomerEditProfile() {
  const navigate = useNavigate();

  const [customerId, setCustomerId] = useState("");
  const [fullName, setFullName] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [email, setEmail] = useState("");
  const [profileImageUrl, setProfileImageUrl] = useState<string | null>(null);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraError, setCameraError] = useState("");

  const cameraVideoRef = useRef<HTMLVideoElement | null>(null);
  const cameraStreamRef = useRef<MediaStream | null>(null);
  const cameraCanvasRef = useRef<HTMLCanvasElement | null>(null);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadProfile() {
      try {
        setLoading(true);
        setError("");

        const result =
          await apiFetch<CustomerProfileData>("/customers/me");

        setCustomerId(result.customer_id || "");
        setFullName(result.full_name || "");
        setDateOfBirth(result.date_of_birth || "");
        setPhoneNumber(result.phone_number || "");
        setEmail(result.email || "");
        setProfileImageUrl(result.profile_image_url || null);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load your profile."
        );
      } finally {
        setLoading(false);
      }
    }

    loadProfile();
  }, []);

  async function openCamera() {
    try {
      setCameraError("");

      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error(
          "Camera access is not supported by this browser."
        );
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "user" },
          width: { ideal: 1280 },
          height: { ideal: 1280 },
        },
        audio: false,
      });

      cameraStreamRef.current = stream;
      setCameraOpen(true);

      requestAnimationFrame(() => {
        if (cameraVideoRef.current) {
          cameraVideoRef.current.srcObject = stream;
          cameraVideoRef.current.play().catch(() => {});
        }
      });
    } catch (err) {
      setCameraError(
        err instanceof Error
          ? err.message
          : "Unable to access your camera."
      );
    }
  }

  function closeCamera() {
    if (cameraStreamRef.current) {
      cameraStreamRef.current.getTracks().forEach((track) => track.stop());
      cameraStreamRef.current = null;
    }

    if (cameraVideoRef.current) {
      cameraVideoRef.current.srcObject = null;
    }

    setCameraOpen(false);
    setCameraError("");
  }

  async function captureProfilePhoto() {
    const video = cameraVideoRef.current;
    const canvas = cameraCanvasRef.current;

    if (!video || !canvas || video.readyState < 2) {
      setCameraError("Camera is not ready yet. Please try again.");
      return;
    }

    try {
      setUploadingImage(true);
      setCameraError("");
      setError("");

      const size = Math.min(
        video.videoWidth || 1024,
        video.videoHeight || 1024
      );

      canvas.width = size;
      canvas.height = size;

      const context = canvas.getContext("2d");

      if (!context) {
        throw new Error("Unable to capture the camera image.");
      }

      const sourceSize = Math.min(
        video.videoWidth,
        video.videoHeight
      );

      const sourceX = (video.videoWidth - sourceSize) / 2;
      const sourceY = (video.videoHeight - sourceSize) / 2;

      context.drawImage(
        video,
        sourceX,
        sourceY,
        sourceSize,
        sourceSize,
        0,
        0,
        size,
        size
      );

      const blob = await new Promise<Blob | null>((resolve) =>
        canvas.toBlob(resolve, "image/jpeg", 0.9)
      );

      if (!blob) {
        throw new Error("Unable to create the profile photo.");
      }

      const formData = new FormData();
      formData.append("file", blob, "profile-photo.jpg");

      const token = sessionStorage.getItem("digibills_token");

      if (!token) {
        throw new Error(
          "Your session has expired. Please log in again."
        );
      }

      const apiBase =
        import.meta.env.VITE_API_BASE_URL ||
        "http://127.0.0.1:8000";

      const response = await fetch(
        `${apiBase}/customers/me/profile-image`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail || "Unable to update your profile photo."
        );
      }

      setProfileImageUrl(data.profile_image_url || null);
      closeCamera();
    } catch (err) {
      setCameraError(
        err instanceof Error
          ? err.message
          : "Unable to update your profile photo."
      );
    } finally {
      setUploadingImage(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!fullName.trim()) {
      setError("Full name is required.");
      return;
    }

    if (!phoneNumber.trim()) {
      setError("Phone number is required.");
      return;
    }

    try {
      setSaving(true);
      setError("");

      await apiFetch<CustomerProfileData>("/customers/me", {
        method: "PUT",
        body: JSON.stringify({
          full_name: fullName.trim(),
          phone_number: phoneNumber.trim(),
          email: email.trim() || null,
          profile_image_url: profileImageUrl,
          date_of_birth: dateOfBirth || null,
        }),
      });

      navigate("/customer/profile");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to update your profile."
      );
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <section className="dashboard customer-edit-profile-screen">
        <div className="customer-mobile-page-header">
          <button
            type="button"
            className="customer-back-button"
            onClick={() => navigate(-1)}
            aria-label="Go back"
          >
            <ArrowLeft size={20} />
          </button>

          <h1>Edit Profile</h1>

          <span className="customer-header-spacer" />
        </div>

        <div className="customer-profile-loading">
          Loading your profile...
        </div>
      </section>
    );
  }

  return (
    <section className="dashboard customer-edit-profile-screen">
      <div className="customer-mobile-page-header">
        <button
          type="button"
          className="customer-back-button"
          onClick={() => navigate("/customer/profile")}
          aria-label="Go back"
        >
          <ArrowLeft size={20} />
        </button>

        <h1>Edit Profile</h1>

        <span className="customer-header-spacer" />
      </div>

      <form
        className="customer-edit-profile-card"
        onSubmit={handleSubmit}
      >
        <div className="customer-edit-profile-photo-section">
          <div className="customer-edit-profile-photo">
            {profileImageUrl ? (
              <img
                src={
                  profileImageUrl.startsWith("http")
                    ? profileImageUrl
                    : `http://127.0.0.1:8000${profileImageUrl}`
                }
                alt="Profile"
              />
            ) : (
              <UserRound size={30} />
            )}
          </div>

          <button
            type="button"
            className="customer-edit-profile-camera"
            onClick={openCamera}
            disabled={uploadingImage || saving}
            aria-label="Take profile photo"
            title="Take profile photo"
          >
            <Camera size={17} />
          </button>

          <div className="customer-edit-profile-photo-copy">
            <strong>{uploadingImage ? "Saving photo..." : "Profile Photo"}</strong>
            <span>Use your camera to update your profile photo.</span>
          </div>
        </div>

        {cameraOpen && (
          <div
            className="customer-profile-camera-modal"
            role="dialog"
            aria-modal="true"
            aria-label="Take profile photo"
          >
            <div className="customer-profile-camera-modal-card">
              <div className="customer-profile-camera-modal-header">
                <div>
                  <strong>Take Profile Photo</strong>
                  <span>Position your face inside the frame.</span>
                </div>

                <button
                  type="button"
                  className="customer-profile-camera-close"
                  onClick={closeCamera}
                  disabled={uploadingImage}
                  aria-label="Close camera"
                >
                  ×
                </button>
              </div>

              <div className="customer-profile-camera-preview">
                <video
                  ref={cameraVideoRef}
                  autoPlay
                  playsInline
                  muted
                />
                <div className="customer-profile-camera-guide" />
              </div>

              {cameraError && (
                <div
                  className="customer-edit-profile-error"
                  role="alert"
                >
                  {cameraError}
                </div>
              )}

              <div className="customer-profile-camera-actions">
                <button
                  type="button"
                  className="customer-profile-camera-cancel"
                  onClick={closeCamera}
                  disabled={uploadingImage}
                >
                  Cancel
                </button>

                <button
                  type="button"
                  className="customer-profile-camera-capture"
                  onClick={captureProfilePhoto}
                  disabled={uploadingImage}
                >
                  <Camera size={17} />
                  {uploadingImage ? "Saving..." : "Capture Photo"}
                </button>
              </div>

              <canvas
                ref={cameraCanvasRef}
                className="customer-profile-camera-canvas"
              />
            </div>
          </div>
        )}

        <div className="customer-edit-profile-intro">
          <div className="customer-edit-profile-icon">
            <UserRound size={22} />
          </div>

          <div>
            <h2>Personal Information</h2>
            <p>Keep your profile information up to date.</p>
          </div>
        </div>

        {error && (
          <div className="customer-edit-profile-error" role="alert">
            {error}
          </div>
        )}

        <div className="customer-edit-profile-fields">
          <label className="customer-edit-profile-field">
            <span>Customer ID</span>

            <div className="customer-edit-profile-input-wrap">
              <UserRound size={17} />
              <input
                type="text"
                value={customerId}
                readOnly
                aria-readonly="true"
              />
            </div>
          </label>

          <label className="customer-edit-profile-field">
            <span>Full Name</span>

            <div className="customer-edit-profile-input-wrap">
              <UserRound size={17} />
              <input
                type="text"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Enter your full name"
                autoComplete="name"
              />
            </div>
          </label>

          <label className="customer-edit-profile-field">
            <span>Date of Birth</span>

            <div className="customer-edit-profile-input-wrap">
              <input
                type="date"
                value={dateOfBirth}
                onChange={(event) => setDateOfBirth(event.target.value)}
                aria-label="Date of Birth"
              />
            </div>
          </label>

          <label className="customer-edit-profile-field">
            <span>Phone Number</span>

            <div className="customer-edit-profile-input-wrap">
              <Phone size={17} />
              <input
                type="tel"
                value={phoneNumber}
                onChange={(event) =>
                  setPhoneNumber(event.target.value)
                }
                placeholder="Enter your phone number"
                autoComplete="tel"
              />
            </div>
          </label>

          <label className="customer-edit-profile-field">
            <span>Email Address</span>

            <div className="customer-edit-profile-input-wrap">
              <Mail size={17} />
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="Enter your email address"
                autoComplete="email"
              />
            </div>
          </label>
        </div>

        <div className="customer-edit-profile-actions">
          <button
            type="button"
            className="customer-edit-profile-cancel"
            onClick={() => navigate("/customer/profile")}
            disabled={saving}
          >
            Cancel
          </button>

          <button
            type="submit"
            className="customer-primary-button customer-edit-profile-save"
            disabled={saving}
          >
            <Save size={17} />
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </form>
    </section>
  );
}
