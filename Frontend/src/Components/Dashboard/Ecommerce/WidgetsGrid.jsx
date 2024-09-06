import React from 'react';
import {  Col, Row } from 'reactstrap';
import { SmallWidgetsData } from '../../../Data/Ecommerce';
import SmallWidgets from '../../Common/CommonWidgets/SmallWidgets';
import TotalBalance from './TotalBalance';

const WidgetsGrid = () => {
  return (
    <Col xxl='5' md='7' className='box-col-7'>
      <Row>
        <Col sm='12'>
          <TotalBalance />
        </Col>
        {SmallWidgetsData.map((data, i) => (
          <Col xs='6' key={i}>
            <SmallWidgets data={data} />
          </Col>
        ))}
      </Row>
    </Col>
  );
};

export default WidgetsGrid;
