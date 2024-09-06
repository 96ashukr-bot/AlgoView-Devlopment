import React, { Fragment } from "react";
import { Container, Row } from "reactstrap";
import { Breadcrumbs } from "../../../AbstractElements";
import Basic from "./Basic";
import Directions from "./Direction";
import HtmlElement from "./HtmlElement";
import Offset from "./Offset";

const Tooltips = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle="Tooltip" parent="Ui Kits" title="Tooltip" />
      <Container fluid={true}>
        <Row>
          <Basic />
          <Directions />
          <HtmlElement />
          <Offset />
        </Row>
      </Container>
    </Fragment>
  );
};

export default Tooltips;
