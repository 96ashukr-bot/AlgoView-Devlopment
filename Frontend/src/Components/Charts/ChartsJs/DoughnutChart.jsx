import React from "react";
import { Doughnut } from "react-chartjs-2";
import { Col, Card, CardBody } from "reactstrap";
import { DoughnutChart } from "../../../Constant";
import { doughnutData, doughnutOption } from "../../../Data/Chart/chartjs";
import HeaderCard from '../../Common/Component/HeaderCard';

const DoughnutChartClass = () => {

    return (
        <Col xl="6" md="12" >
            <Card>
                <HeaderCard title={DoughnutChart} />
                <CardBody className="chart-block">
                    <Doughnut data={doughnutData} options={doughnutOption} width={717} height={358} />
                </CardBody>
            </Card>
        </Col>
    )
}

export default DoughnutChartClass;