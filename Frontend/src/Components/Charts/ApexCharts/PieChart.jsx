import React, { Fragment } from "react";
import { Card, CardBody, Col } from "reactstrap";
import { PieChart } from "../../../Constant";
import HeaderCard from "../../Common/Component/HeaderCard";
import Chart from 'react-apexcharts';
import { apexPieChart } from "./apexData";

const PieChartClass = () => {
    return (
        <Fragment>
            <Col sm='12' xl='6'>
                <Card>
                    <HeaderCard title={PieChart} />
                    <CardBody className="apex-chart">
                        <div id='piechart'>
                            <Chart options={apexPieChart.options} series={apexPieChart.series} type="pie" width={380} />
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}

export default PieChartClass;