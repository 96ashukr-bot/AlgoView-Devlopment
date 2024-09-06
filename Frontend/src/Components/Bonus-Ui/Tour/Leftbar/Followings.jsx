import React, { Fragment, useState } from 'react';
import { Card, CardHeader, CardBody } from 'reactstrap';
import { FollowingsData } from '../../../Common/Data/Bonus-ui';
import Image from '../../../../CommonElements/Media';
import { Btn, H5 } from '../../../../AbstractElements';
import { ChevronDown, ChevronUp } from 'react-feather';

const Followings = ({ colClass }) => {
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
                Followings {isShow ? <ChevronUp className='m-0' /> : <ChevronDown className='m-0' />}
              </Btn>
            </H5>
          </CardHeader>
          <div className={`collapse ${isShow ? 'show' : ''}`} id='collapseicon11' aria-labelledby='collapseicon11' data-parent='#accordion'>
            <CardBody className='social-list filter-cards-view'>
              {FollowingsData.map((item) => (
                <div className='media' key={item.id}>
                  <Image attrImage={{ className: 'img-50 img-fluid m-r-20 rounded-circle mb-0', alt: '', src: `${item.img}` }} />
                  <div className='media-body'>
                    <span className='d-block'>{item.name}</span>
                    <a href='#javascript'>Add Friend</a>
                  </div>
                </div>
              ))}
            </CardBody>
          </div>
        </Card>
      </div>
    </Fragment>
  );
};

export default Followings;
