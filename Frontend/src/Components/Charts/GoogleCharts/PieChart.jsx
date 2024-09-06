import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader } from 'reactstrap';
import { Chart } from 'react-google-charts';
import { H5 } from '../../../AbstractElements';

const PieChartClass = ({ data, title, colClass, digit, is3D, pieHole, pieStartAngle, pieSliceText }) => {

    return (
        <Fragment>
            <div className={colClass ? 'col-sm-12' : 'col-sm-12 col-xl-6'}>
                <Card>
                    <CardHeader>
                        <H5>{title} {digit ? <span className="digits">{digit}</span> : ''} </H5>
                    </CardHeader>
                    <CardBody className="chart-block">
                        <div className="chart-overflow" id="pie-chart1">
                            <Chart
                                width={data.width}
                                height={data.height}
                                chartType={data.chartType}
                                loader={<div>{'Loading Chart'}</div>}
                                data={data.data}
                                options={data.options && is3D ? { is3D: is3D } : '' &&
                                    pieHole ? { pieHole: pieHole } : '' &&
                                        pieStartAngle ? { pieStartAngle: pieStartAngle } : '' &&
                                            pieSliceText ? { pieSliceText: pieSliceText } : ''
                                }
                                rootProps={data.rootProps}
                            />
                        </div>
                    </CardBody>
                </Card>
            </div>
        </Fragment>
    );
};

export default PieChartClass;