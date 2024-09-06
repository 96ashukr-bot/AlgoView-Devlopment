import React from 'react';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H5, H4 } from '../../../AbstractElements';
import { DailyDropdown, OrderThisMonthTitle } from '../../../Constant';
import { OrderThisMonthChart } from '../../../Data/Ecommerce/Chart';
import DropdownCommon from '../../Common/Dropdown';
import CountUp from 'react-countup';
import ReactApexChart from 'react-apexcharts';
const OrderThisMonth = () => {
  return (
    <Card className='card'>
      <CardHeader className='card-header card-no-border'>
        <div className='header-top'>
          <H5 attrH5={{ className: 'm-0' }}>{OrderThisMonthTitle}</H5>
          <div className='card-header-right-icon'>
            <DropdownCommon dropdownMain={{ className: 'icon-dropdown', direction: 'start' }} options={DailyDropdown} iconName='icon-more-alt' btn={{ tag: 'span' }} />
          </div>
        </div>
      </CardHeader>
      <CardBody className='card-body pt-0'>
        <div className='light-card balance-card d-inline-block'>
          <H4 attrH4={{ className: 'm-0' }}>
            <CountUp className='me-1' prefix='$' duration={0} separator=',' end={12000} />
            <CountUp className='f-light f-14' prefix='(' suffix=' To Goal)' duration={0} separator=',' end={15080} />
          </H4>
        </div>
        <div className='order-wrapper'>
          <ReactApexChart type='line' height={235} options={OrderThisMonthChart.options} series={OrderThisMonthChart.series} />
        </div>
      </CardBody>
    </Card>
  );
};

export default OrderThisMonth;
