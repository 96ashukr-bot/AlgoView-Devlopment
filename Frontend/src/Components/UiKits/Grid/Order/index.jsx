import React from 'react';
import { Card, CardBody, Col, Row } from 'reactstrap';
import { P } from '../../../../AbstractElements';
import { Order } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';

const OrderCard = () => {

  return (
    <Col sm="12">
      <Card>
        <HeaderCard title={Order} />
        <CardBody className="grid-showcase">
          <P>{'Use'} <code>{'.order-'}</code> {'classNamees for controlling the'} <strong>{'visual order'}</strong> {'of your content. These classNamees are responsive, so you can set the'} <code>{'order'}</code> {'by breakpoint (e.g.,'} <code>{'.order-1.order-md-2'}</code>{'). Includes support for'} <code>{'1'}</code> {'through'} <code>{'12'}</code> {'across all five grid tiers.'}</P>
          <Row>
            <Col className="col"><span>{'First, but unordered'}</span></Col>
            <Col className="col order-12"><span>{'Second, but last'}</span></Col>
            <Col className="col order-1"><span>{'Third, but first'}</span></Col>
          </Row>
          <Row>
            <Col className="col order-last"><span>{'First, but last'}</span></Col>
            <Col className="col"><span>{'Second, but unordered'}</span></Col>
            <Col className="col order-first"><span>{'Third, but first'}</span></Col>
          </Row>
        </CardBody>
      </Card>
    </Col>
  );
};

export default OrderCard;