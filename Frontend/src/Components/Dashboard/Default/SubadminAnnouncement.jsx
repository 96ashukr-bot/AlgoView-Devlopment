import React, { useCallback, useEffect, useState } from "react";
import { Alert, Button, Card, CardBody, Col, FormGroup, Label, Spinner } from "reactstrap";
import {
  fetchUserProfile,
  getSubadminDashboardAnnouncement,
  updateSubadminDashboardAnnouncement,
} from "../../../Services/Authentication";

const normalizeRole = (profile) => String(profile?.role?.name || "").trim().toLowerCase();

const SubadminAnnouncement = () => {
  const [role, setRole] = useState("");
  const [subadminName, setSubadminName] = useState("");
  const [message, setMessage] = useState("");
  const [activeMessage, setActiveMessage] = useState("");
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
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAnnouncement().catch(() => setFeedback("Unable to load the dashboard message."));
  }, [loadAnnouncement]);

  const isSuperadmin = ["super-admin", "superadmin"].includes(role);
  const isSubadmin = ["sub-admin", "subadmin"].includes(role);

  const saveMessage = async (nextMessage) => {
    setSaving(true);
    setFeedback("");
    try {
      const announcement = await updateSubadminDashboardAnnouncement(nextMessage);
      const savedMessage = announcement?.is_active ? String(announcement.message || "") : "";
      setMessage(savedMessage);
      setActiveMessage(savedMessage);
      setFeedback(savedMessage ? "Message published to all Subadmin dashboards." : "Message removed from Subadmin dashboards.");
    } catch (error) {
      setFeedback(error?.response?.data?.message || error?.response?.data?.detail || "Unable to save the message.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <Col xs="12" className="mb-3"><Spinner size="sm" /> Loading dashboard message…</Col>;
  }
  if (isSubadmin && activeMessage) {
    return (
      <Col xs="12">
        <Alert color="primary" className="mb-3 shadow-sm">
          <strong className="d-block mb-1">Message from Superadmin</strong>
          <strong className="d-block mb-1">Dear {subadminName || "Subadmin"},</strong>
          <span style={{ whiteSpace: "pre-wrap" }}>{activeMessage}</span>
        </Alert>
      </Col>
    );
  }
  if (!isSuperadmin) return null;

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
          <Button color="primary" disabled={saving || !message.trim()} onClick={() => saveMessage(message.trim())}>
            {saving ? "Publishing…" : "Publish Message"}
          </Button>{" "}
          <Button color="outline-danger" disabled={saving || !activeMessage} onClick={() => saveMessage("")}>
            Clear Message
          </Button>
          {feedback ? <div className="mt-2">{feedback}</div> : null}
        </CardBody>
      </Card>
    </Col>
  );
};

export default SubadminAnnouncement;
