import React from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { H5, LI, P, UL } from '../../../../AbstractElements';
import { CustomContent, CustomcontentText, CustomcontentText2, Daysago, ListGrouphead } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';

const CustomContents = () => {
  return (
    <Col sm='12' xl='12'>
      <Card>
        <HeaderCard title={CustomContent} />
        <CardBody>
          <UL attrUL={{ className: 'bgcolor simple-list' }}>
            <LI attrLI={{ className: 'p-2 border-0 list-group-item-action flex-column align-items-start active' }}>
              <div className='d-flex w-100 justify-content-between'>
                <H5 attrH5={{ className: 'mb-1' }}>{ListGrouphead}</H5>
                <small>{Daysago}</small>
              </div>
              <P attrPara={{ className: 'mb-1' }}>{CustomcontentText}</P>
              <small>{CustomcontentText2}</small>
            </LI>
            <LI attrLI={{ className: 'p-2 border-0 list-group-item-action flex-column align-items-start ' }}>
              <div className='d-flex w-100 justify-content-between'>
                <H5 attrH5={{ className: 'mb-1' }}>{ListGrouphead}</H5>
                <small className='text-muted'>{Daysago}</small>
              </div>
              <P attrPara={{ className: 'mb-1' }}>{CustomcontentText}</P>
              <small className='text-muted'>{CustomcontentText2}</small>
            </LI>
            <LI attrLI={{ className: 'p-2 border-0 list-group-item-action flex-column align-items-start ' }}>
              <div className='d-flex w-100 justify-content-between'>
                <H5 attrH5={{ className: 'mb-1' }}>{ListGrouphead}</H5>
                <small className='text-muted'>{Daysago}</small>
              </div>
              <P attrPara={{ className: 'mb-1' }}>{CustomcontentText}</P>
              <small className='text-muted'>{CustomcontentText2}</small>
            </LI>
          </UL>
        </CardBody>
      </Card>
    </Col>
  );
};

export default CustomContents;
