import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H5 } from '../../../AbstractElements';
import { DailyDropdown, InstagramSubscribers, InstaGrowth } from '../../../Constant';
import { InstagramSubscriptionChart } from '../../../Data/Social/Chart';
import DropdownCommon from '../../Common/Dropdown';

const InstagramSubscription = () => {
  return (
    <Card>
      <CardHeader className='card-no-border'>
        <div className='header-top'>
          <H5 attrH5={{ className: 'm-0' }}>
            {InstagramSubscribers}
            <span className='f-14 f-w-500 ms-1 f-light'>({InstaGrowth})</span>
          </H5>
          <div className='card-header-right-icon'>
            <DropdownCommon dropdownMain={{ className: 'icon-dropdown', direction: 'start' }} options={DailyDropdown} iconName='icon-more-alt' btn={{ tag: 'span' }} />
          </div>
        </div>
      </CardHeader>
      <CardBody className='pt-0'>
        <div className='subscriber-chart-container'>
          <ReactApexChart height={265} type='line' options={InstagramSubscriptionChart.options} series={InstagramSubscriptionChart.series} />
        </div>
      </CardBody>
    </Card>
  );
};

export default InstagramSubscription;
