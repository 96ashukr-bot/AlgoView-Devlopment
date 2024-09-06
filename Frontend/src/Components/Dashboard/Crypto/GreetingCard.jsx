import React from 'react';
import { Card, CardBody } from 'reactstrap';
import { H5, P, Btn, Image } from '../../../AbstractElements';
import { DepositNow, GreetingMessage4, GreetingMessage4SubMessage } from '../../../Constant';

import WelcomeImage from '../../../assets/images/dashboard-4/crypto.png';
const GreetingCard = () => {
  return (
    <Card className='crypto-main-card'>
      <CardBody>
        <div className='deposit-wrap'>
          <div>
            <H5>{GreetingMessage4}</H5>
            <P>{GreetingMessage4SubMessage}</P>
            <Btn attrBtn={{ color: 'white', className: 'f-w-500' }}>{DepositNow}</Btn>
          </div>
          <Image attrImage={{ src: WelcomeImage, alt: 'crypto' }} />
        </div>
      </CardBody>
    </Card>
  );
};

export default GreetingCard;
