import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { H5 } from '../../../AbstractElements';
import { DailyDropdown, Visitors } from '../../../Constant';
import { OptionsVisitorChartWidget } from '../../../Data/Ecommerce/Chart';
import SvgIcon from '../../Common/Component/SvgIcon';
import DropdownCommon from '../../Common/Dropdown';

const VisitorsCard = () => {
  return (
    <Card className='visitor-card'>
      <CardHeader className='card-no-border pb-0'>
        <div className='header-top'>
          <H5 attrH5={{ className: 'm-0' }}>
            {Visitors}
            <span className='f-14 font-primary f-w-500 ms-1'>
              <SvgIcon iconId='user-visitor' className='svg-fill me-1' />
              (+2.8)
            </span>
          </H5>
          <div className='card-header-right-icon'>
            <DropdownCommon dropdownMain={{ className: 'icon-dropdown', direction: 'start' }} options={DailyDropdown} iconName='icon-more-alt' btn={{ tag: 'span' }} />
          </div>
        </div>
      </CardHeader>
      <CardBody className='pt-3'>
        <div className='visitors-container'>
          <ReactApexChart height={270} type='bar' options={OptionsVisitorChartWidget.options} series={OptionsVisitorChartWidget.series} />
        </div>
      </CardBody>
    </Card>
  );
};

export default VisitorsCard;
