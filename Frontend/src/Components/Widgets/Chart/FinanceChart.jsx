import React, { Fragment } from 'react';
import Charts from 'react-apexcharts';
import { Navigation } from 'react-feather';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';
import { H5 } from '../../../AbstractElements';
import { Finance } from '../../../Constant';
import { columnChart } from '../../Common/Data/ApexChart';

const FinanceChart = () => {
    return (
        <Fragment>
            <Col xl="5" lg="12" className="box-col-12">
                <Card>
                    <CardHeader>
                        <Row>
                            <Col xs="9">
                                <H5>{Finance}</H5>
                            </Col>
                            <Col xs="3" className="text-end"><Navigation className="text-muted" /></Col>
                        </Row>
                    </CardHeader>
                    <CardBody>
                        <div className="chart-container">
                            <div id="columnchart">
                                <Charts options={columnChart.options} series={columnChart.series} height="380" type="bar" />
                            </div>
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}

export default FinanceChart;