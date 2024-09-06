import React, { Fragment } from 'react';
import { Card, Col, Row } from 'reactstrap';
import Charts from 'react-apexcharts';
import { lineChart1, lineChart2, lineChart3 } from '../../Common/Data/ApexChart';

import { H4, H6 } from '../../../AbstractElements';
import { CompareToLastMonth, TotalProject, TotalSale } from '../../../Constant';

const ChartWidgets = () => {
  return (
    <Fragment>
      <Row>
        <Col xl='4' md='12' className='box-col-12'>
          <Card className='o-hidden'>
            <div className='chart-widget-top'>
              <Row className='row card-body pb-0 m-0'>
                <Col xl='9' lg='8' className='col-9 p-0'>
                  <H6 attrH6={{ className: 'mb-2' }}>{TotalSale}</H6>
                  <H4>$3654.00</H4>
                  <span>{CompareToLastMonth}</span>
                </Col>
                <Col xl='3' lg='4' xs='3' className='text-end p-0'>
                  <H6 className='txt-success'>+65%</H6>
                </Col>
              </Row>
              <div>
                <div id='chart-widget1'>
                  <Charts options={lineChart1.options} series={lineChart1.series} height='170' type='area' />
                </div>
              </div>
            </div>
          </Card>
        </Col>

        <Col xl='4'>
          <Card className='o-hidden'>
            <div className='chart-widget-top'>
              <Row className='card-body pb-0 m-0'>
                <Col xl='9' lg='8' xs='9' className='p-0'>
                  <H6 attrH6={{ className: 'mb-2' }}>{TotalProject}</H6>
                  <H4>12569</H4>
                  <span>{CompareToLastMonth}</span>
                </Col>
                <Col xl='3' lg='4' xs='3' className='text-end p-0'>
                  <H6 className='txt-success'>+65%</H6>
                </Col>
              </Row>
              <div id='chart-widget2'>
                <Charts id='chart-widget-top-second' className='flot-chart-placeholder' options={lineChart2.options} series={lineChart2.series} height='170' type='area' />
              </div>
            </div>
          </Card>
        </Col>

        <Col xl='4'>
          <Card className='o-hidden'>
            <div className='chart-widget-top'>
              <Row className='card-body pb-0 m-0'>
                <Col xl='9' lg='8' xs='9' className='p-0'>
                  <H6 attrH6={{ className: 'mb-2' }}>{TotalProject}</H6>
                  <H4>12569</H4>
                  <span>{CompareToLastMonth}</span>
                </Col>
                <Col xl='3' lg='4' xs='3' className='text-end p-0'>
                  <H6 className='txt-success'>+65%</H6>
                </Col>
              </Row>
              <div id='chart-widget2'>
                <Charts id='chart-widget-top-second' className='flot-chart-placeholder' options={lineChart3.options} series={lineChart3.series} height='170' type='area' />
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </Fragment>
  );
};

export default ChartWidgets;
