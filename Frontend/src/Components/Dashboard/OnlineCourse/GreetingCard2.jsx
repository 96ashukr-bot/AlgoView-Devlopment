import React from 'react';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H5, Btn, Image } from '../../../AbstractElements';
import { BetterResults, DoYouWantToGet, MoreDetails } from '../../../Constant';
import SvgIcon from '../../Common/Component/SvgIcon';
import greetingImage from '../../../assets/images/dashboard-3/better.png';
import SquareGroupUi from './SquareGroupUi';

const GreetingCard2 = () => {
  return (
    <Card className='get-card overflow-hidden'>
      <CardHeader className='card-header card-no-border'>
        <H5>{DoYouWantToGet}</H5>
        <span className='f-14 f-w-500 f-light'>{BetterResults}</span>
        <Btn attrBtn={{ color: 'primary', className: 'btn-hover-effect' }}>
          {MoreDetails}
          <span className='ms-1'>
            <SvgIcon className='fill-icon' iconId='arrowright' />
          </span>
        </Btn>
      </CardHeader>
      <CardBody className='pt-0'>
        <div className='get-image text-center'>
          <Image attrImage={{ className: 'img-fluid', src: greetingImage, alt: 'leptop with men vector' }} />
        </div>
      </CardBody>
      <SquareGroupUi />
    </Card>
  );
};

export default GreetingCard2;
