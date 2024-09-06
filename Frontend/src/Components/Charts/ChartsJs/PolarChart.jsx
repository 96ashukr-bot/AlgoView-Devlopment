import React from "react";
import { Col, Card, CardBody } from "reactstrap";
import HeaderCard from '../../Common/Component/HeaderCard';
import { PolarChart } from '../../../Constant';
import { PolarArea } from "react-chartjs-2";
import { polarData, polarOption } from "../../../Data/Chart/chartjs";

const PolarChartClass = () => {
    return (
        <Col xl="6" md="12" >
            <Card>
                <HeaderCard title={PolarChart} />
                <CardBody className="chart-block chart-vertical-center">
                    <PolarArea data={polarData} options={polarOption} width={717} height={358} />
                </CardBody>
            </Card>
        </Col>
    )
}

export default PolarChartClass;