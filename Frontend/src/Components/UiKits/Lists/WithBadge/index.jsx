import React from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { LI, UL } from '../../../../AbstractElements';
import { WithBadges } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';

const WithBadge = () => {
  return (
    <Col sm='12' xl='12'>
      <Card>
        <HeaderCard title={WithBadges} />
        <CardBody>
          <UL attrUL={{ className: 'simple-list border-0' }}>
            <LI attrLI={{ className: 'd-flex border-0 p-1 justify-content-between align-items-center' }}>
              {'Cras justo odio'}
              <span className='badge badge-primary counter digits'>{'14'}</span>
            </LI>
            <LI attrLI={{ className: 'd-flex border-0 p-1 justify-content-between align-items-center' }}>
              {'Dapibus ac facilisis in'}
              <span className='badge badge-secondary counter digits'>{'2'}</span>
            </LI>
            <LI attrLI={{ className: 'd-flex border-0 p-1 justify-content-between align-items-center' }}>
              {'Morbi leo risus'}
              <span className='badge badge-success rounded-pill counter digits'>{'1'}</span>
            </LI>
            <LI attrLI={{ className: 'd-flex border-0 p-1 justify-content-between align-items-center' }}>
              {'Dapibus ac facilisis in'}
              <span className='badge badge-info rounded-pill digits'>{'100%'}</span>
            </LI>
            <LI attrLI={{ className: 'd-flex border-0 p-1 justify-content-between align-items-center' }}>
              {'Dapibus ac facilisis in'}
              <span className='badge badge-warning counter digits'>{'2'}</span>
            </LI>
            <LI attrLI={{ className: 'd-flex border-0 p-1 justify-content-between align-items-center' }}>
              {'Morbi leo risus'}
              <span className='badge badge-danger rounded-pill digits'>{'sale'}</span>
            </LI>
            <LI attrLI={{ className: 'd-flex border-0 p-1 justify-content-between align-items-center' }}>
              {'Cras justo odio'}
              <span className='badge badge-light txt-dark counter digits'>{'14'}</span>
            </LI>
          </UL>
        </CardBody>
      </Card>
    </Col>
  );
};

export default WithBadge;
