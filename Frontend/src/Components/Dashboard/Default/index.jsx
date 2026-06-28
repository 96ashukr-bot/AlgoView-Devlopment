import React, { Fragment, useEffect, useState } from "react";
import { Link, Navigate, useSearchParams } from "react-router-dom";
import { ArrowLeft } from "react-feather";
import { Container, Row } from "reactstrap";
import { Breadcrumbs } from "../../../AbstractElements";
import { RotatingLines } from "react-loader-spinner";
import ClientHeader from "../../Application/Clients/Client/ClientHeader";
import GreetingCard from "./GreetingCard";
import ClientAlert from "../../Application/Clients/Client/ClientAlert";
import { fetchUserProfile, getSupportChatUnreadCount } from "../../../Services/Authentication";
import "./Dashboards.css";

const SUPPORT_CHAT_BADGE_INTERVAL_MS = 30000;

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [supportChatUnreadCount, setSupportChatUnreadCount] = useState(0);
  const [userProfile, setUserProfile] = useState(null);
  const [searchParams] = useSearchParams();
  const requestedClientId = searchParams.get("client_id") || "";
  const viewedClientId = /^\d+$/.test(requestedClientId) ? requestedClientId : "";

  const roleName = String(userProfile?.role?.name || "").trim().toLowerCase();
  const isClient = ["client", "user"].includes(roleName);
  const isStaffUser = [
    "admin",
    "super-admin",
    "superadmin",
    "sub-admin",
    "subadmin",
  ].includes(roleName);
  const isStaffPreview = Boolean(viewedClientId) && isStaffUser;

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false);
    },);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    let mounted = true;
    fetchUserProfile()
      .then((profile) => {
        if (mounted) setUserProfile(profile);
      })
      .catch(() => {
        if (mounted) setUserProfile(null);
      });
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!isClient) return undefined;
    let timeoutId;
    let cancelled = false;

    const refreshUnreadCount = async () => {
      if (cancelled || document.hidden) return;
      try {
        const data = await getSupportChatUnreadCount();
        setSupportChatUnreadCount(Number(data.unread_count || 0));
      } catch (_error) {
        setSupportChatUnreadCount(0);
      }
    };
    const scheduleRefresh = () => {
      timeoutId = window.setTimeout(async () => {
        await refreshUnreadCount();
        if (!cancelled) {
          scheduleRefresh();
        }
      }, SUPPORT_CHAT_BADGE_INTERVAL_MS);
    };
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        refreshUnreadCount();
      }
    };

    refreshUnreadCount();
    scheduleRefresh();
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [isClient]);

  if (userProfile && isStaffUser && !viewedClientId) {
    return <Navigate to="/dashboard/algoviewtech/admin" replace />;
  }

  return (
    <Fragment>
      {isStaffPreview ? (
        <div className="client-preview-toolbar">
          <div>
            <strong>Client dashboard preview</strong>
            <span>You are still signed in as an administrator.</span>
          </div>
          <Link to="/client/all-clients-list" className="btn btn-primary btn-sm">
            <ArrowLeft size={15} />
            Back to Client List
          </Link>
        </div>
      ) : null}
      <Breadcrumbs mainTitle="Default" parent="Dashboard" title="Default" />
      <Container fluid={true}>
        {loading ? (
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              height: "70vh",
            }}
          >
            <RotatingLines
              strokeColor="#283F7B"
              strokeWidth="4"
              animationDuration="0.75"
              width="80"
              visible={true}
            />
          </div>
        ) : (
          <Row className="widget-grid">
            <ClientHeader clientId={viewedClientId} />
            {(isClient || isStaffPreview) && <GreetingCard userProfile={userProfile} clientId={viewedClientId} />}
            {isClient ? <ClientAlert /> : null}
          </Row>
        )}
      </Container>
      {isClient && !loading ? (
        <Link to="/support-chat" className="client-support-chat-fab" title="Support Chat">
          <i className="fa fa-comments" />
          <span>Support Chat</span>
          {supportChatUnreadCount > 0 ? (
            <span className="client-support-chat-fab-badge">
              {supportChatUnreadCount > 99 ? "99+" : supportChatUnreadCount}
            </span>
          ) : null}
        </Link>
      ) : null}
    </Fragment>
  );
};

export default Dashboard;
