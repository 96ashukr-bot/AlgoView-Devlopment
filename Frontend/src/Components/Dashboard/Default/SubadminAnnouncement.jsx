import React, { useCallback, useEffect, useState } from "react";
import { Alert, Button, Card, CardBody, Col, FormGroup, Label, Spinner } from "reactstrap";
import {
  fetchUserProfile,
  getSubadminDashboardAnnouncement,
  updateSubadminDashboardAnnouncement,
} from "../../../Services/Authentication";

const normalizeRole = (profile) => String(profile?.role?.name || "").trim().toLowerCase();

const SubadminAnnouncement = ({ mode = "dashboard" }) => {
  const [role, setRole] = useState("");
  const [subadminName, setSubadminName] = useState("");
  const [message, setMessage] = useState("");
  const [activeMessage, setActiveMessage] = useState("");
  const [mediaUrl, setMediaUrl] = useState("");
  const [mediaFile, setMediaFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState("");

  const loadAnnouncement = useCallback(async () => {
    setLoading(true);
    try {
      const profile = await fetchUserProfile();
      const nextRole = normalizeRole(profile);
      setRole(nextRole);
      setSubadminName(
        String(
          profile?.fullName
          || [profile?.firstName, profile?.middleName, profile?.lastName].filter(Boolean).join(" ")
          || profile?.userName
          || "Subadmin"
        ).trim()
      );
      if (!["super-admin", "superadmin", "sub-admin", "subadmin"].includes(nextRole)) return;
      const announcement = await getSubadminDashboardAnnouncement();
      const nextMessage = announcement?.is_active ? String(announcement.message || "") : "";
      setMessage(nextMessage);
      setActiveMessage(nextMessage);
      setMediaUrl(announcement?.is_active ? String(announcement.media_url || "") : "");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAnnouncement().catch(() => setFeedback("Unable to load the dashboard message."));
  }, [loadAnnouncement]);

  const isSuperadmin = ["super-admin", "superadmin"].includes(role);
  const isSubadmin = ["sub-admin", "subadmin"].includes(role);

  const saveMessage = async (nextMessage, options = {}) => {
    setSaving(true);
    setFeedback("");
    try {
      const announcement = await updateSubadminDashboardAnnouncement(
        nextMessage,
        options.media || null,
        Boolean(options.removeMedia)
      );
      const savedMessage = announcement?.is_active ? String(announcement.message || "") : "";
      setMessage(savedMessage);
      setActiveMessage(savedMessage);
      setMediaUrl(announcement?.is_active ? String(announcement.media_url || "") : "");
      setMediaFile(null);
      setFeedback(announcement?.is_active ? "Announcement published to all Subadmin dashboards." : "Announcement removed from Subadmin dashboards.");
    } catch (error) {
      setFeedback(error?.response?.data?.message || error?.response?.data?.detail || "Unable to save the message.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <Col xs="12" className="mb-3"><Spinner size="sm" /> Loading dashboard message…</Col>;
  }
  if (mode === "dashboard" && isSubadmin && (activeMessage || mediaUrl)) {
    return (
      <Col xs="12">
        <Alert
          color="light"
          className="mb-3 text-center border-0"
          style={{ backgroundColor: "transparent" }}
        >
          <strong className="d-block mb-1">Dear {subadminName || "Subadmin"},</strong>
          {activeMessage ? <span className="d-block" style={{ whiteSpace: "pre-wrap" }}>{activeMessage}</span> : null}
          {mediaUrl ? <img className="mt-2" src={mediaUrl} alt="Announcement" style={{ maxWidth: "100%", maxHeight: "320px", objectFit: "contain" }} /> : null}
        </Alert>
      </Col>
    );
  }
  if (mode !== "settings" || !isSuperadmin) return null;

  return (
    <Col xs="12">
      <Card className="mb-3">
        <CardBody>
          <h5 className="mb-2">Subadmin Dashboard Message</h5>
          <p className="text-muted">Publish a message at the top of every Subadmin dashboard.</p>
          <FormGroup>
            <Label for="subadmin-dashboard-message">Message</Label>
            <textarea
              id="subadmin-dashboard-message"
              className="form-control"
              rows="3"
              maxLength="2000"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Write a message for Subadmins…"
            />
            <small className="text-muted">{message.length}/2000 characters</small>
          </FormGroup>
          <FormGroup>
            <Label for="subadmin-dashboard-media">GIF or Sticker (optional)</Label>
            <input
              id="subadmin-dashboard-media"
              className="form-control"
              type="file"
              accept="image/gif,image/png,image/webp,image/jpeg"
              onChange={(event) => setMediaFile(event.target.files?.[0] || null)}
            />
            <small className="text-muted">GIF, PNG, WebP or JPEG, maximum 5 MB.</small>
            {mediaUrl ? (
              <div className="mt-2">
                <img src={mediaUrl} alt="Current announcement" style={{ maxWidth: "240px", maxHeight: "180px", objectFit: "contain" }} />
                <div><Button className="mt-2" size="sm" color="outline-danger" disabled={saving} onClick={() => saveMessage(message.trim(), { removeMedia: true })}>Remove GIF/Sticker</Button></div>
              </div>
            ) : null}
          </FormGroup>
          <Button color="primary" disabled={saving || (!message.trim() && !mediaFile && !mediaUrl)} onClick={() => saveMessage(message.trim(), { media: mediaFile })}>
            {saving ? "Publishing…" : "Publish Announcement"}
          </Button>{" "}
          <Button color="outline-danger" disabled={saving || (!activeMessage && !mediaUrl)} onClick={() => saveMessage("", { removeMedia: true })}>
            Clear Announcement
          </Button>
          {feedback ? <div className="mt-2">{feedback}</div> : null}
        </CardBody>
      </Card>
    </Col>
  );
};

export default SubadminAnnouncement;
