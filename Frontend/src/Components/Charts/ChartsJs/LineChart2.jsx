import React from "react";
import { Line } from "react-chartjs-2";
import { Col, Card, CardBody } from "reactstrap";
import { LineChart2 } from "../../../Constant";
import { lineChart2Data, lineChart2option } from "../../../Data/Chart/chartjs";
import HeaderCard from '../../Common/Component/HeaderCard';

const LineChart2Class = () => {
    
    return (
        <Col xl="6" md="12" >
            <Card>
                <HeaderCard title={LineChart2} />
                <CardBody className="chart-block">
                    <Line data={lineChart2Data} options={lineChart2option} width={778} height={400} />
                </CardBody>
            </Card>
        </Col>
    )
}

export default LineChart2Class;