import React from 'react';
import { Col, Row } from 'reactstrap';

import LightCardBox from './LightCardBox';

const LightCard = ({ LightCardData }) => {
  return (
    <Col xl='3' md='12' sm='5' className='p-0'>
      <Row className='g-sm-4 g-2'>
        {LightCardData.map((data, i) => (
          <Col key={i} xl='12' md='4'>
            <LightCardBox data={data} />
          </Col>
        ))}
      </Row>
    </Col>
  );
};

export default LightCard;
