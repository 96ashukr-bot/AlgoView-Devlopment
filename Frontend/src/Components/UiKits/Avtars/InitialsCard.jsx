import React from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { Image } from '../../../AbstractElements';
import { Initials } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';

const InitialsCard = () => {
  return (
    <Col xxl="6" sm="12 box-col-6">
      <Card>
        <HeaderCard title={Initials} />
        <CardBody className="avatar-showcase">
          <div className="avatars">
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-100 rounded-circle', src: `${require('../../../assets/images/user/16.png')}`, alt: '' }} /></div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-90 rounded-circle', src: `${require('../../../assets/images/user/16.png')}`, alt: '' }} /></div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-80 rounded-circle', src: `${require('../../../assets/images/user/16.png')}`, alt: '' }} /></div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-70 rounded-circle', src: `${require('../../../assets/images/user/16.png')}`, alt: '' }} /></div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-60 rounded-circle', src: `${require('../../../assets/images/user/16.png')}`, alt: '' }} /></div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-50 rounded-circle', src: `${require('../../../assets/images/user/16.png')}`, alt: '' }} /></div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-40 rounded-circle', src: `${require('../../../assets/images/user/16.png')}`, alt: '' }} /></div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-30 rounded-circle', src: `${require('../../../assets/images/user/16.png')}`, alt: '' }} /></div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-20 rounded-circle', src: `${require('../../../assets/images/user/16.png')}`, alt: '' }} /></div>
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default InitialsCard;