import React, { Fragment } from 'react';
import { Row, Col, Card, CardBody } from 'reactstrap';
import Chart from 'react-apexcharts';
import { LiveProductChart, MonthlySale, TurnoverChart, WidgetsUserChart } from '../../common/data/apex-chart';
import HeaderCard from '../../Common/Component/HeaderCard';

const SmallWidgets = () => {
    return (
        <Fragment>
            <Row>
                <Col xl={7} className="xl-50 box-col-6">
                    <div className="small-chart-widget chart-widgets-small">
                        <Card>
                            <HeaderCard title={"Live Products"} />
                            <CardBody>
                                <div className="chart-container">
                                    <Row>
                                        <Col>
                                            <div id="chart-widget6">
                                                <Chart options={LiveProductChart.options} series={LiveProductChart.series} type='line' height={320} />
                                            </div>
                                        </Col>
                                    </Row>
                                </div>
                            </CardBody>
                        </Card>
                    </div>
                </Col>
                <Col xl="5" className="xl-50 box-col-6">
                    <div className="small-chart-widget chart-widgets-small">
                        <div className="card">
                            <div className="card-header pb-0">
                                <h5>Turnover</h5>
                            </div>
                            <div className="card-body">
                                <div className="chart-container">
                                    <div className="row">
                                        <div className="col-12">
                                            <div id="chart-widget7">
                                                <Chart options={TurnoverChart.options} series={TurnoverChart.series} type='area' height={320} />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </Col>
                <Col xl="5" className="xl-50 box-col-6">
                    <div className="small-chart-widget chart-widgets-small">
                        <div className="card">
                            <div className="card-header pb-0">
                                <h5>Monthly Sales</h5>
                            </div>
                            <div className="card-body">
                                <div className="chart-container">
                                    <div className="row">
                                        <div className="col-12">
                                            <div id="chart-widget8">
                                                <Chart options={MonthlySale.options} series={MonthlySale.series} height="280" type="radar" />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </Col>
                <div className="xl-50 col-xl-7 box-col-6">
                    <div className="small-chart-widget chart-widgets-small">
                        <div className="card">
                            <div className="card-header pb-0">
                                <h5>Uses</h5>
                            </div>
                            <div className="card-body">
                                <div className="chart-container">
                                    <div className="row">
                                        <div className="col-12">
                                            <div id="chart-widget9">
                                                <Chart options={WidgetsUserChart.options} series={WidgetsUserChart.series} height="280" type="bubble" />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </Row>
        </Fragment>
    );
};

export default SmallWidgets;