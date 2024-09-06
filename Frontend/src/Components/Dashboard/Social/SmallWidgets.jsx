import React from 'react';
import { Card, CardBody } from 'reactstrap';
import { H4 } from '../../../AbstractElements';
import { DailyDropdown } from '../../../Constant';

import DropdownCommon from '../../Common/Dropdown';
import SmallWidgetsChart from './SmallWidgetsChart';
const SmallWidgets = ({ data }) => {
  return (
    <Card className='click-widgets widget-hover'>
      <CardBody>
        <DropdownCommon dropdownMain={{ className: 'text-end icon-dropdown', direction: 'start' }} options={DailyDropdown} iconName='icon-more-alt' btn={{ tag: 'span' }} />
        <div className='d-flex justify-content-around'>
          <div className='click-chart'>
            <SmallWidgetsChart chartData={data.chart} />
          </div>
          <div>
            <H4 attrH4={{ className: 'mb-0' }}>%{data.total}</H4>
            <span className='f-light d-block my-1'>{data.title}</span>
            <span className='font-success'>+{data.gros}%</span>
          </div>
        </div>
      </CardBody>
    </Card>
  );
};

export default SmallWidgets;
