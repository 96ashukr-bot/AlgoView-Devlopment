import React from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { Image } from '../../../AbstractElements';
import { Shape } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';

const ShapeCard = () => {
  return (
    <Col xxl="6" sm="12 box-col-6">
      <Card>
        <HeaderCard title={Shape} />
        <CardBody className="avatar-showcase">
          <div className="avatars">
            <div className="avatar">
              <Image attrImage={{ body: true, className: 'img-100 b-r-8', src: `${require('../../../assets/images/user/1.jpg')}`, alt: '#' }} />
            </div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-90 b-r-30', src: `${require('../../../assets/images/user/1.jpg')}`, alt: '#' }} /></div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-80 b-r-35', src: `${require('../../../assets/images/user/1.jpg')}`, alt: '#' }} /></div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-70 rounded-circle', src: `${require('../../../assets/images/user/1.jpg')}`, alt: '#' }} /></div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-60 b-r-25', src: `${require('../../../assets/images/user/1.jpg')}`, alt: '#' }} /></div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-50 b-r-15', src: `${require('../../../assets/images/user/1.jpg')}`, alt: '#' }} /></div>
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default ShapeCard;