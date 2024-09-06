import React, { Fragment } from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { DonutChart } from '../../../Constant';
import { Chart } from "react-google-charts";
import HeaderCard from '../../Common/Component/HeaderCard';

const PieChart3Class = ({ data, pieHole }) => {

    return (
        <Fragment>
            <Col sm="12" xl="6">
                <Card>
                    <HeaderCard title={DonutChart} />
                    <CardBody className="chart-block">
                        <div className="chart-overflow" id="pie-chart1">
                            <Chart
                                width={data.width}
                                height={data.height}
                                chartType={data.chartType}
                                loader={<div>{"Loading Chart"}</div>}
                                data={data.data}
                                options={data.options &&
                                    { pieHole: pieHole }
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

export default PieChart3Class;