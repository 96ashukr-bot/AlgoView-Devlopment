import React from 'react';
import { TrendingUp } from 'react-feather';
import { Card, CardBody } from 'reactstrap';
import { H6, H5 } from '../../../AbstractElements';
import SvgIcon from '../Component/SvgIcon';
import CurrencyWidgetChart from '../../Dashboard/Crypto/CurrencyWidgetChart';

const CurrencyWidget = ({ data, mainClass }) => {
  return (
    <div className={`currency-widget ${data.color} ${mainClass ? mainClass : ''}`}>
      <div className='d-flex'>
        <div className='currency-icon-widget'>
          <SvgIcon iconId={data.icon} />
        </div>
        <div>
          <H6>
            {data.title} <span className='f-light'>{data.sortName}</span>
          </H6>
        </div>
      </div>
      <Card>
        <CardBody className='d-flex'>
          <div className='currency-chart-wrap'>
            <CurrencyWidgetChart chartData={data.chart} />
          </div>
          <div className={`bg-light-${data.color} text-center`}>
            <H5 attrH5={{ className: 'mb-0' }}>${data.price}</H5>
            <span className={`f-12 f-w-500 font-${data.color}`}>
              <TrendingUp className='me-1' />+{data.gros}%
            </span>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

export default CurrencyWidget;
