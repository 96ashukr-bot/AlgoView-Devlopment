import { MarketChart } from '../../Common/Data/ApexChart';
import React, { Fragment } from 'react';
import Charts from 'react-apexcharts';
import { Row, Col, Card, CardBody } from 'reactstrap';
import HeaderCard from '../../Common/Component/HeaderCard';

const BarChartsWidgets = () => {
  return (
    <Fragment>
      <Row>
        <Col xs='12'>
          <Card className='o-hidden'>
            <HeaderCard title={'Marketing Expenses'} />
            <div className='bar-chart-widget'>
              <CardBody className='bottom-content'>
                <Row>
                  <Col>
                    <div id='chart-widget4'>
                      <Charts options={MarketChart.options} series={MarketChart.series} type='bar' height={360} />
                    </div>
                  </Col>
                </Row>
              </CardBody>
            </div>
          </Card>
        </Col>
      </Row>
    </Fragment>
  );
};

export default BarChartsWidgets;
