import React, { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { getAccessToken, getRefreshToken } from "../Services/authStorage";

const PrivateRoute = () => {
  const [hasSession, setHasSession] = useState(Boolean(getAccessToken() || getRefreshToken()));

  useEffect(() => {
    setHasSession(Boolean(getAccessToken() || getRefreshToken()));
  }, []);
  return hasSession ? <Outlet /> : <Navigate exact to={`/login`} />;
};

export default PrivateRoute;
