import React, { Fragment } from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { BasicAreaChart } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';
import Chart from 'react-apexcharts';
import { apexAreaChart } from './apexData';

const BasicAreaChartClass = () => {
    return (
        <Fragment>
            <Col sm='12' xl='6'>
                <Card>
                    <HeaderCard title={BasicAreaChart} />
                    <CardBody>
                        <div id='basic-apex'>
                            <Chart options={apexAreaChart.options} series={apexAreaChart.series} type="area" height={350} />
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default BasicAreaChartClass;