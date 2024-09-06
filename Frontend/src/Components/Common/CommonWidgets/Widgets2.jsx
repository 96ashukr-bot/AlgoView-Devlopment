import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { Card, CardBody } from 'reactstrap';
import { H4 } from '../../../AbstractElements';

const Widgets2 = ({ data, chartClass, mainClass }) => {
  return (
    <>
      <Card className={`widget-1 widget-with-chart ${mainClass ? mainClass : ''}`}>
        <CardBody>
          <div>
            <H4 attrH4={{ className: 'mb-1' }}>{data.total}</H4>
            <span className='f-light'>{data.title}</span>
          </div>
          <div className={`${chartClass ? chartClass : 'order-chart'}`}>
            <ReactApexChart type={data.chart.options.chart.type} height={data.chart.options.chart.height} options={data.chart.options} series={data.chart.series} />
          </div>
        </CardBody>
      </Card>
    </>
  );
};

export default Widgets2;
