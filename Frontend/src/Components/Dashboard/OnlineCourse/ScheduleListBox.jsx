import React from 'react';
import { H6, Image, UL, LI } from '../../../AbstractElements';

import SvgIcon from '../../Common/Component/SvgIcon';

const ScheduleListBox = ({ data }) => {
  return (
    <UL attrUL={{ className: 'schedule-list d-flex' }}>
      {data.map((item, i) => (
        <LI key={i} attrLI={{ className: `${item.color}` }}>
          <Image attrImage={{ src: require(`../../../assets/images/dashboard/user/${item.image}`), alt: 'profile' }} />
          <div>
            <H6 className='mb-1'>{item.title}</H6>
            <UL>
              <LI attrLI={{ className: 'f-light' }}>
                <SvgIcon iconId={item.icon} className='fill-icon f-light' />
                <span>{item.date}</span>
              </LI>
              <LI attrLI={{ className: 'f-light' }}>
                <SvgIcon iconId={item.icon2} className='fill-icon f-success' />
                <span> {item.date2}</span>
              </LI>
            </UL>
          </div>
        </LI>
      ))}
    </UL>
  );
};

export default ScheduleListBox;
