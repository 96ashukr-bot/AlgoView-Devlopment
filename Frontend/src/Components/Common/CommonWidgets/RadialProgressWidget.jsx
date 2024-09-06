import React from 'react';
import { ArrowDown, ArrowUp } from 'react-feather';
import { Card, CardBody } from 'reactstrap';
import { H6, H5, P } from '../../../AbstractElements';
import RadialProgressChart from './RadialProgressChart';

const RadialProgressWidget = ({ data, chartHeight }) => {
  return (
    <Card className='widget-hover'>
      <CardBody className='radial-progress-card'>
        <div>
          <H6 attrH6={{ className: 'mb-0' }}>{data.title}</H6>
          <div className='sale-details'>
            <H5 attrH5={{ className: `font-${data.color} mb-0` }}>{data.average}</H5>
            <span className='f-12 f-light f-w-500'>
              {data.gros >= 1.5 ? <ArrowUp /> : <ArrowDown />}
              {data.gros >= 1.5 ? '+' : '-'}
              {data.gros}%
            </span>
          </div>
          <P attrPara={{ className: 'f-light' }}> {data.subTitle}</P>
        </div>
        <div className='radial-chart-wrap'>
          <RadialProgressChart chartHeight={chartHeight} chartOption={data} />
        </div>
      </CardBody>
    </Card>
  );
};

export default RadialProgressWidget;
