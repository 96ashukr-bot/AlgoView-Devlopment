import React, { Fragment } from "react";
import { Card, CardBody, Col } from "reactstrap";
import { CandlestickChart } from "../../../Constant";
import HeaderCard from "../../Common/Component/HeaderCard";
import Chart from 'react-apexcharts';
import { apexCandleStickCharts } from "./apexData";

const CandlestickChartClass = () => {
    return (
        <Fragment>
            <Col sm='12'>
                <Card>
                    <HeaderCard title={CandlestickChart} />
                    <CardBody >
                        <div id='candlestick'>
                            <Chart options={apexCandleStickCharts.options} series={apexCandleStickCharts.series} type="candlestick" height={350} />
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}

export default CandlestickChartClass;