import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';

import { OrderStatus } from '../../../Constant';
import { ShoppingBag } from 'react-feather';
import { H5 } from '../../../AbstractElements';

import ReactApexChart from 'react-apexcharts';
import { OrderStatusChartData } from '../../Common/Data/ApexChart';

const OrderStatusChart = () => {
  return (
    <Fragment>
      <Col xl='7' lg='12' className='box-col-12'>
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
            <div className='chart-container'>
              <div id='linechart'>
                <ReactApexChart type='line' height={350} series={OrderStatusChartData.series} options={OrderStatusChartData.options} />
              </div>
            </div>
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};
export default OrderStatusChart;
