import React from 'react';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';
import { H5, UL, LI } from '../../../AbstractElements';
import { Earning, Order, OrderOverviewTitle, Refunds } from '../../../Constant';
import { LightCardData2 } from '../../../Data/DefaultDashboard';
import { OptionsOverView, OptionsOverViewBarChart } from '../../../Data/Ecommerce/Chart';
import ReactApexChart from 'react-apexcharts';
import LightCardBox from '../Default/LightCardBox';

const OrderOverview = () => {
  return (
    <Card>
      <CardHeader className='card-no-border'>
        <H5>{OrderOverviewTitle}</H5>
      </CardHeader>
      <CardBody className='pt-0'>
        <Row className='m-0 overall-card'>
          <Col xl='9' md='8' sm='7' className='box-col-7 p-0'>
            <div className='chart-right'>
              <Row>
                <Col xl='12'>
                  <CardBody className='p-0'>
                    <UL attrUL={{ horizontal: true, className: 'd-flex balance-data' }}>
                      <LI>
                        <span className='circle bg-secondary' />
                        <span className='f-light ms-1'>{Refunds}</span>
                      </LI>
                      <LI>
                        <span className='circle bg-primary'> </span>
                        <span className='f-light ms-1'>{Earning}</span>
                      </LI>
                      <LI>
                        <span className='circle bg-success'> </span>
                        <span className='f-light ms-1'>{Order}</span>
                      </LI>
                    </UL>
                    <div className='current-sale-container order-container'>
                      <ReactApexChart className='overview-wrapper' type='line' height={300} options={OptionsOverView.options} series={OptionsOverView.series} />
                      <div className='back-bar-container'>
                        <ReactApexChart type='bar' height={180} options={OptionsOverViewBarChart.options} series={OptionsOverViewBarChart.series} />
                      </div>
                    </div>
                  </CardBody>
                </Col>
              </Row>
            </div>
          </Col>
          <Col xl='3' md='4' sm='5' className='box-col-5 p-0'>
            <Row className='g-sm-3 g-2'>
              {LightCardData2.map((data, i) => (
                <Col key={i} md='12'>
                  <LightCardBox data={data} />
                </Col>
              ))}
            </Row>
          </Col>
        </Row>
      </CardBody>
    </Card>
  );
};

export default OrderOverview;
