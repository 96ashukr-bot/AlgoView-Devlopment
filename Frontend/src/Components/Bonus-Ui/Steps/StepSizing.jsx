import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';
import { H5 } from '../../../AbstractElements';

const StepsSizingClass = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <H5>Step Sizing</H5><span>A step with classname <code>.u-steps-xs</code><code>.u-steps-sm</code><code>.u-steps-lg</code></span>
                    </CardHeader>
                    <CardBody>
                        <Row className="u-steps u-steps-xs steps-sizing-sm-mb">
                            <Col md="4" className="u-step"><span className="u-step-icon icon wb-shopping-cart" aria-hidden="true"></span>
                                <div className="u-step-desc"><span className="u-step-title">Shopping</span></div>
                            </Col>
                            <Col md="4" className="u-step current"><span className="u-step-icon icon wb-pluse" aria-hidden="true"></span>
                                <div className="u-step-desc"><span className="u-step-title">Billing</span></div>
                            </Col>
                            <Col md="4" className="u-step"><span className="u-step-icon icon wb-time" aria-hidden="true"></span>
                                <div className="u-step-desc"><span className="u-step-title">Getting</span></div>
                            </Col>
                        </Row>
                        <Row className="u-steps u-steps-sm steps-sizing-sm-mb">
                            <Col md="4" className="u-step"><span className="u-step-icon icon wb-shopping-cart" aria-hidden="true"></span>
                                <div className="u-step-desc"><span className="u-step-title">Shopping</span></div>
                            </Col>
                            <Col md="4" className="u-step current"><span className="u-step-icon icon wb-pluse" aria-hidden="true"></span>
                                <div className="u-step-desc"><span className="u-step-title">Billing</span></div>
                            </Col>
                            <Col md="4" className="u-step"><span className="u-step-icon icon wb-time" aria-hidden="true"></span>
                                <div className="u-step-desc"><span className="u-step-title">Getting</span></div>
                            </Col>
                        </Row>
                        <Row className="u-steps steps-sizing-sm-mb">
                            <Col md="4" className="u-step"><span className="u-step-icon icon wb-shopping-cart" aria-hidden="true"></span>
                                <div className="u-step-desc"><span className="u-step-title">Shopping</span></div>
                            </Col>
                            <Col md="4" className="u-step current"><span className="u-step-icon icon wb-pluse" aria-hidden="true"></span>
                                <div className="u-step-desc"><span className="u-step-title">Billing</span></div>
                            </Col>
                            <Col md="4" className="u-step"><span className="u-step-icon icon wb-time" aria-hidden="true"></span>
                                <div className="u-step-desc"><span className="u-step-title">Getting</span></div>
                            </Col>
                        </Row>
                        <Row className="u-steps u-steps-lg">
                            <Col md="4" className="u-step"><span className="u-step-icon icon wb-shopping-cart" aria-hidden="true"></span>
                                <div className="u-step-desc"><span className="u-step-title">Shopping</span></div>
                            </Col>
                            <Col md="4" className="u-step current"><span className="u-step-icon icon wb-pluse" aria-hidden="true"></span>
                                <div className="u-step-desc"><span className="u-step-title">Billing</span></div>
                            </Col>
                            <Col md="4" className="u-step"><span className="u-step-icon icon wb-time" aria-hidden="true"></span>
                                <div className="u-step-desc"><span className="u-step-title">Getting</span></div>
                            </Col>
                        </Row>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default StepsSizingClass;