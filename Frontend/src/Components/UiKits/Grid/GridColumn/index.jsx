import React from 'react';
import { Card, CardBody, Col, Row } from 'reactstrap';
import { P } from '../../../../AbstractElements';
import { GridColumn } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';

const GridColumnCard = () => {
  return (
    <Col sm="12">
      <Card>
        <HeaderCard title={GridColumn} />
        <CardBody className="grid-showcase">
          <P>{'Using a single set of'} <code>{'.col-md-*'}</code> {'grid classes, you can create a basic grid system that starts out stacked on mobile devices and tablet devices (the extra small to small range) before becoming horizontal on desktop (medium) devices. Place grid columns within any'} <code>{'.row'}</code>.</P>
          <Row>
            <Col md="1 text-center"><span>{'col-md-1'}</span></Col>
            <Col md="2 text-center"><span>{'col-md-2'}</span></Col>
            <Col md="2 text-center"><span>{'col-md-2'}</span></Col>
            <Col md="3 text-center"><span>{'col-md-3'}</span></Col>
            <Col md="4 text-center"><span>{'col-md-4'}</span></Col>
            <Col md="5 text-center"><span>{'col-md-5'}</span></Col>
            <Col md="7 text-center"><span>{'col-md-7'}</span></Col>
            <Col md="6 text-center"><span>{'col-md-6'}</span></Col>
            <Col md="6 text-center"><span>{'col-md-6'}</span></Col>
            <Col md="8 text-center"><span>{'col-md-8'}</span></Col>
            <Col md="4 text-center"><span>{'col-md-4'}</span></Col>
            <Col md="9 text-center"><span>{'col-md-9'}</span></Col>
            <Col md="3 text-center"><span>{'col-md-3'}</span></Col>
            <Col md="10 text-center"><span>{'col-md-10'}</span></Col>
            <Col md="2 text-center"><span>{'col-md-2'}</span></Col>
            <Col md="12 text-center"><span>{'col-md-12'}</span></Col>
          </Row>
        </CardBody>
      </Card>
    </Col>
  );
};

export default GridColumnCard;