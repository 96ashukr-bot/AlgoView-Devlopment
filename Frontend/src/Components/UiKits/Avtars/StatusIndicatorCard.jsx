import React from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { Image } from '../../../AbstractElements';
import { StatusIndicator } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';

const StatusIndicatorCard = () => {
  return (
    <Col xxl="6" sm="12 box-col-6">
      <Card>
        <HeaderCard title={StatusIndicator} />
        <CardBody className="avatar-showcase">
          <div className="avatars">
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-100 rounded-circle', src: `${require('../../../assets/images/user/1.jpg')}`, alt: '#' }} />
              <div className="status status-100 bg-success"> </div>
            </div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-90 rounded-circle', src: `${require('../../../assets/images/user/1.jpg')}`, alt: '#' }} />
              <div className="status status-90"></div>
            </div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-80 rounded-circle', src: `${require('../../../assets/images/user/1.jpg')}`, alt: '#' }} />
              <div className="status status-80 bg-success"></div>
            </div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-70 rounded-circle', src: `${require('../../../assets/images/user/1.jpg')}`, alt: '#' }} />
              <div className="status status-70"></div>
            </div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-60 rounded-circle', src: `${require('../../../assets/images/user/1.jpg')}`, alt: '#' }} />
              <div className="status status-60 bg-success"></div>
            </div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-50 rounded-circle', src: `${require('../../../assets/images/user/1.jpg')}`, alt: '#' }} />
              <div className="status status-50"> </div>
            </div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-40 rounded-circle', src: `${require('../../../assets/images/user/1.jpg')}`, alt: '#' }} />
              <div className="status status-40"></div>
            </div>
            <div className="avatar"><Image attrImage={{ body: true, className: 'img-30 rounded-circle', src: `${require('../../../assets/images/user/1.jpg')}`, alt: '#' }} />
              <div className="status status-30"></div>
            </div>
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default StatusIndicatorCard;