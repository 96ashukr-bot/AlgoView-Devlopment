import React from 'react';
import { Card, CardBody } from 'reactstrap';
import { Image, H5 } from '../../../AbstractElements';
import RadialChart from './RadialChart';

const SocialWidget = ({ data }) => {
  return (
    <Card className='social-widget widget-hover'>
      <CardBody>
        <div className='d-flex align-items-center justify-content-between'>
          <div className='d-flex align-items-center gap-2'>
            <div className='social-icons'>
              <Image attrImage={{ src: require(`../../../assets/images/dashboard-5/social/${data.image}`), alt: 'facebook icon' }} />
            </div>
            <span>{data.title}</span>
          </div>
          <span className='font-success f-12 d-xxl-block d-xl-none'>+{data.gros}%</span>
        </div>
        <div className='social-content'>
          <div>
            <H5 attrH5={{ className: 'mb-1' }}>{data.total}</H5>
            <span className='f-light'>{data.subTitle}</span>
          </div>
          <div className='social-chart'>
            <RadialChart chartData={data.chart} />
          </div>
        </div>
      </CardBody>
    </Card>
  );
};

export default SocialWidget;
