import React from 'react';
import { Card, CardBody, Col, Row } from 'reactstrap';
import { P } from '../../../../AbstractElements';
import { Offsets } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';

const OffsetCard = () => {
  return (
    <Col sm="12">
      <Card>
        <HeaderCard title={Offsets} />
        <CardBody className="grid-showcase">
          <P>{'Move columns to the right using'} <code>{'.offset-md-*'}</code> {'classes. These classes increase the left margin of a column by'} <code>{'*'}</code> {'columns. For example,'} <code>{'.offset-md-4'}</code> {'moves'} <code>{'.col-md-4'}</code> {'over four columns.'}</P>
          <Row>
            <Col md="4"><span>{'.col-md-4'}</span></Col>
            <Col md="4 offset-md-4"><span>{'.col-md-4 .offset-md-4'}</span></Col>
          </Row>
          <Row>
            <Col md="3 offset-md-3"><span>{'.col-md-3 .offset-md-3'}</span></Col>
            <Col md="3 offset-md-3"><span>{'.col-md-3 .offset-md-3'}</span></Col>
          </Row>
          <Row>
            <Col md="6 offset-md-3"><span>{'.col-md-6 .offset-md-3'}</span></Col>
          </Row>
          <Row>
            <Col sm="4" md="6"><span>{'.col-sm-5 .col-md-6'}</span></Col>
            <Col sm="4 offset-sm-2" md="6 offset-md-0"><span>{'.col-sm-5 .offset-sm-2 .col-md-6 .offset-md-0'}</span></Col>
          </Row>
          <Row>
            <Col sm="6" md="5" lg="6"><span>{'.col-sm-6 .col-md-5 .col-lg-6'}</span></Col>
            <Col sm="6" md="5 offset-md-2" lg="6 offset-lg-0"><span>{'.col-sm-6 .col-md-5 .offset-md-2 .col-lg-6 .offset-lg-0'}</span></Col>
          </Row>
        </CardBody>
      </Card>
    </Col>
  );
};

export default OffsetCard;