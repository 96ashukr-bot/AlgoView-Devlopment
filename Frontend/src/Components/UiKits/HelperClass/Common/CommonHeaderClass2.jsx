import React from 'react';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H5 } from '../../../../AbstractElements';

const CommonHeaderClass = (props) => {
  return (
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
  );
};

export default CommonHeaderClass;