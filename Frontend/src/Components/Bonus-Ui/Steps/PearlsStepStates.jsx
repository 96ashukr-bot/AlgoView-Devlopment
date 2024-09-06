import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';
import { H5 } from '../../../AbstractElements';

const PearlsStepStatesClass = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card >
                    <CardHeader>
                        <H5>Pearls Step States</H5><span>A pearls step states with different class<code>.done</code><code>.currunt</code><code>.error</code><code>.disabled</code></span>
                    </CardHeader>
                    <CardBody>
                        <Row className="mb-5">
                            <div className="u-pearl current col-4">
                                <div className="u-pearl-icon">1</div><span className="u-pearl-title">Account Info</span>
                            </div>
                            <div className="u-pearl disabled col-4">
                                <div className="u-pearl-icon">2</div><span className="u-pearl-title">Billing Info</span>
                            </div>
                            <div className="u-pearl disabled col-4">
                                <div className="u-pearl-icon">3</div><span className="u-pearl-title">Confirmation</span>
                            </div>
                        </Row>
                        <Row className="mb-5">
                            <div className="u-pearl done col-4">
                                <div className="u-pearl-icon">1</div><span className="u-pearl-title">Account Info</span>
                            </div>
                            <div className="u-pearl current col-4">
                                <div className="u-pearl-icon">2</div><span className="u-pearl-title">Billing Info</span>
                            </div>
                            <div className="u-pearl disabled col-4">
                                <div className="u-pearl-icon">3</div><span className="u-pearl-title">Confirmation</span>
                            </div>
                        </Row>
                        <Row className="mb-5">
                            <div className="u-pearl done col-4">
                                <div className="u-pearl-icon">1</div><span className="u-pearl-title">Account Info</span>
                            </div>
                            <div className="u-pearl current error col-4">
                                <div className="u-pearl-icon">2</div><span className="u-pearl-title">Billing Info</span>
                            </div>
                            <div className="u-pearl disabled col-4">
                                <div className="u-pearl-icon">3</div><span className="u-pearl-title">Confirmation</span>
                            </div>
                        </Row>
                        <Row>
                            <div className="u-pearl done col-4">
                                <div className="u-pearl-icon">1</div><span className="u-pearl-title">Account Info</span>
                            </div>
                            <div className="u-pearl done col-4">
                                <div className="u-pearl-icon">2</div><span className="u-pearl-title">Billing Info</span>
                            </div>
                            <div className="u-pearl current col-4">
                                <div className="u-pearl-icon">3</div><span className="u-pearl-title">Confirmation</span>
                            </div>
                        </Row>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default PearlsStepStatesClass;