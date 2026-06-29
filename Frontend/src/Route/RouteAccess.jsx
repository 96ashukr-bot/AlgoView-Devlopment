import React, { useEffect, useMemo, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import Loader from "../Layout/Loader";
import { fetchUserProfile } from "../Services/Authentication";

const STAFF_ONLY_PREFIXES = [
  "/client",
  "/settings",
  "/service-manage",
  "/subadmin",
  "/kyc",
  "/ip-pool",
  "/license",
];

const STAFF_ONLY_PATHS = [
  "/dashboard/admin",
  "/dashboard/algoviewtech/admin",
  "/dashboard/rolepermmision",
  "/dashboard/rolepermmisionupdate",
  "/tradedetails/signals",
  "/tradedetails/trade-history",
  "/tradedetails/complete-trade-history",
  "/tradedetails/trading-status",
  "/tradedetails/webhook-diagnostics",
  "/tradedetails/sl-tp-watcher",
  "/openposition/optionchainlist",
];

const CLIENT_ALLOWED_PATHS = [
  "/dashboard/user",
  "/dashboard/algoviewtech/user",
  "/dashboard/segments/update-segment",
  "/dashboard/optionchain",
  "/tradedetails/client-trade-history",
  "/tradedetails/signals",
  "/tradedetails/complete-trade-history",
  "/support-chat",
  "/dashboard/helpcenter",
  "/callback",
  "/apiinfo/apikeys",
];

const normalizeRole = (profile) => {
  const rawRole = String(profile?.role?.name || "").trim().toLowerCase();
  if (["super-admin", "superadmin", "admin"].includes(rawRole)) {
    return "admin";
  }
  if (["sub-admin", "subadmin"].includes(rawRole)) {
    return "subadmin";
  }
  if (
    ["client", "user"].includes(rawRole) ||
    profile?.type_of_user === "is_client" ||
    profile?.is_client === true ||
    String(profile?.is_client || "").toLowerCase() === "true"
  ) {
    return "client";
  }
  return rawRole || "unknown";
};

const pathMatches = (pathname, prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`);

const isStaffOnlyPath = (pathname) => {
  if (CLIENT_ALLOWED_PATHS.some((prefix) => pathMatches(pathname, prefix))) {
    return false;
  }
  return (
    STAFF_ONLY_PATHS.some((prefix) => pathMatches(pathname, prefix)) ||
    STAFF_ONLY_PREFIXES.some((prefix) => pathMatches(pathname, prefix))
  );
};

const RouteAccess = ({ children }) => {
  const location = useLocation();
  const [state, setState] = useState({ loading: true, role: null, checkedPath: null });
  const staffOnly = useMemo(() => isStaffOnlyPath(location.pathname), [location.pathname]);

  useEffect(() => {
    let mounted = true;
    const loadProfile = async () => {
      if (!staffOnly) {
        setState({ loading: false, role: null, checkedPath: location.pathname });
        return;
      }
      setState({ loading: true, role: null, checkedPath: location.pathname });
      try {
        const profile = await fetchUserProfile();
        if (mounted) {
          setState({ loading: false, role: normalizeRole(profile), checkedPath: location.pathname });
        }
      } catch (_error) {
        if (mounted) {
          setState({ loading: false, role: "unknown", checkedPath: location.pathname });
        }
      }
    };
    loadProfile();
    return () => {
      mounted = false;
    };
  }, [staffOnly, location.pathname]);

  if (!staffOnly) {
    return children;
  }

  if (state.loading || state.checkedPath !== location.pathname) {
    return <Loader />;
  }

  if (!["admin", "subadmin"].includes(state.role)) {
    return <Navigate to="/dashboard/algoviewtech/user" replace />;
  }

  return children;
};

export default RouteAccess;
