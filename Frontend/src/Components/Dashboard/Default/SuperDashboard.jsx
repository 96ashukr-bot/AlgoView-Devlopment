import React from 'react';
import { Card, CardBody, Col, Media } from 'reactstrap';
import { H4, P, Btn, Image } from '../../../AbstractElements';
import { WelcomeMessage, WelcomeToCuba, WhatsNew } from '../../../Constant';

import CarToon from '../../../assets/images/dashboard/cartoon.svg';

const SuperDashboard = () => {
  return (
    <Col className='col-xxl-4 col-sm-6 box-col-6'>
      <Card className='profile-box'>
        <CardBody>
          <Media>
            <Media body>
              <div className='greeting-user'>
                <H4 attrH4={{ className: 'f-w-600' }}>Welcome To AlgoView</H4>
                <P>{WelcomeMessage}</P>
                <div className='whatsnew-btn'>
                  <Btn attrBtn={{ color: 'transparent', outline: true, className: 'btn btn-outline-white' }}>{WhatsNew}</Btn>
                </div>
              </div>
            </Media>
            <div>
              <div className='clockbox'>
                <svg id='clock' xmlns='http://www.w3.org/2000/svg' viewBox='0 0 600 600'>
                  <g id='face'>
                    <circle className='circle' cx={300} cy={300} r='253.9' />
                    <path className='hour-marks' d='M300.5 94V61M506 300.5h32M300.5 506v33M94 300.5H60M411.3 107.8l7.9-13.8M493 190.2l13-7.4M492.1 411.4l16.5 9.5M411 492.3l8.9 15.3M189 492.3l-9.2 15.9M107.7 411L93 419.5M107.5 189.3l-17.1-9.9M188.1 108.2l-9-15.6' />
                    <circle className='mid-circle' cx={300} cy={300} r='16.2' />
                  </g>
                  <g id='hour'>
                    <path className='hour-hand' d='M300.5 298V142' />
                    <circle className='sizing-box' cx={300} cy={300} r='253.9' />
                  </g>
                  <g id='minute'>
                    <path className='minute-hand' d='M300.5 298V67' />
                    <circle className='sizing-box' cx={300} cy={300} r='253.9' />
                  </g>
                  <g id='second'>
                    <path className='second-hand' d='M300.5 350V55' />
                    <circle className='sizing-box' cx={300} cy={300} r='253.9'></circle>
                  </g>
                </svg>
              </div>
              <div className='badge f-10 p-0' id='txt' />
            </div>
          </Media>
          <div className='cartoon'>
            <Image attrImage={{ src: CarToon, alt: 'vector women with leptop' }} />
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default SuperDashboard;
