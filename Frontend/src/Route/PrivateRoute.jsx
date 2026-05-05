import React, { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { getAccessToken, getRefreshToken } from "../Services/authStorage";

const hasUsableSession = () => Boolean(getAccessToken() || getRefreshToken());

const PrivateRoute = () => {
  const [hasSession, setHasSession] = useState(hasUsableSession());

  useEffect(() => {
    setHasSession(hasUsableSession());
  }, []);
  return hasSession ? <Outlet /> : <Navigate exact to={`/login`} />;
};

export default PrivateRoute;
