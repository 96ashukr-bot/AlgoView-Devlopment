import React, { Fragment } from "react";
import { Card, CardBody, Col } from "reactstrap";
import { SteplineChart } from "../../../Constant";
import HeaderCard from "../../Common/Component/HeaderCard";
import Chart from 'react-apexcharts';
import { apexSteplineChart } from "./apexData";

const SteplineChartClass = () => {
    return (
        <Fragment>
            <Col sm='12' xl='6'>
                <Card>
                    <HeaderCard title={SteplineChart} />
                    <CardBody>
                        <div id='stepline'>
                            <Chart options={apexSteplineChart.options} series={apexSteplineChart.series} type="line" height={350} />
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}

export default SteplineChartClass;