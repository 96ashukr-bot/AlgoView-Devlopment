import React, { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";

const PrivateRoute = () => {
  const [login, setLogin] = useState(JSON.parse(localStorage.getItem("login")));
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    setAuthenticated(JSON.parse(localStorage.getItem("authenticated")));
    localStorage.setItem("authenticated", authenticated);
    localStorage.setItem("login", login);
  }, []);
  return login || authenticated ? <Outlet /> : <Navigate exact to={`/login`} />;
};

export default PrivateRoute;
