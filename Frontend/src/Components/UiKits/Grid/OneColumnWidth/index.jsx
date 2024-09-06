import React from 'react';
import { Card, CardBody, Col, Row } from 'reactstrap';
import { P } from '../../../../AbstractElements';
import HeaderCard from '../../../Common/Component/HeaderCard';

const OneColumnWidthCard = () => {
  return (
    <Col sm="12">
      <Card>
        <HeaderCard title={'Setting one column width'} />
        <CardBody className="grid-showcase">
          <P>{'Auto-layout for flexbox grid columns also means you can set the width of one column and have the sibling columns automatically resize around it. You may use predefined grid classes (as shown below), grid mixins, or inline widths. Note that the other columns will resize no matter the width of the center column.'}</P>
          <Row>
            <Col className="col"><span>{'1 of 3'}</span></Col>
            <Col className="col-6"><span>{'2 of 3 (wider)'}</span></Col>
            <Col className="col"><span> {'3 of 3'}</span></Col>
          </Row>
          <Row>
            <Col className="col"><span>{'1 of 3'}</span></Col>
            <Col className="col-5"><span> {'2 of 3 (wider)'}</span></Col>
            <Col className="col"><span>{'3 of 3'}</span></Col>
          </Row>
        </CardBody>
      </Card>
    </Col>
  );
};

export default OneColumnWidthCard;