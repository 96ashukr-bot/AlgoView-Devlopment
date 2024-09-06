import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';
import { H5 } from '../../../AbstractElements';
import { CryptoAnnotationsTitle } from '../../../Constant';
import { optionsAnnotation } from '../../Common/Data/ApexChart';

const CryptoAnnotations = () => {
  return (
    <Col xl='6' lg='12' className='xl-50'>
      <Card>
        <CardHeader>
          <H5>{CryptoAnnotationsTitle}</H5>
        </CardHeader>
        <CardBody>
          <div className='chart-container'>
            <Row>
              <Col xs='12'>
                <div id='crypto-annotation'>
                  <ReactApexChart type='line' height={400} series={optionsAnnotation.series} options={optionsAnnotation.options} />
                </div>
              </Col>
            </Row>
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default CryptoAnnotations;
