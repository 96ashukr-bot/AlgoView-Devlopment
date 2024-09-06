import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardBody, CardHeader, Col, Table } from 'reactstrap';
import { Image, H5, P } from '../../../AbstractElements';
import { DailyDropdown, RecentSalesTitle } from '../../../Constant';
import { RecentSalesData } from '../../../Data/DefaultDashboard';
import DropdownCommon from '../../Common/Dropdown';

const RecentSales = () => {
  return (
    <Col xxl='4' md='6' className='appointment-sec box-col-6'>
      <div className='appointment'>
        <Card>
          <CardHeader className='card-no-border'>
            <div className='header-top'>
              <H5 attrH5={{ className: 'm-0' }}>{RecentSalesTitle}</H5>
              <div className='card-header-right-icon'>
                <DropdownCommon icon={false} options={DailyDropdown} btn={{ caret: true }} />
              </div>
            </div>
          </CardHeader>
          <CardBody className='pt-0'>
            <div className='appointment-table'>
              <Table borderless responsive>
                <tbody>
                  {RecentSalesData.map((item, i) => (
                    <tr key={i}>
                      <td>
                        <Image attrImage={{ className: 'img-fluid img-40 rounded-circle', src: require(`../../../assets/images/dashboard/user/${item.image}`), alt: 'user' }} />
                      </td>
                      <td className='img-content-box'>
                        <Link className='d-block f-w-500' to={`/app/users/profile`}>
                          {item.title}
                        </Link>
                        <span className='f-light'>{item.subTitle}</span>
                      </td>
                      <td className='text-end'>
                        <P attrPara={{ className: 'm-0 font-success' }}>{item.badge}</P>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
          </CardBody>
        </Card>
      </div>
    </Col>
  );
};

export default RecentSales;
