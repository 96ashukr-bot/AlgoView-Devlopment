import React from 'react';
import { Row, Col, Card, CardBody } from 'reactstrap';
import Chart from 'react-apexcharts';
import { MonthlySale } from '../../Common/Data/ApexChart';
import HeaderCard from '../../Common/Component/HeaderCard';

const MonthlySaleChart = () => {
    return (
        <Col xl="5" className="xl-50 box-col-6">
            <div className="small-chart-widget chart-widgets-small">
                <Card>
                    <HeaderCard title={"Monthly Sales"} />
                    <CardBody>
                        <div className="chart-container">
                            <Row>
                                <Col>
                                    <div id="chart-widget8">
                                        <Chart options={MonthlySale.options} series={MonthlySale.series} height="280" type="radar" />
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

export default MonthlySaleChart;