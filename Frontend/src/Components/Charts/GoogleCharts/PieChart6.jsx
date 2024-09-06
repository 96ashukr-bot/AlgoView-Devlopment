import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { RotatingPieChart } from '../../../Constant';
import { Chart } from "react-google-charts";
import { H5 } from '../../../AbstractElements';

const PieChart5Class = ({ data }) => {

    return (
        <Fragment>
            <Col sm="12" >
                <Card>
                    <CardHeader>
                        <H5>{RotatingPieChart}  <span className="digits">{'2'}</span>  </H5>
                    </CardHeader>
                    <CardBody className="chart-block">
                        <div className="chart-overflow" id="pie-chart1">
                            <Chart
                                width={data.width}
                                height={data.height}
                                chartType={data.chartType}
                                loader={<div>{"Loading Chart"}</div>}
                                data={[
                                    [
                                        { type: 'string', label: 'Task ID' },
                                        { type: 'string', label: 'Task Name' },
                                        { type: 'date', label: 'Start Date' },
                                        { type: 'date', label: 'End Date' },
                                        { type: 'number', label: 'Duration' },
                                        { type: 'number', label: 'Percent Complete' },
                                        { type: 'string', label: 'Dependencies' },
                                    ],
                                    [
                                        'Research',
                                        'Find sources',
                                        new Date(2015, 0, 1),
                                        new Date(2015, 0, 5),
                                        null,
                                        100,
                                        null,
                                    ],
                                    [
                                        'Write',
                                        'Write paper',
                                        null,
                                        new Date(2015, 0, 9),
                                        3 * 24 * 60 * 60 * 1000,
                                        25,
                                        'Research,Outline',
                                    ],
                                    [
                                        'Cite',
                                        'Create bibliography',
                                        null,
                                        new Date(2015, 0, 7),
                                        1 * 24 * 60 * 60 * 1000,
                                        20,
                                        'Research',
                                    ],
                                    [
                                        'Complete',
                                        'Hand in paper',
                                        null,
                                        new Date(2015, 0, 10),
                                        1 * 24 * 60 * 60 * 1000,
                                        0,
                                        'Cite,Write',
                                    ],
                                    [
                                        'Outline',
                                        'Outline paper',
                                        null,
                                        new Date(2015, 0, 6),
                                        1 * 24 * 60 * 60 * 1000,
                                        100,
                                        'Research',
                                    ],
                                ]}
                                options={{
                                    gantt: {
                                        criticalPathEnabled: false,
                                        arrow: {
                                            angle: 100,
                                            width: 5,
                                            color: '#51bb25',
                                            radius: 0
                                        },

                                        palette: [
                                            {
                                                "color": "#7366ff",
                                                "dark": "#f73164",
                                                "light": "#047afb"
                                            }
                                        ]

                                    },
                                    backgroundColor: 'transparent',
                                }}
                                rootProps={data.rootProps}
                            />
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}

export default PieChart5Class;