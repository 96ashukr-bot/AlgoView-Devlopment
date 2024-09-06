import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { H5 } from '../../../../AbstractElements';

const CommonHeaderClass = (props) => {
  return (
    <Col xl="6" lg="12" md="6">
      <Card>
        <CardHeader>
          <H5>{props.title}</H5>
        </CardHeader>
        <CardBody>
          <pre className="helper-classes">
            {props.children}
          </pre>
        </CardBody>
      </Card>
    </Col>
  );
};

export default CommonHeaderClass;