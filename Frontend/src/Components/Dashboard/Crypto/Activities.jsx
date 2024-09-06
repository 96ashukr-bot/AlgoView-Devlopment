import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardBody, CardHeader, Table } from 'reactstrap';
import { H5, Image } from '../../../AbstractElements';
import { ActivitiesTitle, DailyDropdown } from '../../../Constant';
import { activitiesMyOption } from '../../../Data/Crypto';
import DropdownCommon from '../../Common/Dropdown';

const Activities = () => {
  return (
    <Card>
      <CardHeader className='card-header card-no-border'>
        <div className='header-top'>
          <H5 className='m-0'>{ActivitiesTitle}</H5>
          <div className='card-header-right-icon'>
            <DropdownCommon dropdownMain={{ className: 'icon-dropdown', direction: 'start' }} options={DailyDropdown} iconName='icon-more-alt' btn={{ tag: 'span' }} />
          </div>
        </div>
      </CardHeader>
      <CardBody className='pt-0 activity-card'>
        <div className='appointment-table customer-table table-responsive'>
          <Table className='table table-bordernone'>
            <tbody>
              {activitiesMyOption.map((item, i) => (
                <tr key={i}>
                  <td>
                    <Image attrImage={{ className: 'img-fluid img-40 rounded-circle me-2', src: require(`../../../assets/images/dashboard/user/${item.image}`), alt: 'user' }} />
                  </td>
                  <td className='img-content-box'>
                    <Link className='d-block f-w-500' to={`/app/users/profile`}>
                      {item.title}
                    </Link>
                    <span className='f-light'>{item.subTitle}</span>
                  </td>
                  <td className='text-end'>
                    <span className={`font-${item.status}`}>{item.price}</span>
                    <span className='d-block f-light'>{item.total}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      </CardBody>
    </Card>
  );
};

export default Activities;
