import React from 'react';
import { UserMinus, UserPlus } from 'react-feather';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { UL, LI, H5 } from '../../../AbstractElements';
import { TotalUsers, WeeklyMonDropdown } from '../../../Constant';
import DropdownCommon from '../../Common/Dropdown';
const TotalUser = () => {
  return (
    <Card>
      <CardHeader className='card-no-border'>
        <div className='header-top'>
          <H5>{TotalUsers}</H5>
          <DropdownCommon dropdownMain={{ className: 'icon-dropdown', direction: 'start' }} options={WeeklyMonDropdown} iconName='icon-more-alt' btn={{ tag: 'span' }} />
        </div>
      </CardHeader>
      <CardBody className='pt-0'>
        <UL attrUL={{ className: 'user-list' }}>
          <LI>
            <div className='user-icon primary'>
              <div className='user-box'>
                <UserPlus className='font-primary' />
              </div>
            </div>
            <div>
              <H5 attrH5={{ className: 'mb-1' }}>178,098</H5>
              <span className='font-primary d-flex align-items-center'>
                <i className='icon-arrow-up icon-rotate me-1'> </i>
                <span className='f-w-500'>+30.89</span>
              </span>
            </div>
          </LI>
          <LI>
            <div className='user-icon success'>
              <div className='user-box'>
                <UserMinus className='font-success' />
              </div>
            </div>
            <div>
              <H5 attrH5={{ className: 'mb-1' }}>178,098</H5>
              <span className='font-danger d-flex align-items-center'>
                <i className='icon-arrow-down icon-rotate me-1' />
                <span className='f-w-500'>-08.89</span>
              </span>
            </div>
          </LI>
        </UL>
      </CardBody>
    </Card>
  );
};

export default TotalUser;
