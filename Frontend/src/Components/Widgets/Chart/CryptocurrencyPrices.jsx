import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';
import { H5 } from '../../../AbstractElements';
import { CryptocurrencyPricesTitle } from '../../../Constant';
import { CryptocurrencyPricesTitleChartData } from '../../Common/Data/ApexChart';

const CryptocurrencyPrices = () => {
  return (
    <Col xl='6' lg='12' className='xl-50'>
      <Card>
        <CardHeader>
          <H5>{CryptocurrencyPricesTitle}</H5>
        </CardHeader>
        <CardBody>
          <div className='chart-container crypto-chart'>
            <Row className='row'>
              <Col>
                <ReactApexChart type='area' height={400} series={CryptocurrencyPricesTitleChartData.series} options={CryptocurrencyPricesTitleChartData.options} />
              </Col>
            </Row>
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default CryptocurrencyPrices;
