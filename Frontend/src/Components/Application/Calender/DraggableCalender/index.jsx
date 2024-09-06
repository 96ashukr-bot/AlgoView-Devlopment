import { Breadcrumbs } from "../../../../AbstractElements";
import { Dragging_Event } from "../../../../Constant";
import DragCalendar from "./DragCalendar";
import { Card, CardBody, Col, Container, Row } from "reactstrap";
import React, { Fragment } from "react";
import HeaderCard from "../../../Common/Component/HeaderCard";

const DraggableContain = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle="Dragable Calender" parent="Apps" title="Dragable Calender" />
      <Container fluid={true} className="calendar-basic">
        <Row>
          <Col sm="12">
            <Card>
              <HeaderCard title={Dragging_Event} />
              <CardBody>
                <div className="basic-calendar">
                  <Row>
                    <DragCalendar />
                  </Row>
                </div>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};
export default DraggableContain;
