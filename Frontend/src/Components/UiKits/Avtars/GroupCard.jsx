import React from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { Image, LI, UL } from '../../../AbstractElements';
import { Groups } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';

const GroupCard = () => {
  return (
    <Col sm='12'>
      <Card>
        <HeaderCard title={Groups} />
        <CardBody className='avatar-showcase'>
          <div className='customers d-inline-block avatar-group'>
            <UL attrUL={{ as: 'ul', className: 'simple-list' }}>
              <LI attrLI={{ className: 'd-inline-block border-0' }}>
                <Image attrImage={{ body: true, className: 'img-70 rounded-circle', src: `${require('../../../assets/images/user/3.jpg')}`, alt: '' }} />
              </LI>
              <LI attrLI={{ className: 'd-inline-block border-0' }}>
                <Image attrImage={{ body: true, className: 'img-70 rounded-circle', src: `${require('../../../assets/images/user/5.jpg')}`, alt: '' }} />
              </LI>
              <LI attrLI={{ className: 'd-inline-block border-0' }}>
                <Image attrImage={{ body: true, className: 'img-70 rounded-circle', src: `${require('../../../assets/images/user/1.jpg')}`, alt: '' }} />
              </LI>
            </UL>
          </div>
          <div className='customers d-inline-block avatar-group'>
            <UL attrUL={{ as: 'ul', className: 'simple-list border-0' }}>
              <LI attrLI={{ className: 'd-inline-block border-0' }}>
                <Image attrImage={{ body: true, className: 'img-50 rounded-circle', src: `${require('../../../assets/images/user/3.jpg')}`, alt: '' }} />
              </LI>
              <LI attrLI={{ className: 'd-inline-block border-0' }}>
                <Image attrImage={{ body: true, className: 'img-50 rounded-circle', src: `${require('../../../assets/images/user/5.jpg')}`, alt: '' }} />
              </LI>
              <LI attrLI={{ className: 'd-inline-block border-0' }}>
                <Image attrImage={{ body: true, className: 'img-50 rounded-circle', src: `${require('../../../assets/images/user/1.jpg')}`, alt: '' }} />
              </LI>
            </UL>
          </div>
          <div className='customers d-inline-block avatar-group'>
            <UL attrUL={{ as: 'ul', className: 'simple-list border-0' }}>
              <LI attrLI={{ className: 'd-inline-block border-0' }}>
                <Image attrImage={{ body: true, className: 'img-40 rounded-circle', src: `${require('../../../assets/images/user/3.jpg')}`, alt: '' }} />
              </LI>
              <LI attrLI={{ className: 'd-inline-block border-0' }}>
                <Image attrImage={{ body: true, className: 'img-40 rounded-circle', src: `${require('../../../assets/images/user/5.jpg')}`, alt: '' }} />
              </LI>
              <LI attrLI={{ className: 'd-inline-block border-0' }}>
                <Image attrImage={{ body: true, className: 'img-40 rounded-circle', src: `${require('../../../assets/images/user/1.jpg')}`, alt: '' }} />
              </LI>
            </UL>
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default GroupCard;
