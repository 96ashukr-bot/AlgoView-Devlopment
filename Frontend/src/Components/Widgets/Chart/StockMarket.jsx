import React, { Fragment } from 'react';
import { optionsCandleStickChart } from '../../Common/Data/ApexChart';
import Chart from 'react-apexcharts';
import { Col, Card, CardBody } from 'reactstrap';
import HeaderCard from '../../Common/Component/HeaderCard';

const StockMarket = () => {
  return (
    <Fragment>
      {/* <!-- browser uses widget chart Start--> */}
      <Col sm='12' className='box-col-12'>
        <div className='donut-chart-widget'>
          <Card>
            <HeaderCard title={'Stock Market'} />
            <CardBody>
              <div id='chart-widget13'>
                <Chart options={optionsCandleStickChart.options} series={optionsCandleStickChart.series} height='500' type='candlestick' />
              </div>
            </CardBody>
          </Card>
        </div>
      </Col>
      {/* <!-- browser uses widget chart Endss--> */}
    </Fragment>
  );
};

export default StockMarket;
