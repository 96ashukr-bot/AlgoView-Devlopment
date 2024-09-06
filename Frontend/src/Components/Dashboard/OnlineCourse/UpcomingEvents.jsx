import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H5 } from '../../../AbstractElements';
import { DailyDropdown, UpcomingEventsTitle } from '../../../Constant';
import { UpcomingOptionsChartData } from '../../../Data/OnlineCourse/ChartData';
import DropdownCommon from '../../Common/Dropdown';

const UpcomingEvents = () => {
  return (
    <Card>
      <CardHeader className='card-no-border'>
        <div className='header-top'>
          <H5>{UpcomingEventsTitle}</H5>
          <DropdownCommon dropdownMain={{ className: 'icon-dropdown', direction: 'start' }} options={DailyDropdown} iconName='icon-more-alt' btn={{ tag: 'span' }} />
        </div>
      </CardHeader>
      <CardBody className='pt-0'>
        <div className='upcoming-event-wrap'>
          <ReactApexChart height={305} type='rangeBar' options={UpcomingOptionsChartData.options} series={UpcomingOptionsChartData.series} />
        </div>
      </CardBody>
    </Card>
  );
};

export default UpcomingEvents;
