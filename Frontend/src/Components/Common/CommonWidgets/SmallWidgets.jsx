import React from 'react';
import { Card, CardBody } from 'reactstrap';
import { H4 } from '../../../AbstractElements';
import SvgIcon from '../Component/SvgIcon';
import CountUp from 'react-countup';
const SmallWidgets = ({ data, mainClass }) => {
  return (
    <Card className={`small-widget ${mainClass ? mainClass : ''}`}>
      <CardBody className={data.color}>
        <span className='f-light'>{data.title}</span>
        <div className='d-flex align-items-end gap-1'>
          <H4>
            <CountUp suffix={data.suffix ? data.suffix : ''} prefix={data.prefix ? data.prefix : ''} duration={0} separator=',' end={data.total} />
          </H4>
          <span className={`font-${data.color} f-12 f-w-500`}>
            <i className={`icon-arrow-${data.gros < 50 ? 'down' : 'up'}`} />
            <span>
              {data.gros < 50 ? '-' : '+'}
              {data.gros}%
            </span>
          </span>
        </div>
        <div className='bg-gradient'>
          <SvgIcon iconId={data.icon} className='stroke-icon svg-fill' />
        </div>
      </CardBody>
    </Card>
  );
};

export default SmallWidgets;
