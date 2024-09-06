import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { PieChart } from '../../../Constant';
import { Chart } from "react-google-charts";
import { H5 } from '../../../AbstractElements';

const PieChart2Class = ({ data, is3D }) => {

    return (
        <Fragment>
            <Col sm="12" xl="6">
                <Card>
                    <CardHeader>
                        <H5>{PieChart}  <span className="digits">{'2'}</span>  </H5>
                    </CardHeader>
                    <CardBody className="chart-block">
                        <div className="chart-overflow" id="pie-chart1">
                            <Chart
                                width={data.width}
                                height={data.height}
                                chartType={data.chartType}
                                loader={<div>{"Loading Chart"}</div>}
                                data={data.data}
                                options={data.options &&
                                    { is3D: is3D }
                                }
                                rootProps={data.rootProps}
                            />
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}

export default PieChart2Class;