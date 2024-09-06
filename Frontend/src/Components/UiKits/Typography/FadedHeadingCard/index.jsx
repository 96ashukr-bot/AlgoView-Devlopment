import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { H3, H5 } from '../../../../AbstractElements';
import { Headings } from '../../../../Constant';

const FadedHeadingCard = () => {
  return (
    <Col sm="12">
      <Card>
        <CardHeader>
          <H5>{Headings}</H5><span>{'Use the included utility classNamees to recreate the small secondary heading text.'}  </span>
        </CardHeader>
        <CardBody className="typography">
          <H3>{'Fancy display heading'}<small className="text-muted">{'With faded secondary text'}</small></H3>
        </CardBody>
      </Card>
    </Col>
  );
};

export default FadedHeadingCard;