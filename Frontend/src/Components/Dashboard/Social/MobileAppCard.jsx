import React from 'react';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { Btn, H5, Image } from '../../../AbstractElements';
import { HaveYouTriedOur, MobileApplication, TryNow } from '../../../Constant';

import wave from '../../../assets/images/dashboard-5/wave.png';
import mobileImage from '../../../assets/images/dashboard-5/mobile-img.png';

const MobileAppCard = () => {
  return (
    <Card className='mobile-app-card'>
      <CardHeader className='card-no-border pb-0'>
        <H5 attrH5={{ className: 'mb-3' }}>
          <span className='f-16 f-light'>{HaveYouTriedOur} </span>
          {MobileApplication}
        </H5>
        <Btn attrBtn={{ color: 'primary', className: 'purchase-btn btn-hover-effect f-w-500', type: 'button' }}>{TryNow}</Btn>
      </CardHeader>
      <CardBody className='p-0 text-end'>
        <Image attrImage={{ className: 'wavy', src: wave, alt: '' }} />
        <Image attrImage={{ src: mobileImage, alt: '' }} />
      </CardBody>
    </Card>
  );
};

export default MobileAppCard;
