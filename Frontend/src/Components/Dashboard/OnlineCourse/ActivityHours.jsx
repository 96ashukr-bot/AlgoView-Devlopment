import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';
import { H5 } from '../../../AbstractElements';
import { ActivityHoursTitle, DailyDropdown } from '../../../Constant';
import { LightCardBoxData } from '../../../Data/OnlineCourse';
import { ActivityHoursChartData } from '../../../Data/OnlineCourse/ChartData';
import DropdownCommon from '../../Common/Dropdown';
import LightCardBox from './LightCardBox';

const ActivityHours = () => {
  return (
    <Card>
      <CardHeader className='card-no-border'>
        <div className='header-top'>
          <H5>{ActivityHoursTitle}</H5>
          <DropdownCommon dropdownMain={{ className: 'icon-dropdown', direction: 'start' }} options={DailyDropdown} iconName='icon-more-alt' btn={{ tag: 'span' }} />
        </div>
      </CardHeader>
      <CardBody className='pt-0'>
        <Row className='m-0 overall-card'>
          <Col xl='8' className='col-xl-8'>
            <div className='chart-right'>
              <Row>
                <Col xl='12' className='col-xl-12'>
                  <CardBody className='p-0'>
                    <div className='activity-wrap'>
                      <ReactApexChart type='bar' height={300} options={ActivityHoursChartData.options} series={ActivityHoursChartData.series} />
                    </div>
                  </CardBody>
                </Col>
              </Row>
            </div>
          </Col>
          <Col xl='4' className='p-0'>
            <Row className='g-sm-3 g-2 mt-0'>
              {LightCardBoxData.map((item, i) => (
                <Col key={i} xl='12' md='6' sm='4'>
                  <LightCardBox data={item} key={i} />
                </Col>
              ))}
            </Row>
          </Col>
        </Row>
      </CardBody>
    </Card>
  );
};

export default ActivityHours;
