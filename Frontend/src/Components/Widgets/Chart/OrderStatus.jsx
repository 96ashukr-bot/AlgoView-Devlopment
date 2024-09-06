import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';
import Chart from 'react-apexcharts';
import { progress1, progress2, progress3, progress4, progress5 } from '../../Common/Data/ApexChart';
import { OrderStatus } from '../../../Constant';
import { ShoppingBag } from 'react-feather';
import { H5 } from '../../../AbstractElements';

const OrderStatusProgressChart = () => {
  return (
    <Fragment>
      <Col xl='6' lg='12' className='box-col-6 xl-50'>
        <Card>
          <CardHeader>
            <Row>
              <Col xs='9'>
                <H5>{OrderStatus}</H5>
              </Col>
              <Col xs='3' className='text-end'>
                <ShoppingBag className='text-muted' />
              </Col>
            </Row>
          </CardHeader>
          <CardBody>
            <div className='chart-container progress-chart'>
              <div id='progress1'>
                <Chart options={progress1.options} series={progress1.series} height='70' type='bar' />
              </div>
              <div id='progress2'>
                <Chart options={progress2.options} series={progress2.series} height='70' type='bar' />
              </div>
              <div id='progress3'>
                <Chart options={progress3.options} series={progress3.series} height='70' type='bar' />
              </div>
              <div id='progress4'>
                <Chart options={progress4.options} series={progress4.series} height='70' type='bar' />
              </div>
              <div id='progress5'>
                <Chart options={progress5.options} series={progress5.series} height='70' type='bar' />
              </div>
            </div>
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};

export default OrderStatusProgressChart;
