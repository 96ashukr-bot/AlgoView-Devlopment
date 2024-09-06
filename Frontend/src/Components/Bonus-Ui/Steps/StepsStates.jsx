import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';
import { H5, P } from '../../../AbstractElements';

const StepsStatesClass = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <H5>Step States</H5>
                        <span>A u-step with classname <code>.done</code> A u-step with classname <code>.error</code>A u-step with classname <code>.current</code>A u-step with classname <code>.disabled</code></span>
                    </CardHeader>
                    <CardBody>
                        <Row className="row-lg">
                            <Col xl="3" lg="6">
                                <div className="u-step done bg-primary"><span className="u-step-number txt-primary">1</span>
                                    <div className="u-step-desc"><span className="u-step-title">Getting</span>
                                        <P attrPara={{ className: 'text-light' }} >Waiting for the goods</P>
                                    </div>
                                </div>
                            </Col>
                            <Col xl="3" lg="6" className="steps-md-mt">
                                <div className="u-step error bg-secondary"><span className="u-step-number txt-secondary">2</span>
                                    <div className="u-step-desc"><span className="u-step-title">Getting</span>
                                        <P attrPara={{ className: 'text-light' }} >Waiting for the goods</P>
                                    </div>
                                </div>
                            </Col>
                            <Col xl="3" lg="6" className="lg-mt">
                                <div className="u-step current bg-success"><span className="u-step-number txt-success">3</span>
                                    <div className="u-step-desc"><span className="u-step-title">Getting</span>
                                        <P>Waiting for the goods</P>
                                    </div>
                                </div>
                            </Col>
                            <Col xl="3" lg="6" className="lg-mt">
                                <div className="u-step disabled"><span className="u-step-number">4</span>
                                    <div className="u-step-desc"><span className="u-step-title">Getting</span>
                                        <P>Waiting for the goods</P>
                                    </div>
                                </div>
                            </Col>
                        </Row>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default StepsStatesClass;