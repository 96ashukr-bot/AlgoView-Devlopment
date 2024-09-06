import React from 'react';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H5 } from '../../../AbstractElements';
import { FollowersGrowth, WeeklyMonDropdown } from '../../../Constant';
import { GrowthChartData, GrowthChartDataResponsive } from '../../../Data/DefaultDashboard/Chart';

import ReactApexChart from 'react-apexcharts';
import DropdownCommon from '../../Common/Dropdown';

const FollowerGrowth = () => {
  const updatedChartData = {
    ...GrowthChartData,
    options: {
      ...GrowthChartData.options,
      ...GrowthChartDataResponsive,
    },
  };
  return (
    <Card className='card growth-wrap'>
      <CardHeader className='card-no-border pb-0'>
        <div className='header-top'>
          <H5>{FollowersGrowth}</H5>
          <DropdownCommon dropdownMain={{ className: 'icon-dropdown', direction: 'start' }} options={WeeklyMonDropdown} iconName='icon-more-alt' btn={{ tag: 'span' }} />
        </div>
      </CardHeader>
      <CardBody>
        <div className='growth-wrapper'>
          <ReactApexChart height={135} type='line' options={updatedChartData.options} series={updatedChartData.series} />
        </div>
      </CardBody>
    </Card>
  );
};

export default FollowerGrowth;
