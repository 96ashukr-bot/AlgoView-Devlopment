import React, { Fragment } from "react";
import { Card, CardBody, Col } from "reactstrap";
import { BubbleChart } from "../../../Constant";
import HeaderCard from "../../Common/Component/HeaderCard";
import Chart from 'react-apexcharts';
import { apex3DbubbleCharts } from "./apexData";

const BubbleChartClass = () => {
    return (
        <Fragment>
            <Col sm='12' xl='6'>
                <Card>
                    <HeaderCard title={BubbleChart} />
                    <CardBody>
                        <div id='chart-bubble'>
                            <Chart options={apex3DbubbleCharts.options} series={apex3DbubbleCharts.series} type="bubble" height={350} />
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}

export default BubbleChartClass;