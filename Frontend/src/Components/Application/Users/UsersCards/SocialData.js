import React from 'react';
import { LI, UL, H5 } from '../../../../AbstractElements';
const SocialData = ({ totalPost, follower, following }) => {
  return (
    <UL attrUL={{ className: 'social-follow' }}>
      <LI>
        <H5 attrH5={{ className: 'mb-0' }}>{totalPost}</H5>
        <span className='f-light'>Posts</span>
      </LI>
      <LI>
        <H5 attrH5={{ className: 'mb-0' }}>{follower}</H5>
        <span className='f-light'>Followers</span>
      </LI>
      <LI>
        <H5 attrH5={{ className: 'mb-0' }}>{following}</H5>
        <span className='f-light'>Following</span>
      </LI>
    </UL>
  );
};

export default SocialData;
