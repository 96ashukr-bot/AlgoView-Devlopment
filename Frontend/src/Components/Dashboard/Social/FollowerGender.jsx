import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H5 } from '../../../AbstractElements';
import { DailyDropdown, FollowerGenderTitle } from '../../../Constant';
import { FollowerGenderChart } from '../../../Data/Social/Chart';
import DropdownCommon from '../../Common/Dropdown';

const FollowerGender = () => {
  return (
    <Card>
      <CardHeader className='card-no-border'>
        <div className='header-top gap-1'>
          <H5>{FollowerGenderTitle}</H5>
          <DropdownCommon dropdownMain={{ className: 'icon-dropdown', direction: 'start' }} options={DailyDropdown} iconName='icon-more-alt' btn={{ tag: 'span' }} />
        </div>
      </CardHeader>
      <CardBody className='pt-0'>
        <div className='follower-chart'>
          <ReactApexChart width={325} height={325} type='radialBar' series={FollowerGenderChart.series} options={FollowerGenderChart.options} />
        </div>
      </CardBody>
    </Card>
  );
};

export default FollowerGender;
