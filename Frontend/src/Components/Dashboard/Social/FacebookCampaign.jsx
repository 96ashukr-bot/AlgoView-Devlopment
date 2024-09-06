import React from 'react';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H5, UL, LI, Image } from '../../../AbstractElements';
import { FacebookCampaignTitle, FollowersGoals, FollowersGoalsTotal, FollowersToday, FollowersTodayTotal } from '../../../Constant';

const FacebookCampaign = () => {
  const customersList = ['1', '6', '7', '3', '8'];
  return (
    <Card className=' follower-wrap'>
      <CardHeader className='card-no-border'>
        <H5 className='mb-1'>{FacebookCampaignTitle}</H5>
        <div className='d-inline-block badge badge-light-success rounded-pill'>Active</div>
      </CardHeader>
      <CardBody className='pt-0 papernote-wrap'>
        <UL attrUL={{ className: 'campaign-list' }}>
          <LI>
            <div className='campaign-box'>
              <H5 className='mb-1'>{FollowersTodayTotal}</H5>
              <span className='f-light'>{FollowersToday}</span>
            </div>
          </LI>
          <LI>
            <div className='campaign-box'>
              <H5 className='mb-1'>{FollowersGoalsTotal}</H5>
              <span className='f-light'>{FollowersGoals}</span>
            </div>
          </LI>
        </UL>
        <div className='customers'>
          <UL>
            {customersList.map((item, i) => (
              <LI attrLI={{ className: 'd-inline-block' }} key={i}>
                <Image attrImage={{ className: 'm-0 img-40 rounded-circle', src: require(`../../../assets/images/dashboard/user/${item}.jpg`), alt: 'user' }} />
              </LI>
            ))}
            <LI attrLI={{ className: 'd-inline-block' }}>
              <div className='light-card'>
                <span className='f-w-500'>+5</span>
              </div>
            </LI>
          </UL>
        </div>
      </CardBody>
    </Card>
  );
};

export default FacebookCampaign;
