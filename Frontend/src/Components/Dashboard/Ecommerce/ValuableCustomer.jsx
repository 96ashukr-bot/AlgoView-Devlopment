import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardHeader, Table } from 'reactstrap';
import { H5, Image } from '../../../AbstractElements';
import { DailyDropdown, ValuableCustomerTitle } from '../../../Constant';
import { ValuableCustomerData } from '../../../Data/Ecommerce';
import DropdownCommon from '../../Common/Dropdown';

const ValuableCustomer = () => {
  return (
    <div className='appointment'>
      <Card>
        <CardHeader className='card-no-border'>
          <div className='header-top'>
            <H5 className='m-0'>{ValuableCustomerTitle}</H5>
            <div className='card-header-right-icon'>
              <DropdownCommon dropdownMain={{ className: 'icon-dropdown', direction: 'start' }} options={DailyDropdown} iconName='icon-more-alt' btn={{ tag: 'span' }} />
            </div>
          </div>
        </CardHeader>
        <div className='card-body pt-0'>
          <div className='appointment-table customer-table '>
            <Table borderless responsive>
              <tbody>
                {ValuableCustomerData.map((item, i) => (
                  <tr key={i}>
                    <td>
                      <Image attrImage={{ className: 'img-fluid img-40 rounded-circle me-2', src: require(`../../../assets/images/dashboard/user/${item.image}`), alt: 'user' }} />
                    </td>
                    <td className='img-content-box'>
                      <Link className='f-w-500' to={`/user-profile`}>
                        {item.name}
                      </Link>
                      <span className='f-light'>{item.email}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ValuableCustomer;
