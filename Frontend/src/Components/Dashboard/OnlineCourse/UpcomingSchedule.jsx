import React from 'react';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H5, Btn } from '../../../AbstractElements';
import { Create, UpcomingScheduleTitle } from '../../../Constant';
import { ScheduleListData } from '../../../Data/OnlineCourse';
import ScheduleListBox from './ScheduleListBox';

const UpcomingSchedule = () => {
  return (
    <Card className='schedule-card'>
      <CardHeader className='card-no-border'>
        <div className='header-top'>
          <H5 attrH5={{ className: 'm-0' }}>{UpcomingScheduleTitle}</H5>
          <div className='card-header-right-icon'>
            <Btn attrBtn={{ color: 'light-primary', className: 'btn badge-light-primary' }}>+ {Create}</Btn>
          </div>
        </div> 
      </CardHeader>
      <CardBody className='pt-0'>
        <ScheduleListBox data={ScheduleListData} />
      </CardBody>
    </Card>
  );
};

export default UpcomingSchedule;
