import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardBody, Col } from 'reactstrap';
import { H6 } from '../../../AbstractElements';
import { PurchaseNow } from '../../../Constant';

import purchase from '../../../assets/images/dashboard/purchase.png';

const PreAccountCard = () => {
  return (
    <Col xxl='3' md='6' className='box-col-6 col-ed-none wow zoomIn'>
      <Card className='purchase-card'>
        <img className='img-fluid' src={purchase} alt='vector mens with leptop' />
        <CardBody className='pt-3'>
          <H6 attrH6={{ className: 'mb-3' }}>
            Buy <a href='#javascript'>Pro Account </a>to Explore Primium Features
          </H6>
          <Link className='purchase-btn btn btn-primary btn-hover-effect f-w-500' to='https://1.envato.market/3GVzd' target='_blank'>
            {PurchaseNow}
          </Link>
        </CardBody>
      </Card>
    </Col>
  );
};

export default PreAccountCard;
