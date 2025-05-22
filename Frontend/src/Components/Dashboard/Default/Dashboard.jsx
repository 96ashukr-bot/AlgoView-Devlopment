import React, { Fragment } from "react";
import { Container, Row } from "reactstrap";
import { Breadcrumbs } from "../../../AbstractElements";
// import SuperDashboard from "./SuperDashboard";
import WidgetsWrapper1 from "./WidgetsWraper1";
import MarketDashboard from "./MarketDashboard";

const Dashboard = () => {
 
  return (
    <Fragment>
      <Breadcrumbs mainTitle="Default" parent="Dashboard" title="Default" />
      <Container fluid={true}>
        <Row className="widget-grid">
          {/* <SuperDashboard /> */}
          <WidgetsWrapper1/>
          <MarketDashboard />
        </Row>
      </Container>
    </Fragment>
  );
};

export default Dashboard;
