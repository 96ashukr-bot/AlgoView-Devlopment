import React, { Fragment } from "react";
import { Card, CardBody, Col } from "reactstrap";
import { RadarChart } from "../../../Constant";
import HeaderCard from "../../Common/Component/HeaderCard";
import Chart from 'react-apexcharts';
import { apexRadarPolygonfillCharts } from "./apexData";

const RadarChartClass = () => {
    return (
        <Fragment>
            <Col sm='12' xl="6">
                <Card>
                    <HeaderCard title={RadarChart} />
                    <CardBody>
                        <div id='radarchart'>
                            <Chart options={apexRadarPolygonfillCharts.options} series={apexRadarPolygonfillCharts.series} type="radar" height={350} />
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}

export default RadarChartClass;