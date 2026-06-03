import React, { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import Loader from "../Layout/Loader";
import { getMyAgreementAcceptanceStatus } from "../Services/Authentication";

const LegalGate = () => {
  const location = useLocation();
  const [state, setState] = useState({ loading: true, accepted: true });

  useEffect(() => {
    let mounted = true;
    const checkStatus = async () => {
      try {
        const response = await getMyAgreementAcceptanceStatus();
        if (mounted) {
          setState({ loading: false, accepted: response.accepted !== false });
        }
      } catch (_error) {
        if (mounted) {
          setState({ loading: false, accepted: true });
        }
      }
    };
    checkStatus();
    return () => {
      mounted = false;
    };
  }, [location.pathname]);

  if (state.loading) {
    return <Loader />;
  }

  if (!state.accepted) {
    return <Navigate to="/terms-acceptance" replace />;
  }

  return <Outlet />;
};

export default LegalGate;
