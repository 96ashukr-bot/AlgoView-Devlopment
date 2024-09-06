import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { H5 } from '../../../AbstractElements';
import { DailyDropdown, Timeline } from '../../../Constant';
import { TimeLineChart } from '../../../Data/DefaultDashboard/Chart';
import DropdownCommon from '../../Common/Dropdown';

const TimelineCard = () => {
  return (
    <Col xxl='4' md='6' className='appointment-sec box-col-6'>
      <div className='appointment'>
        <Card>
          <CardHeader className='card-no-border'>
            <div className='header-top'>
              <H5 attrH5={{ className: 'm-0' }}>{Timeline}</H5>
              <div className='card-header-right-icon'>
                <DropdownCommon icon={false} options={DailyDropdown} btn={{ caret: true }} />
              </div>
            </div>
          </CardHeader>
          <CardBody className='pt-0'>
            <div className='schedule-container'>
              <ReactApexChart height={355} type='rangeBar' options={TimeLineChart.options} series={TimeLineChart.series} />
            </div>
          </CardBody>
        </Card>
      </div>
    </Col>
  );
};

export default TimelineCard;
