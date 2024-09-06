import React, { Fragment, useState } from 'react';
import { Card, CardBody, CardHeader, Collapse, Media, UncontrolledTooltip } from 'reactstrap';
import { Btn, H5, H6, Image, LI, UL } from '../../../../AbstractElements';
import { Likes, Messages, MyPage, MyProfile, Notification, View } from '../../../../Constant';
import { customersData } from '../../../../Data/SocialHeader';
import one from '../../../../assets/images/user/1.jpg';
import { ChevronDown, ChevronUp } from 'react-feather';

const MyProfileClass = () => {
  const [isProfile, setisProfile] = useState(true);
  return (
    <Fragment>
      <Card>
        <CardHeader>
          <H5 attrH5={{ className: 'mb-0' }}>
            <Btn attrBtn={{ className: 'd-flex justify-content-between', color: 'link', onClick: () => setisProfile(!isProfile) }}>
              {MyProfile}
              {isProfile ? <ChevronUp className='m-0' /> : <ChevronDown className='m-0' />}
            </Btn>
          </H5>
        </CardHeader>
        <Collapse isOpen={isProfile}>
          <CardBody className='socialprofile filter-cards-view'>
            <Media>
              <Image attrImage={{ className: 'img-50 img-fluid m-r-20 rounded-circle', src: `${one}`, alt: '' }} />
              <Media body>
                <H6 attrH6={{ className: 'font-primary f-w-600' }}>{MyPage}</H6>
                <span className='d-block'>
                  <span>
                    <i className='fa fa-comments-o'> </i>
                    <span className='px-2'>
                      {Messages}
                      <span className='badge rounded-pill badge-light ms-2'>{'9'}</span>
                    </span>
                  </span>
                </span>
                <span className='d-block'>
                  <span>
                    <i className='fa fa-bell-o'></i>
                    <span className='px-2'>
                      {Notification}
                      <span className='badge rounded-pill badge-light ms-2'>{'9'}</span>
                    </span>
                  </span>
                </span>
              </Media>
            </Media>
            <div className='social-btngroup d-flex'>
              <Btn attrBtn={{ color: 'primary text-center', type: 'button' }}>{Likes}</Btn>
              <Btn attrBtn={{ color: 'light text-center ms-2', type: 'button' }}>{View}</Btn>
            </div>
            <div className='likes-profile text-center'>
              <H5>
                <span>
                  <i className='fa fa-heart font-danger'></i> {'884'}
                </span>
              </H5>
            </div>
            <div className='text-center'>{'35 New Likes This Week'}</div>
            <div className='customers text-center social-group'>
              <UL>
                {customersData.map((data, i) => (
                  <LI attrLI={{ className: 'd-inline-block border-0 p-0' }} key={i}>
                    <Image attrImage={{ className: 'img-40 rounded-circle', src: `${data.img}`, alt: 'ThirdImg', id: 'UncontrolledTooltipExample' }} />
                    <UncontrolledTooltip placement='top' target='UncontrolledTooltipExample'>
                      {data.name}
                    </UncontrolledTooltip>
                  </LI>
                ))}
              </UL>
            </div>
          </CardBody>
        </Collapse>
      </Card>
    </Fragment>
  );
};

export default MyProfileClass;
