import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardBody } from 'reactstrap';
import { Image, H5, LI, UL } from '../../../AbstractElements';
import { BrooklynSimmons, BrooklynSimmonsEmail } from '../../../Constant';
import { SocialProfileStatus } from '../../../Data/Social';

import profileImage from '../../../assets/images/dashboard-5/profile.png';
import SvgIcon from '../../Common/Component/SvgIcon';

const SocialProfileCard = () => {
  return (
    <Card className='social-profile'>
      <CardBody>
        <div className='social-img-wrap'>
          <div className='social-img'>
            <Image attrImage={{ src: profileImage, alt: 'profile' }} />
          </div>
          <div className='edit-icon'>
            <SvgIcon iconId='profile-check' />
          </div>
        </div>
        <div className='social-details'>
          <H5 attrH5={{ className: 'mb-1' }}>
            <Link to={`/app/social-app`}>{BrooklynSimmons}</Link>
          </H5>
          <span className='f-light'>{BrooklynSimmonsEmail}</span>
          <UL attrUL={{ className: 'social-follow' }}>
            {SocialProfileStatus.map((item, i) => (
              <LI key={i}>
                <H5 attrH5={{ className: 'mb-0' }}>{item.active}</H5>
                <span className='f-light'>{item.title}</span>
              </LI>
            ))}
          </UL>
        </div>
      </CardBody>
    </Card>
  );
};

export default SocialProfileCard;
