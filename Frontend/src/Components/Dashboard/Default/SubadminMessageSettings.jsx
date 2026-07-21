import React, { Fragment } from "react";
import { Container, Row } from "reactstrap";
import { Breadcrumbs } from "../../../AbstractElements";
import SubadminAnnouncement from "./SubadminAnnouncement";

const SubadminMessageSettings = () => (
  <Fragment>
    <Breadcrumbs mainTitle="Subadmin Message" parent="Settings" title="Subadmin Message" />
    <Container fluid>
      <Row>
        <SubadminAnnouncement mode="settings" />
      </Row>
    </Container>
  </Fragment>
);

export default SubadminMessageSettings;
