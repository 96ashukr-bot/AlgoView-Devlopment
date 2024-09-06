import React, { Fragment, useState } from 'react';
import { Card, CardHeader, CardBody } from 'reactstrap';
import { FriendsData } from '../../../Common/Data/Bonus-ui';
import Image from '../../../../CommonElements/Media';
import { Btn, H5 } from '../../../../AbstractElements';
import { ChevronDown, ChevronUp } from 'react-feather';

const Friends = ({ colClass }) => {
  const [isShow, setIsShow] = useState(true);
  const toggleClick = () => {
    setIsShow(!isShow);
  };

  return (
    <Fragment>
      <div className={colClass}>
        <Card>
          <CardHeader>
            <H5 attrH5={{ className: 'p-0' }}>
              <Btn
                attrBtn={{
                  className: 'btn btn-link d-flex justify-content-between',
                  color: 'transperant',
                  onClick: toggleClick,
                }}>
                Friends {isShow ? <ChevronUp className='m-0' /> : <ChevronDown className='m-0' />}
              </Btn>
            </H5>
          </CardHeader>
          <div className={`collapse ${isShow ? 'show' : ''}`} id='collapseicon13' data-parent='#accordion' aria-labelledby='collapseicon13'>
            <CardBody className='avatar-showcase filter-cards-view'>
              {FriendsData.map((item) => (
                <div className='d-inline-block friend-pic' key={item.id}>
                  <Image attrImage={{ className: 'img-50 rounded-circle', src: `${item.img}`, alt: '#' }} />
                </div>
              ))}
            </CardBody>
          </div>
        </Card>
      </div>
    </Fragment>
  );
};

export default Friends;
