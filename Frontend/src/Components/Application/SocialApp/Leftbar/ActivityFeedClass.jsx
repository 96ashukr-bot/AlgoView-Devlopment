import React, { Fragment, useState } from 'react';
import { ChevronDown, ChevronUp } from 'react-feather';
import { Card, CardHeader, CardBody, Media, Collapse } from 'reactstrap';
import { Btn, H3, Image, P } from '../../../../AbstractElements';
import { ActivityFeed } from '../../../../Constant';
import { ActivityFeedData } from '../../../../Data/SocialHeader';

const ActivityFeedClass = () => {
  const [isActivity, setisActivity] = useState(true);
  return (
    <Fragment>
      <Card>
        <CardHeader>
          <H3 attrH3={{ className: 'mb-0' }}>
            <Btn attrBtn={{ className: 'd-flex justify-content-between', color: 'link', onClick: () => setisActivity(!isActivity) }}>
              {ActivityFeed} {isActivity ? <ChevronUp className='m-0' /> : <ChevronDown className='m-0' />}
            </Btn>
          </H3>
        </CardHeader>
        <Collapse isOpen={isActivity}>
          <CardBody className='social-status filter-cards-view'>
            {ActivityFeedData.map((data, i) => (
              <Media key={i}>
                <Image attrImage={{ className: 'img-50 rounded-circle m-r-15', src: `${data.img}`, alt: 'tenImg' }} />
                <Media body>
                  <span className='f-w-500 d-block'>{data.name}</span>
                  <P>
                    {data.para} <a href='#javascript'>{'Photo'}</a>
                  </P>
                  <span className='light-span'>{data.time}</span>
                </Media>
              </Media>
            ))}
          </CardBody>
        </Collapse>
      </Card>
    </Fragment>
  );
};

export default ActivityFeedClass;
