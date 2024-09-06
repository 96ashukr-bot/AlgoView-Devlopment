import React from 'react';
import { Col, Card, CardBody } from "reactstrap";
import HeaderCard from '../../Common/Component/HeaderCard';
import { LineChart } from '../../../Constant';
import { Line } from 'react-chartjs-2';
import { lineChartData, lineChartOptions } from '../../../Data/Chart/chartjs';

const LineChartClass = () => {

    return (
        <Col xl="6" md="12" >
            <Card>
                <HeaderCard title={LineChart} />
                <CardBody className="chart-block">
                    <Line data={lineChartData} options={lineChartOptions} width={717} height={358} />
                </CardBody>
            </Card>
        </Col>
    )
}

export default LineChartClass;