import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';
import { SkillStatus } from '../../../Constant';
import Chart from 'react-apexcharts';
import { radialChartLive } from '../../Common/Data/ApexChart';
import { TrendingUp } from 'react-feather';
import { H5 } from '../../../AbstractElements';

const SkillStatusChart = () => {
  return (
    <Fragment>
      <Col xl='6' lg='12' className='box-col-6 xl-50 box-col-6 xl-50'>
        <Card>
          <CardHeader>
            <Row>
              <Col xs='9'>
                <H5>{SkillStatus}</H5>
              </Col>
              <Col xs='3' className='text-end'>
                <TrendingUp className='text-muted' />
              </Col>
            </Row>
          </CardHeader>
          <CardBody>
            <div className='chart-container'>
              <div id='circlechart'>
                <Chart options={radialChartLive.options} series={radialChartLive.series} height='350' type='radialBar' />
              </div>
            </div>
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};

export default SkillStatusChart;
