import React from 'react';
import { Col, Row } from 'reactstrap';
import { RadialProgressWidgetData } from '../../../Data/Crypto';
import RadialProgressWidget from '../../Common/CommonWidgets/RadialProgressWidget';
import GreetingCard from './GreetingCard';

import Transactions from './Transactions';

const LeftGrid = () => {
  return (
    <Col xxl='3' xl='4' className='box-col-4'>
      <Row>
        <Col xl='12' sm='6'>
          <GreetingCard />
        </Col>
        {RadialProgressWidgetData.map((item, i) => (
          <Col key={i} xl='12' sm='6'>
            <RadialProgressWidget chartHeight={150} data={item} />
          </Col>
        ))}
        <Col sm='12'>
          <Transactions />
        </Col>
      </Row>
    </Col>
  );
};

export default LeftGrid;
