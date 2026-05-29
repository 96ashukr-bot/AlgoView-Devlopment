import React, { Fragment, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  Col,
  FormGroup,
  Input,
  Label,
  Row,
} from "reactstrap";
import { H3 } from "../../../AbstractElements";
import {
  createSupportChatThread,
  fetchUserProfile,
  getSupportChatClients,
  getSupportChatThread,
  getSupportChatThreads,
  sendSupportChatMessage,
  updateSupportChatThread,
} from "../../../Services/Authentication";
import "./SupportChat.css";

const roleName = (profile) => String(profile?.role?.name || "").toLowerCase();
const isStaffProfile = (profile) => ["super-admin", "superadmin", "admin", "sub-admin", "subadmin"].includes(roleName(profile));
const isSuperProfile = (profile) => ["super-admin", "superadmin", "admin"].includes(roleName(profile));
const CHAT_REFRESH_INTERVAL_MS = 10000;

const formatDateTime = (value) => {
  if (!value) return "-";
  try {
    return new Date(value).toLocaleString("en-IN", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch (_error) {
    return value;
  }
};

const SupportChat = () => {
  const [profile, setProfile] = useState(null);
  const [threads, setThreads] = useState([]);
  const [clients, setClients] = useState([]);
  const [selectedThreadId, setSelectedThreadId] = useState(null);
  const [threadDetail, setThreadDetail] = useState(null);
  const [filters, setFilters] = useState({ status: "", search: "" });
  const [newThread, setNewThread] = useState({ subject: "", message: "", client_id: "" });
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");
  const selectedThreadIdRef = useRef(null);
  const filtersRef = useRef(filters);

  const staff = useMemo(() => isStaffProfile(profile), [profile]);
  const superStaff = useMemo(() => isSuperProfile(profile), [profile]);

  useEffect(() => {
    selectedThreadIdRef.current = selectedThreadId;
  }, [selectedThreadId]);

  useEffect(() => {
    filtersRef.current = filters;
  }, [filters]);

  const loadThreads = useCallback(async (nextFilters = filtersRef.current, options = {}) => {
    const silent = Boolean(options.silent);
    if (!silent) {
      setLoading(true);
      setError("");
    }
    try {
      const data = await getSupportChatThreads({
        status: nextFilters.status || undefined,
        search: nextFilters.search || undefined,
      });
      const results = data.results || [];
      setThreads(results);
      if (!selectedThreadIdRef.current && results.length > 0) {
        setSelectedThreadId(results[0].id);
      }
    } catch (err) {
      if (!silent) {
        setError(err?.response?.data?.message || err.message || "Unable to load chats.");
        setThreads([]);
      }
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }, []);

  const loadThreadDetail = useCallback(async (threadId, options = {}) => {
    if (!threadId) {
      setThreadDetail(null);
      return;
    }
    const silent = Boolean(options.silent);
    if (!silent) {
      setDetailLoading(true);
      setError("");
    }
    try {
      const data = await getSupportChatThread(threadId);
      setThreadDetail(data);
      setThreads((prev) => prev.map((thread) => (thread.id === threadId ? data.thread : thread)));
    } catch (err) {
      if (!silent) {
        setError(err?.response?.data?.message || err.message || "Unable to load chat.");
        setThreadDetail(null);
      }
    } finally {
      if (!silent) {
        setDetailLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      try {
        const userProfile = await fetchUserProfile();
        setProfile(userProfile);
        if (isStaffProfile(userProfile)) {
          const clientData = await getSupportChatClients();
          setClients(clientData.results || []);
        }
      } catch (err) {
        setError(err?.response?.data?.message || err.message || "Unable to load profile.");
      }
      loadThreads();
    };
    init();
  }, [loadThreads]);

  useEffect(() => {
    loadThreadDetail(selectedThreadId);
  }, [loadThreadDetail, selectedThreadId]);

  useEffect(() => {
    if (!profile) return undefined;
    const intervalId = window.setInterval(async () => {
      if (document.hidden) return;
      await loadThreads(filtersRef.current, { silent: true });
      if (selectedThreadIdRef.current) {
        await loadThreadDetail(selectedThreadIdRef.current, { silent: true });
      }
    }, CHAT_REFRESH_INTERVAL_MS);

    return () => window.clearInterval(intervalId);
  }, [loadThreadDetail, loadThreads, profile]);

  const handleFilterChange = (event) => {
    const { name, value } = event.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  };

  const handleNewThreadChange = (event) => {
    const { name, value } = event.target;
    setNewThread((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreateThread = async () => {
    if (!newThread.message.trim()) {
      setError("Message is required.");
      return;
    }
    if (staff && !newThread.client_id) {
      setError("Select a client first.");
      return;
    }
    setError("");
    try {
      const created = await createSupportChatThread({
        subject: newThread.subject,
        message: newThread.message,
        client_id: staff ? newThread.client_id : undefined,
      });
      setNewThread({ subject: "", message: "", client_id: "" });
      await loadThreads();
      setSelectedThreadId(created.id);
    } catch (err) {
      setError(err?.response?.data?.message || err.message || "Unable to create chat.");
    }
  };

  const handleSendReply = async () => {
    if (!selectedThreadId || !reply.trim()) return;
    setError("");
    try {
      await sendSupportChatMessage(selectedThreadId, { message: reply });
      setReply("");
      await loadThreadDetail(selectedThreadId);
      await loadThreads();
    } catch (err) {
      setError(err?.response?.data?.message || err.message || "Unable to send reply.");
    }
  };

  const handleStatusChange = async (status) => {
    if (!selectedThreadId) return;
    setError("");
    try {
      await updateSupportChatThread(selectedThreadId, { status });
      await loadThreadDetail(selectedThreadId);
      await loadThreads();
    } catch (err) {
      setError(err?.response?.data?.message || err.message || "Unable to update chat status.");
    }
  };

  const selectedThread = threadDetail?.thread;
  const messages = threadDetail?.messages || [];

  return (
    <Fragment>
      <Col sm="12">
        <Card className="support-chat-shell">
          <CardHeader>
            <div className="d-flex justify-content-between align-items-center flex-wrap gap-2">
              <div>
                <H3>Support Chat</H3>
              </div>
              <div className="d-flex gap-2">
                <Badge color="light-success" className="align-self-center">
                  Auto refresh on
                </Badge>
                <Button color="light" onClick={() => loadThreads()} disabled={loading}>
                  <i className="fa fa-refresh me-1" />
                  Refresh
                </Button>
              </div>
            </div>
          </CardHeader>

          <div className="p-3">
            {error ? <div className="alert alert-danger py-2">{error}</div> : null}

            <Row className="g-0 border rounded overflow-hidden">
              <Col md="4" className="support-chat-list">
                <div className="p-3 border-bottom">
                  <Row className="g-2">
                    <Col md="7">
                      <Input
                        name="search"
                        value={filters.search}
                        onChange={handleFilterChange}
                        placeholder="Search chats"
                      />
                    </Col>
                    <Col md="5">
                      <Input name="status" type="select" value={filters.status} onChange={handleFilterChange}>
                        <option value="">All</option>
                        <option value="open">Open</option>
                        <option value="resolved">Resolved</option>
                      </Input>
                    </Col>
                    <Col md="12">
                      <Button className="search-btn-clr w-100" onClick={() => loadThreads(filters)} disabled={loading}>
                        Apply
                      </Button>
                    </Col>
                  </Row>
                </div>

                <div className="p-3 border-bottom">
                  {staff ? (
                    <FormGroup>
                      <Label>{superStaff ? "Client" : "Assigned Client"}</Label>
                      <Input name="client_id" type="select" value={newThread.client_id} onChange={handleNewThreadChange}>
                        <option value="">Select client</option>
                        {clients.map((client) => (
                          <option key={client.id} value={client.id}>
                            {client.name} {client.email ? `(${client.email})` : ""}
                          </option>
                        ))}
                      </Input>
                    </FormGroup>
                  ) : null}
                  <FormGroup>
                    <Label>Subject</Label>
                    <Input name="subject" value={newThread.subject} onChange={handleNewThreadChange} placeholder="Optional" />
                  </FormGroup>
                  <FormGroup>
                    <Label>{staff ? "Start Message" : "Send Message / Query"}</Label>
                    <Input
                      name="message"
                      type="textarea"
                      rows="3"
                      value={newThread.message}
                      onChange={handleNewThreadChange}
                      placeholder="Type message"
                    />
                  </FormGroup>
                  <Button className="search-btn-clr w-100" onClick={handleCreateThread}>
                    <i className="fa fa-paper-plane me-1" />
                    Send
                  </Button>
                </div>

                <div>
                  {threads.length === 0 ? (
                    <div className="p-4 text-center text-muted">{loading ? "Loading chats..." : "No chats found."}</div>
                  ) : (
                    threads.map((thread) => (
                      <button
                        key={thread.id}
                        type="button"
                        className={`support-thread-item ${selectedThreadId === thread.id ? "active" : ""}`}
                        onClick={() => setSelectedThreadId(thread.id)}
                      >
                        <div className="d-flex justify-content-between gap-2">
                          <div className="support-thread-title">{thread.subject || "General Query"}</div>
                          <Badge color={thread.status === "open" ? "light-primary" : "light-success"}>{thread.status}</Badge>
                        </div>
                        {staff ? <div className="support-thread-meta">{thread.client?.name || thread.client?.email}</div> : null}
                        <div className="support-thread-preview">{thread.last_message?.message || "No message"}</div>
                        <div className="d-flex justify-content-between align-items-center support-thread-meta mt-1">
                          <span>{formatDateTime(thread.last_message_at)}</span>
                          {thread.unread_count ? <Badge color="danger">{thread.unread_count}</Badge> : null}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </Col>

              <Col md="8" className="support-chat-window">
                {!selectedThread ? (
                  <div className="support-empty-state">{detailLoading ? "Loading chat..." : "Select a chat to view messages."}</div>
                ) : (
                  <>
                    <div className="p-3 border-bottom d-flex justify-content-between align-items-center flex-wrap gap-2">
                      <div>
                        <h5 className="mb-1">{selectedThread.subject || "General Query"}</h5>
                        <div className="text-muted small">
                          {selectedThread.client?.name || selectedThread.client?.email} · {formatDateTime(selectedThread.last_message_at)}
                        </div>
                      </div>
                      <div className="d-flex align-items-center gap-2">
                        <Badge color={selectedThread.status === "open" ? "light-primary" : "light-success"}>
                          {selectedThread.status}
                        </Badge>
                        {staff ? (
                          <Button
                            color={selectedThread.status === "open" ? "success" : "warning"}
                            size="sm"
                            onClick={() => handleStatusChange(selectedThread.status === "open" ? "resolved" : "open")}
                          >
                            {selectedThread.status === "open" ? "Resolve" : "Reopen"}
                          </Button>
                        ) : null}
                      </div>
                    </div>

                    <div className="support-message-list">
                      {messages.map((message) => {
                        const ownMessage = staff
                          ? message.sender_role !== "client"
                          : message.sender_role === "client";
                        return (
                          <div key={message.id} className={`support-message ${ownMessage ? "own" : ""}`}>
                            <div className="support-message-role">
                              {message.sender_role} · {formatDateTime(message.created_at)}
                            </div>
                            <div className="support-message-text">{message.message}</div>
                          </div>
                        );
                      })}
                    </div>

                    <div className="p-3 border-top">
                      <Row className="g-2">
                        <Col md="10">
                          <Input
                            type="textarea"
                            rows="2"
                            value={reply}
                            onChange={(event) => setReply(event.target.value)}
                            placeholder={staff ? "Reply to client" : "Reply"}
                          />
                        </Col>
                        <Col md="2" className="d-grid">
                          <Button className="search-btn-clr" onClick={handleSendReply} disabled={!reply.trim()}>
                            Send
                          </Button>
                        </Col>
                      </Row>
                    </div>
                  </>
                )}
              </Col>
            </Row>
          </div>
        </Card>
      </Col>
    </Fragment>
  );
};

export default SupportChat;
