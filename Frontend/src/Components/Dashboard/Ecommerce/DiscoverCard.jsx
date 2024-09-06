import React from 'react';
import { Card, CardBody } from 'reactstrap';
import { Image, H5, P } from '../../../AbstractElements';
import { DiscoverPera, DiscoverPro, UpdateNow } from '../../../Constant';

import discoverImage from '../../../assets/images/dashboard-2/discover.png';

const DiscoverCard = () => {
  return (
    <Card className='purchase-card discover'>
      <Image attrImage={{ className: 'img-fluid', src: discoverImage, alt: 'vector discover' }} />
      <CardBody className='pt-3'>
        <H5 attrH5={{ className: 'mb-1' }}>{DiscoverPro}</H5>
        <P attrPara={{ className: 'f-light' }}>{DiscoverPera} </P>
        <a className='purchase-btn btn btn-hover-effect btn-primary f-w-500' href='https://1.envato.market/3GVzd' rel="noreferrer" target='_blank'>
          {UpdateNow}
        </a>
      </CardBody>
    </Card>
  );
};

export default DiscoverCard;
