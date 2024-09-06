import React from "react";
import { Col, Card, CardBody } from "reactstrap";
import HeaderCard from '../../Common/Component/HeaderCard';
import { RadarChart } from '../../../Constant';
import { Radar } from "react-chartjs-2";
import { RadarChartData } from "../../../Data/Chart/chartjs";



const RadarChartClass = () => {
    return (
        <Col xl="6" md="12" >
            <Card>
                <HeaderCard title={RadarChart} />
                <CardBody className="chart-block chart-vertical-center">
                    <Radar data={RadarChartData} width={200} height={258} />
                </CardBody>
            </Card>
        </Col>
    )
}

export default RadarChartClass;