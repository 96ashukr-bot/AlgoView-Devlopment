import React, { Fragment, useEffect, useState } from "react";
import { Container, Row } from "reactstrap";
import { Breadcrumbs } from "../../../AbstractElements";
import { RotatingLines } from "react-loader-spinner";
import ClientHeader from "../../Application/Clients/Client/ClientHeader";
import GreetingCard from "./GreetingCard";
import WidgetsWrapper from "./WidgetsWraper";
import ClientAlert from "../../Application/Clients/Client/ClientAlert";

const Dashboard = () => {
  const [loading, setLoading] = useState(true);

  const userProfile = {
    role: {
      name: "client",
    },
  };

  const isClient = userProfile?.role?.name === "client";

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false);
    },);
    return () => clearTimeout(timer);
  }, []);

  return (
    <Fragment>
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
            <ClientHeader />
            {isClient && <GreetingCard userProfile={userProfile} />}
            <WidgetsWrapper />
            <ClientAlert />
          </Row>
        )}
      </Container>
    </Fragment>
  );
};

export default Dashboard;
