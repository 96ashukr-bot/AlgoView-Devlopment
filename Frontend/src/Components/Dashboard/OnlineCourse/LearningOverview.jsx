import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H5 } from '../../../AbstractElements';
import { DailyDropdown, LearningOverviewGrowth, LearningOverviewTitle } from '../../../Constant';
import { LearningOverviewChartData } from '../../../Data/OnlineCourse/ChartData';
import DropdownCommon from '../../Common/Dropdown';

const LearningOverview = () => {
  return (
    <Card>
      <CardHeader className='card-no-border'>
        <div className='header-top'>
          <H5 className='m-0'>
            {LearningOverviewTitle}
            <span className='f-14 f-w-500 ms-1 f-light'>({LearningOverviewGrowth})</span>
          </H5>
          <div className='card-header-right-icon'>
            <DropdownCommon dropdownMain={{ className: 'icon-dropdown', direction: 'start' }} options={DailyDropdown} iconName='icon-more-alt' btn={{ tag: 'span' }} />
          </div>
        </div>
      </CardHeader>
      <CardBody className='pt-0'>
        <div className='learning-wrap'>
          <ReactApexChart type='line' height={315} options={LearningOverviewChartData.options} series={LearningOverviewChartData.series} />
        </div>
      </CardBody>
    </Card>
  );
};

export default LearningOverview;
