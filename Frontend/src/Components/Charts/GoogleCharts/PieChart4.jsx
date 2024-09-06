import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { RotatingPieChart } from '../../../Constant';
import { Chart } from "react-google-charts";
import { H5 } from '../../../AbstractElements';

const PieChart4Class = ({ data, pieStartAngle, pieSliceText }) => {

    return (
        <Fragment>
            <Col sm="12" xl="6">
                <Card>
                    <CardHeader>
                        <H5>{RotatingPieChart}  <span className="digits">{'1'}</span>  </H5>
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
                                    { pieStartAngle: pieStartAngle } &&
                                    { pieSliceText: pieSliceText }
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

export default PieChart4Class;