import React, { Fragment } from "react";
import { Card, CardBody, Col } from "reactstrap";
import { MixedChart } from "../../../Constant";
import HeaderCard from "../../Common/Component/HeaderCard";
import Chart from 'react-apexcharts';
import { apexMixedCharts } from "./apexData";

const MixedChartClass = () => {
    return (
        <Fragment>
            <Col sm='12'>
                <Card>
                    <HeaderCard title={MixedChart} />
                    <CardBody>
                        <div id='mixedchart'>
                            <Chart options={apexMixedCharts.options} series={apexMixedCharts.series} type="line" height={350} />
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}

export default MixedChartClass;