import React from 'react';
import { Card, CardBody, Col, Row } from 'reactstrap';
import { P } from '../../../../AbstractElements';
import { NestingColumn } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';

const NestingColCard = () => {

  return (
    <Col sm="12">
      <Card>
        <HeaderCard title={NestingColumn} />
        <CardBody className="grid-showcase">
          <P>{'Use flexbox alignment utilities to vertically and horizontally align columns.'}</P>
          <Row>
            <Col className="col-sm-9"><span>{'Level 1: .col-sm-9'}</span>
              <Row>
                <Col className="col-8 col-sm-6"><span>{'Level 2: .col-8 .col-sm-6'}</span></Col>
                <Col className="col-4 col-sm-6"><span>{'Level 2: .col-4 .col-sm-6'}</span></Col>
              </Row>
            </Col>
          </Row>
        </CardBody>
      </Card>
    </Col>
  );
};

export default NestingColCard;