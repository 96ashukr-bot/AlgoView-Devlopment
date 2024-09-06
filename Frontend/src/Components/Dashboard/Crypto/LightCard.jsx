import React from 'react';
import { H6 } from '../../../AbstractElements';

const LightCard = ({ data }) => {
  return (
    <div className='light-card balance-card align-items-center'>
      <H6 attrH6={{ className: 'f-w-400 f-14 mb-0' }}>{data.title}</H6>
      <div className='ms-auto text-end'>
        <span className={`badge badge-light-${data.status} rounded-pill`}>
          {data.status === 'success' ? '+' : '-'}
          {data.gros}%
        </span>
      </div>
    </div>
  );
};

export default LightCard;
