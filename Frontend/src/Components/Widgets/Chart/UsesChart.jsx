import React from 'react';
import { Row, Col, Card, CardBody } from 'reactstrap';
import Chart from 'react-apexcharts';
import { WidgetsUserChart } from '../../Common/Data/ApexChart';
import HeaderCard from '../../Common/Component/HeaderCard';

const UsesChart = () => {
    return (
        <Col xl="7" className="xl-50 box-col-6">
            <div className="small-chart-widget chart-widgets-small">
                <Card>
                    <HeaderCard title={"Uses"} />
                    <CardBody>
                        <div className="chart-container">
                            <Row>
                                <Col>
                                    <div id="chart-widget9">
                                        <Chart options={WidgetsUserChart.options} series={WidgetsUserChart.series} height="280" type="bubble" />
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

export default UsesChart;