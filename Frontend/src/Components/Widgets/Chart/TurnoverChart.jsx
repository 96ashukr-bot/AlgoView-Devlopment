import React from 'react';
import { Row, Col, Card, CardBody } from 'reactstrap';
import Chart from 'react-apexcharts';
import { TurnoverChart } from '../../Common/Data/ApexChart';
import HeaderCard from '../../Common/Component/HeaderCard';

const TurnoverChartComponent = () => {
    return (
        <Col xl="5" className="xl-50 box-col-6">
            <div className="small-chart-widget chart-widgets-small">
                <Card>
                    <HeaderCard title={"Turnover"} />
                    <CardBody>
                        <div className="chart-container">
                            <Row>
                                <Col>
                                    <div id="chart-widget7">
                                        <Chart options={TurnoverChart.options} series={TurnoverChart.series} type='area' height={320} />
                                    </div>
                                </Col>
                            </Row>
                        </div>
                    </CardBody>
                </Card>
            </div>
        </Col>
    );
};

export default TurnoverChartComponent;