import React, { Fragment, useState } from 'react';
import { Card, CardHeader, CardBody } from 'reactstrap';
import { FollowersData } from '../../../Common/Data/Bonus-ui';
import Image from '../../../../CommonElements/Media';
import { Btn, H5 } from '../../../../AbstractElements';
import { ChevronDown, ChevronUp } from 'react-feather';

const Followers = ({ colClass }) => {
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
                Followers {isShow ? <ChevronUp className='m-0' /> : <ChevronDown className='m-0' />}
              </Btn>
            </H5>
          </CardHeader>
          <div className={`collapse ${isShow ? 'show' : ''}`} id='collapseicon8' aria-labelledby='collapseicon8' data-parent='#accordion'>
            <CardBody className='social-list filter-cards-view'>
              {FollowersData.map((item) => (
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

export default Followers;
