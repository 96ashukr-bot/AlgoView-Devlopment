import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { H5, H6, UL, LI, P } from '../../../AbstractElements';
import { Activity, DailyDropdown } from '../../../Constant';
import { ActivityData } from '../../../Data/DefaultDashboard';
import DropdownCommon from '../../Common/Dropdown';

const ActivityCard = () => {
  return (
    <Col xxl='4' xl='5' md='6' sm='7' className='notification box-col-6'>
      <Card className='height-equal'>
        <CardHeader className='card-no-border'>
          <div className='header-top'>
            <H5 attrH5={{ className: 'm-0' }}>{Activity}</H5>
            <div className='card-header-right-icon'>
              <DropdownCommon icon={false} options={DailyDropdown} btn={{ caret: true }} />
            </div>
          </div>
        </CardHeader>
        <CardBody className='pt-0'>
          <UL>
            {ActivityData.map((item, i) => (
              <LI key={i} attrLI={{ className: 'd-flex' }}>
                <div className={`activity-dot-${item.color}`} />
                <div className='w-100 ms-3'>
                  <P attrPara={{ className: 'd-flex justify-content-between mb-2' }}>
                    <span className='date-content light-background'>{item.subTitle}</span>
                    <span>{item.time}</span>
                  </P>
                  <H6>
                    {item.title}
                    <span className='dot-notification' />
                  </H6>
                  <p className='f-light'>{item.dis}</p>
                </div>
              </LI>
            ))}
          </UL>
        </CardBody>
      </Card>
    </Col>
  );
};

export default ActivityCard;
