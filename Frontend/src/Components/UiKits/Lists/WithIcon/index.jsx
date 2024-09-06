import React from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { LI, UL } from '../../../../AbstractElements';
import { WithIcon } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';

const WithIcons = () => {
  return (
    <Col sm='12' xl='12'>
      <Card>
        <HeaderCard title={WithIcon} />
        <CardBody>
          <UL attrUL={{ className: 'simple-list border-0' }}>
            <LI attrLI={{ className: ' border-0 p-1 list-group-item-action', tag: 'a', href: '#javascript' }}>
              <i className='icon-save-alt me-2'></i>
              {'Cras justo odio'}
            </LI>
            <LI attrLI={{ className: 'border-0 p-1 list-group-item-action', tag: 'a', href: '#javascript' }}>
              <i className='icon-target me-2'></i>
              {'Dapibus ac facilisis in'}
            </LI>
            <LI attrLI={{ className: 'border-0 p-1 list-group-item-action', tag: 'a', href: '#javascript' }}>
              <i className='icon-mobile me-2'></i>
              {'Morbi leo risus'}
            </LI>
            <LI attrLI={{ className: 'border-0 p-1 list-group-item-action disabled' }}>
              <i className='icon-shopping-cart-full me-2'></i>
              {'Vestibulum at eros'}
            </LI>
          </UL>
        </CardBody>
      </Card>
    </Col>
  );
};

export default WithIcons;
