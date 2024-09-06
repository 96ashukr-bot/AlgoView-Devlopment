import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H5 } from '../../../AbstractElements';
import { FollowersGrowth, WeeklyMonDropdown } from '../../../Constant';
import { GrowthChartData } from '../../../Data/DefaultDashboard/Chart';
import DropdownCommon from '../../Common/Dropdown';

const FollowerGrowth = () => {
  return (
    <Card className='card growth-wrap'>
      <CardHeader className='card-no-border'>
        <div className='header-top'>
          <H5>{FollowersGrowth}</H5>
          <DropdownCommon dropdownMain={{ className: 'icon-dropdown', direction: 'start' }} options={WeeklyMonDropdown} iconName='icon-more-alt' btn={{ tag: 'span' }} />
        </div>
      </CardHeader>
      <CardBody className='pt-0'>
        <div className='growth-wrapper'>
          <ReactApexChart height={200} type='line' options={GrowthChartData.options} series={GrowthChartData.series} />
        </div>
      </CardBody>
    </Card>
  );
};

export default FollowerGrowth;
