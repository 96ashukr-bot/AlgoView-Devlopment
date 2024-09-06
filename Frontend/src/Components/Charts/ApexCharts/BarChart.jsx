import React, { Fragment } from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { BarChart } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';
import Chart from 'react-apexcharts';
import { apexBarChart } from './apexData';

const BarChartClass = () => {
    return (
        <Fragment>
            <Col sm='12' xl='6'>
                <Card>
                    <HeaderCard title={BarChart} />
                    <CardBody>
                        <div id='basic-bar'>
                            <Chart options={apexBarChart.options} series={apexBarChart.series} type="bar" height={350} />
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default BarChartClass;