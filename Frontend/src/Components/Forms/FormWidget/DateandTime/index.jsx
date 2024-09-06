import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader, Col, Container, Row } from 'reactstrap';
import { Breadcrumbs, H5 } from '../../../../AbstractElements';
import DateTimeForm from './DateTimeForm';

const DateTimeContain = () => {
  return (
    <Fragment>
      <Breadcrumbs parent="Forms" title="Date and Time Picker" subParent='Form Widgets' mainTitle="Date and Time Picker" />
      <Container fluid={true}>
        <Card>
          <CardHeader>
            <H5>Date Time Picker</H5>
          </CardHeader>
          <CardBody>
            <Row>
              <Col md="12">
                <div className="datetime-picker">
                  <DateTimeForm />
                </div>
              </Col>
            </Row>
          </CardBody>
        </Card>
      </Container>
    </Fragment>
  );
};
export default DateTimeContain;