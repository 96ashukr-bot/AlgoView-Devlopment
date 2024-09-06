import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H5 } from '../../../AbstractElements';
import { DailyDropdown, ViewTitle } from '../../../Constant';
import { ViewChartOption } from '../../../Data/Social/Chart';
import DropdownCommon from '../../Common/Dropdown';

const Views = () => {
  return (
    <Card>
      <CardHeader className='card-header card-no-border'>
        <div className='header-top'>
          <H5 attrH5={{ className: 'm-0' }}>{ViewTitle}</H5>
          <div className='card-header-right-icon'>
            <DropdownCommon icon={false} options={DailyDropdown} btn={{ caret: true }} />
          </div>
        </div>
      </CardHeader>
      <CardBody className='pt-0'>
        <div className='view-container'>
          <ReactApexChart type='line' height={305} series={ViewChartOption.series} options={ViewChartOption.option} />
        </div>
      </CardBody>
    </Card>
  );
};

export default Views;
