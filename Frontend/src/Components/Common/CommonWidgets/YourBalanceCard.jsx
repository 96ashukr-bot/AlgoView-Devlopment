import React from 'react';
import { ArrowDownRight } from 'react-feather';
import { Link } from 'react-router-dom';
import { Card, CardBody } from 'reactstrap';
import { Image, LI, H5, UL } from '../../../AbstractElements';

import userImage from '../../../assets/images/dashboard-4/user.png';
import { YourBalance, YourTotalBalance } from '../../../Constant';
import { YourBalanceTransaction } from '../../../Data/Crypto';
import SvgIcon from '../Component/SvgIcon';

const YourBalanceCard = ({ mainClass }) => {
  return (
    <Card className={`balance-box ${mainClass ? mainClass : ''}`}>
      <CardBody>
        <div className='balance-profile'>
          <div className='balance-img'>
            <Image attrImage={{ src: userImage, alt: 'user vector' }} />
            <Link className='edit-icon' to={`/app/users/profile`}>
              <SvgIcon iconId='pencil' />
            </Link>
          </div>
          <span className='f-light d-block'>{YourBalance}</span>
          <H5 attrH5={{ className: 'mt-1' }}>${YourTotalBalance}</H5>
          <UL attrUL={{ horizontal: true }}>
            {YourBalanceTransaction.map((item, i) => (
              <LI key={i}>
                <div className={`balance-item ${item.color}`}>
                  <div className='balance-icon-wrap'>
                    <div className='balance-icon'>
                      <ArrowDownRight />
                    </div>
                  </div>
                  <div>
                    <span className='f-12 f-light'>{item.title}</span>
                    <H5>{item.price}</H5>
                    <span className={`badge badge-light-${item.color} rounded-pill`}>{item.badge}</span>
                  </div>
                </div>
              </LI>
            ))}
          </UL>
        </div>
      </CardBody>
    </Card>
  );
};

export default YourBalanceCard;
