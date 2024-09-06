import React, { Fragment, useState } from 'react';
import { Card, CardHeader, CardBody } from 'reactstrap';
import { Btn, H5, LI, P, UL } from '../../../../AbstractElements';
import { AboutMeData } from '../../../Common/Data/Bonus-ui';

const AboutMe = ({ colClass }) => {
  const [isShow, setIsShow] = useState(true);
  const toggleClick = () => {
    setIsShow(!isShow);
  };

  return (
    <Fragment>
      <div className={colClass}>
        <Card data-intro='This is your Your detail' className='step4'>
          <CardHeader>
            <H5 attrH5={{ className: 'p-0' }}>
              <Btn
                attrBtn={{
                  className: 'btn btn-link ps-0',
                  color: 'transperant',
                  onClick: toggleClick,
                }}>
                About Us
              </Btn>
            </H5>
          </CardHeader>
          <div className={`collapse ${isShow ? 'show' : ''}`} id='collapseicon2' aria-labelledby='collapseicon2' data-parent='#accordion'>
            <CardBody className='post-about'>
              <UL attrUL={{ className: 'simple-list' }}>
                {AboutMeData.map((item) => (
                  <LI key={item.id}>
                    <div className='icon'>{item.icon}</div>
                    <div>
                      <H5>{item.designation}</H5>
                      <P>{item.place}</P>
                    </div>
                  </LI>
                ))}
              </UL>
              <div className='social-network theme-form'>
                <span className='f-w-600'>Social Networks</span>
                <a className='btn social-btn btn-fb mb-2 text-center' href='https://www.facebook.com/'>
                  <i className='fa fa-facebook m-r-5'></i>Facebook
                </a>
                <a className='btn social-btn btn-twitter mb-2 text-center' href='https://twitter.com/'>
                  <i className='fa fa-twitter m-r-5'></i>Twitter
                </a>
                <a className='btn social-btn btn-google text-center' href='https://dribbble.com/'>
                  <i className='fa fa-dribbble m-r-5'></i>Dribbble
                </a>
              </div>
            </CardBody>
          </div>
        </Card>
      </div>
    </Fragment>
  );
};

export default AboutMe;
