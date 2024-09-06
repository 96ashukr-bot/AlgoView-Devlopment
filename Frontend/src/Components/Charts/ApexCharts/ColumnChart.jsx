import React, { Fragment } from "react";
import { Card, CardBody, Col } from "reactstrap";
import { ColumnChart } from "../../../Constant";
import HeaderCard from "../../Common/Component/HeaderCard";
import Chart from 'react-apexcharts';
import { apexColumnChartsone } from "./apexData";

const ColumnChartClass = () => {
    return (
        <Fragment>
            <Col sm='12' xl='6'>
                <Card>
                    <HeaderCard title={ColumnChart} />
                    <CardBody>
                        <div id='column-chart'>
                            <Chart options={apexColumnChartsone.options} series={apexColumnChartsone.series} type="bar" height={350} />
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}

export default ColumnChartClass;