import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H5 } from '../../../AbstractElements';
import { MonthlyProfitsGrowth, MonthlyProfitsTitle } from '../../../Constant';
import { MonthlyProfitsChartData } from '../../../Data/Ecommerce/Chart';

const MonthlyProfits = () => {
  return (
    <Card>
      <CardHeader className='card-no-border'>
        <H5>{MonthlyProfitsTitle}</H5>
        <span className='f-light f-w-500 f-14'>({MonthlyProfitsGrowth})</span>
      </CardHeader>
      <CardBody className='pt-0'>
        <div className='monthly-profit'>
          <ReactApexChart type='donut' height={300} series={MonthlyProfitsChartData.series} options={MonthlyProfitsChartData.options} />
        </div>
      </CardBody>
    </Card>
  );
};

export default MonthlyProfits;
