import React, { Fragment } from 'react';
import { Col, Card, CardBody } from "reactstrap";
import HeaderCard from '../../Common/Component/HeaderCard';
import { BarChart } from '../../../Constant';
import { Bar } from 'react-chartjs-2';
import { barChartData, barChartOptions } from '../../../Data/Chart/chartjs';

const BarChartClass = () => {
    return (
        <Fragment>
            <Col xl="6" md="12" >
                <Card>
                    <HeaderCard title={BarChart} />
                    <CardBody className="chart-block">
                        <Bar data={barChartData} options={barChartOptions} width={717} height={358} />
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}

export default BarChartClass;