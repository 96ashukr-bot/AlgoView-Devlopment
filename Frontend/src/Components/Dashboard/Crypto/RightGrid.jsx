import React from 'react';
import { Col, Row } from 'reactstrap';
import Activities from './Activities';
import MyPortfolio from './MyPortfolio';
import YourBalanceCard from '../../Common/CommonWidgets/YourBalanceCard';

const RightGrid = () => {
  return (
    <Col xxl='3' className='box-col-12'>
      <Row className='box-order'>
        <Col xxl='12' sm='6' className='box-col-6'>
          <YourBalanceCard />
        </Col>
        <Col xxl='12' className='order-xxl-0 order-1'>
          <MyPortfolio />
        </Col>
        <Col xxl='12' sm='6' className='box-col-6'>
          <Activities />
        </Col>
      </Row>
    </Col>
  );
};

export default RightGrid;
