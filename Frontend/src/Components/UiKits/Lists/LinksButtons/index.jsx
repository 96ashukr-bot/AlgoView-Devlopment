import React from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { LI, UL } from '../../../../AbstractElements';
import { LinksAndButtons } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';

const LinksButtons = () => {
  return (
    <Col sm='12' xl='12'>
      <Card>
        <HeaderCard title={LinksAndButtons} />
        <CardBody>
          <UL attrUL={{ className: 'border-0 simple-list' }}>
            <LI attrLI={{ className: 'border-0 list-group-item-action p-2', tag: 'a', href: '#javascript', active: true }}>{'Cras justo odio'}</LI>
            <LI attrLI={{ className: 'border-0 list-group-item-action p-2', tag: 'a', href: '#javascript' }}>{'Dapibus ac facilisis in'}</LI>
            <LI attrLI={{ className: 'border-0 list-group-item-action p-2', tag: 'a', href: '#javascript' }}>{'Morbi leo risus'}</LI>
            <LI attrLI={{ className: 'border-0 list-group-item-action p-2', tag: 'a', href: '#javascript' }}>{'Porta ac consectetur ac'}</LI>
            <LI attrLI={{ className: 'border-0 list-group-item-action p-2', tag: 'a', href: '#javascript', disabled: true }}>{'Vestibulum at eros'}</LI>
          </UL>
        </CardBody>
      </Card>
    </Col>
  );
};

export default LinksButtons;
