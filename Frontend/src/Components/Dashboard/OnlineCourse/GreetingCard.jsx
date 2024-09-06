import React from 'react';
import { Card, CardBody } from 'reactstrap';
import { H4, Image, P } from '../../../AbstractElements';
import { HelloJashmin, welcomeMessage } from '../../../Constant';
import Hand from '../../../assets/images/dashboard-3/hand.svg';
import welcome from '../../../assets/images/dashboard-3/widget.svg';

const GreetingCard = () => {
  return (
    <Card className='o-hidden welcome-card'>
      <CardBody>
        <H4 attrH4={{ className: 'mb-3 mt-1 f-w-500 mb-0 f-22' }}>
          {HelloJashmin}
          <span>
            <Image attrImage={{ src: Hand, alt: 'hand vector' }} />
          </span>
        </H4>
        <P>{welcomeMessage}</P>
      </CardBody>
      <Image attrImage={{ className: 'welcome-img', src: welcome, alt: 'search image' }} />
    </Card>
  );
};

export default GreetingCard;
