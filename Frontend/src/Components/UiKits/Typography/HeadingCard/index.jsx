import React from 'react';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';
import { H5 } from '../../../../AbstractElements';
import { Headings } from '../../../../Constant';
import HeadingTag from './HeadingTag';
import SubHeadings from './SubHeading';

const HeadingCard = () => (
  <Col sm="12">
    <Card>
      <CardHeader>
        <H5>{Headings}</H5><span>{'All HTML headings'}, <code>&lt;h1&gt;</code> {'through'} <code>&lt;{'h6'}&gt;</code>, {'are available'}.</span>
      </CardHeader>
      <CardBody className="typography">
        <Row>
          <Col sm="12" xl="6">
            <HeadingTag />
          </Col>
          <Col sm="12" xl="6">
            <SubHeadings />
          </Col>
        </Row>
      </CardBody>
    </Card>
  </Col>
);

export default HeadingCard;