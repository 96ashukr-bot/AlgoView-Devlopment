import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';
import { H5, Btn } from '../../../AbstractElements';
import { MarketGraphTitle, SeeAllBalance } from '../../../Constant';
import { MarketGraphLegend } from '../../../Data/Crypto';
import { MarketGraphOption } from '../../../Data/Crypto/Chart';
import DailyFilterNav from './DailyFilterNav';
import LightCard from './LightCard';

const MarketGraph = () => {
  return (
    <Card className='card market-card'>
      <CardHeader className='card-no-border'>
        <div className='header-top'>
          <H5>{MarketGraphTitle}</H5>
          <DailyFilterNav />
        </div>
      </CardHeader>
      <CardBody className='pt-0'>
        <Row className='m-0 overall-card'>
          <Col xxl='8' xl='7' md='8' sm='7' className='p-0 box-col-7 col-ed-7'>
            <div className='market-chart-container'>
              <ReactApexChart type='line' height={300} options={MarketGraphOption.options} series={MarketGraphOption.series} />
            </div>
          </Col>
          <Col xxl='4' xl='5' md='4' sm='5' className='p-0 box-col-5 col-ed-5'>
            <Row className='g-sm-3 g-2'>
              {MarketGraphLegend.map((item, i) => (
                <Col key={i} md='12'>
                  <LightCard data={item} />
                </Col>
              ))}
              <Col md='12'>
                <Btn attrBtn={{ color:'dark', outline: true, className: 'w-100' }}>{SeeAllBalance}</Btn>
              </Col>
            </Row>
          </Col>
        </Row>
      </CardBody>
    </Card>
  );
};

export default MarketGraph;
