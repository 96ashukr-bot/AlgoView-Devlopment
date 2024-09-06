import React, { Fragment } from 'react';
// import { LI, UL } from '../../../../../AbstractElements';
// import CountUp from 'react-countup';
// import { Label } from 'reactstrap';
// import { Comment, Like } from '../../../../../Constant';

const UserFooter = () => {
  return (
    <Fragment>
      {/* <div className='like-comment mt-4'>
        <UL attrUL={{ className: 'simple-list list-inline d-flex flex-row' }}>
          <LI attrLI={{ className: 'list-inline-item border-end pe-2 border-0' }}>
            <Label className='m-0'>
              <a href='#javascript'>
                <i className='fa fa-heart'></i>
              </a>
                {Like}
            </Label>
            <CountUp end={2569} className='ms-2 counter' />
          </LI>
          <LI attrLI={{ className: 'list-inline-item border-0' }}>
            <Label className='m-0'>
              <a href='#javascript'>
                <i className='fa fa-comment'></i>
              </a>
                {Comment}
            </Label>
            <CountUp end={569} className='ms-2 counter' />
          </LI>
        </UL>
      </div> */}
    </Fragment>
  );
};

export default UserFooter;
