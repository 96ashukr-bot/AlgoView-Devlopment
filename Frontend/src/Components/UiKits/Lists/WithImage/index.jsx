import React from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { Image, LI, UL } from '../../../../AbstractElements';
import { WithImages } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';

const WithImage = () => {
  return (
    <Col sm='12' xl='12'>
      <Card>
        <HeaderCard title={WithImages} />
        <CardBody>
          <UL attrUL={{ className: 'simple-list border-0' }}>
            <LI attrLI={{ className: 'border-0 p-1 list-group-item-action', tag: 'a', href: '#javascript' }}>
              <Image attrImage={{ className: 'img-40', body: true, src: `${require('../../../../assets/images/user/1.jpg')}`, alt: '' }} />
              {'Cras justo odio'}
            </LI>
            <LI attrLI={{ className: 'border-0 p-1 list-group-item-action', tag: 'a', href: '#javascript' }}>
              <Image attrImage={{ className: 'img-40', body: true, src: `${require('../../../../assets/images/user/1.jpg')}`, alt: '' }} />
              {'Dapibus ac facilisis in'}
            </LI>
            <LI attrLI={{ className: 'border-0 p-1 list-group-item-action', tag: 'a', href: '#javascript' }}>
              <Image attrImage={{ className: 'img-40', body: true, src: `${require('../../../../assets/images/user/1.jpg')}`, alt: '' }} />
              {'Dapibus ac facilisis in'}
            </LI>
            <LI attrLI={{ className: 'border-0 p-1 list-group-item-action disabled' }}>
              <Image attrImage={{ className: 'img-40', body: true, src: `${require('../../../../assets/images/user/1.jpg')}`, alt: '' }} />
              {'Dapibus ac facilisis in'}
            </LI>
          </UL>
        </CardBody>
      </Card>
    </Col>
  );
};

export default WithImage;
