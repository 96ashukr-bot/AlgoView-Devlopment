import React from 'react';
import { Card, CardBody, Col, Row } from 'reactstrap';
import { P } from '../../../../AbstractElements';
import { HorizontalAlignment } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';

const HorizontalAlignCard = () => {
  return (
    <Col sm="12">
      <Card>
        <HeaderCard title={HorizontalAlignment} />
        <CardBody className="grid-showcase grid-align">
          <P>{'Use flexbox alignment utilities to vertically and horizontally align columns.'}</P>
          <Row className="justify-content-start">
            <Col className="col-4"><span>{'One of two columns'}</span></Col>
            <Col className="col-4"><span>{'One of two columns'}</span></Col>
          </Row>
          <Row className="justify-content-center">
            <Col className="col-4"><span>{'One of two columns'}</span></Col>
            <Col className="col-4"><span>{'One of two columns'}</span></Col>
          </Row>
          <Row className="justify-content-end">
            <Col className="col-4"><span>{'One of two columns'}</span></Col>
            <Col className="col-4"><span>{'One of two columns'}</span></Col>
          </Row>
          <Row className="justify-content-around">
            <Col className="col-4"><span>{'One of two columns'}</span></Col>
            <Col className="col-4"><span>{'One of two columns'}</span></Col>
          </Row>
          <Row className="justify-content-between">
            <Col className="col-4"><span>{'One of two columns'}</span></Col>
            <Col className="col-4"><span>{'One of two columns'}</span></Col>
          </Row>
        </CardBody>
      </Card>
    </Col>
  );
};

export default HorizontalAlignCard;