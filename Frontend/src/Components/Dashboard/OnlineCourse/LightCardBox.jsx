import React from 'react';
import { H6 } from '../../../AbstractElements';

const LightCardBox = ({ data }) => {
  return (
    <div className='light-card balance-card'>
      <div>
        <span className='f-light'>{data.title}</span>
        <H6 attrH6={{ className: 'mt-1 mb-0' }}>
          {data.total}
          <span className={`badge badge-light-${data.color} rounded-pill ms-1`}>{data.badge}%</span>
        </H6>
      </div>
    </div>
  );
};

export default LightCardBox;
