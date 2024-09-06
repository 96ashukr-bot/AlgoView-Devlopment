import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardBody } from 'reactstrap';
import { H4, Image } from '../../../AbstractElements';
import { TapUpBalance, ThisMonth, TotalBalanceTitle } from '../../../Constant';

import CountUp from 'react-countup';
import WidgetImg from '../../../assets/images/dashboard-2/widget-img.png';
import MobileGif from '../../../assets/images/dashboard-2/mobile.gif';

const TotalBalance = () => {
  return (
    <Card className='o-hidden'>
      <CardBody className='balance-widget'>
        <span className='f-w-500 f-light'>{TotalBalanceTitle}</span>
        <H4 attrH4={{ className: 'mb-3 mt-1 f-w-500 mb-0 f-22' }}>
          <CountUp prefix='$' duration={5} start={0} separator=',' end={245154} />
          <span className='f-light f-14 f-w-400 ms-1'>{ThisMonth}</span>
        </H4>
        <Link className='purchase-btn btn btn-primary btn-hover-effect f-w-500' to='#'>
          {TapUpBalance}
        </Link>
        <div className='mobile-right-img'>
          <Image attrImage={{ className: 'left-mobile-img', src: WidgetImg, alt: '' }} />
          <Image attrImage={{ className: 'mobile-img', src: MobileGif, alt: 'mobile with coin' }} />
        </div>
      </CardBody>
    </Card>
  );
};

export default TotalBalance;
