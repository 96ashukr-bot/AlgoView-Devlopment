import React from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { LI, UL } from '../../../../AbstractElements';
import { FlushStyle } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';

const FlushStyles = () => {
  return (
    <Col sm='12' xl='12'>
      <Card>
        <HeaderCard title={FlushStyle} />
        <CardBody>
          <UL attrUL={{ className: 'simple-list border-0 list-group-flush' }}>
            <LI attrLI={{ className: 'border-0 p-2' }}>{'Cras justo odio'}</LI>
            <LI attrLI={{ className: 'border-0 p-2' }}>{'Dapibus ac facilisis in'}</LI>
            <LI attrLI={{ className: 'border-0 p-2' }}>{'Morbi leo risus'}</LI>
            <LI attrLI={{ className: 'border-0 p-2' }}>{'Porta ac consectetur ac'}</LI>
            <LI attrLI={{ className: 'border-0 p-2' }}>{'Vestibulum at eros'}</LI>
            <LI attrLI={{ className: 'border-0 p-2' }}>{'Cras justo odio'}</LI>
            <LI attrLI={{ className: 'border-0 p-2' }}>{'Dapibus ac facilisis in'}</LI>
            <LI attrLI={{ className: 'border-0 p-2' }}>{'Dapibus ac facilisis in'}</LI>
            <LI attrLI={{ className: 'border-0 p-2' }}>{'Dapibus ac facilisis in'}</LI>
          </UL>
        </CardBody>
      </Card>
    </Col>
  );
};

export default FlushStyles;
