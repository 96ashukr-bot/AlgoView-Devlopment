import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H5 } from '../../../AbstractElements';
import { TodayProgressMessage, TodayProgressTitle } from '../../../Constant';
import { todayProgressData } from '../../../Data/OnlineCourse/ChartData';

const TodayProgress = () => {
  return (
    <Card className='get-card'>
      <CardHeader className='card-no-border'>
        <H5>{TodayProgressTitle}</H5>
        <span className='f-14 f-w-500 f-light'>{TodayProgressMessage}</span>
      </CardHeader>
      <CardBody className='pt-0'>
        <div className='progress-chart-wrap'>
          <ReactApexChart type='radialBar' width={240} height={360} options={todayProgressData.options} series={todayProgressData.series} />
        </div>
      </CardBody>
    </Card>
  );
};

export default TodayProgress;
