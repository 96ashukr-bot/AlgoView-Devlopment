import React from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { LI, UL } from '../../../../AbstractElements';
import { DefaultList } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';

const DefaultLists = () => {
  return (
    <Col sm='12' xl='12'>
      <Card>
        <HeaderCard title={DefaultList} />
        <CardBody>
          <UL attrUL={{ className: 'simple-list border-0 list-default' }}>
            <LI attrLI={{ className: 'border-0' }}>{'Cras justo odio'}</LI>
            <LI attrLI={{ className: 'border-0' }}>{'Dapibus ac facilisis in'}</LI>
            <LI attrLI={{ className: 'border-0' }}>{'Morbi leo risus'}</LI>
            <LI attrLI={{ className: 'border-0' }}>{'Porta ac consectetur ac'}</LI>
            <LI attrLI={{ className: 'border-0' }}>{'Vestibulum at eros'}</LI>
          </UL>
        </CardBody>
      </Card>
    </Col>
  );
};

export default DefaultLists;
