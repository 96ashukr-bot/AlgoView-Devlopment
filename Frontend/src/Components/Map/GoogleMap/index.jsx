import React, { Fragment } from "react";
import { Container, Row } from "reactstrap";
import { Breadcrumbs } from "../../../AbstractElements";
import PolylinesMapComp from "./Polylines";
import BasicMapComp from "./BasicMap";
import MarkerMapComp from "./MarkerMap";
import PolygonsComp from "./PolygonsMap";

const GoogleMaps = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle="Google Maps" parent="Maps" title="Google Maps" />
      <Container fluid={true}>
        <Row>
          <BasicMapComp />
          <PolygonsComp />
          <PolylinesMapComp />
          <MarkerMapComp />
        </Row>
      </Container>
    </Fragment>
  );
};

export default GoogleMaps;
