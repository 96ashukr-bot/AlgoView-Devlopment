import React, { Fragment } from "react";
import { Card, CardBody, Col } from "reactstrap";
import { DonutChart } from "../../../Constant";
import HeaderCard from "../../Common/Component/HeaderCard";
import Chart from 'react-apexcharts';
import { apexDonutCharts } from "./apexData";

const DonutChartClass = () => {
    return (
        <Fragment>
            <Col sm='12' xl='6'>
                <Card>
                    <HeaderCard title={DonutChart} />
                    <CardBody className="apex-chart donut-charts">
                        <div id='donutchart'>
                            <Chart options={apexDonutCharts.options} series={apexDonutCharts.series} type="donut" />
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}

export default DonutChartClass;