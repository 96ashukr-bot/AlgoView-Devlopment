import React from 'react';
import { Card, CardBody, Col, Row } from 'reactstrap';
import { P } from '../../../../AbstractElements';
import { VerticalAlignment } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';

const VerticalAlignCard = () => {
  return (
    <Col sm="12">
      <Card>
        <HeaderCard title={VerticalAlignment} />
        <CardBody className="grid-showcase grid-align">
          <P>{'Use flexbox alignment utilities to vertically and horizontally align columns.'}</P>
          <Row>
            <Col className="col align-self-start"><span>{'One of three columns'}</span></Col>
            <Col className="col align-self-center"><span>{'One of three columns'}</span></Col>
            <Col className="col align-self-end"><span>{'One of three columns'}</span></Col>
          </Row>
          <Row className="align-items-start">
            <Col className="col"><span>{'One of three columns'}</span></Col>
            <Col className="col"><span>{'One of three columns'}</span></Col>
            <Col className="col"><span>{'One of three columns'}</span></Col>
          </Row>
          <Row className="align-items-center">
            <Col className="col"><span>{'One of three columns'}</span></Col>
            <Col className="col"><span>{'One of three columns'}</span></Col>
            <Col className="col"><span>{'One of three columns'}</span></Col>
          </Row>
          <Row className="align-items-end">
            <Col className="col"><span>{'One of three columns'}</span></Col>
            <Col className="col"><span>{'One of three columns'}</span></Col>
            <Col className="col"><span>{'One of three columns'}</span></Col>
          </Row>
        </CardBody>
      </Card>
    </Col>
  );
};

export default VerticalAlignCard;