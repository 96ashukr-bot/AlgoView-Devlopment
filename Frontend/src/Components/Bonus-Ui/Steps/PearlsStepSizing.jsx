import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';
import { H5 } from '../../../AbstractElements';

const PearlsStepSizingClass = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <H5>Pearls Step Sizing</H5><span>A Pearls step with classname <code>.u-pearls-xs</code><code>.u-pearls-sm</code><code>.u-pearls-lg</code></span>
                    </CardHeader>
                    <CardBody>
                        <Row className="u-pearls-xs mb-5">
                            <div className="u-pearl done col-4"><span className="u-pearl-number">1</span><span className="u-pearl-title">Account Info</span></div>
                            <div className="u-pearl current col-4"><span className="u-pearl-number">2</span><span className="u-pearl-title">Billing Info</span></div>
                            <div className="u-pearl col-4"><span className="u-pearl-number">3</span><span className="u-pearl-title">Confirmation</span></div>
                        </Row>
                        <Row className="u-pearls-sm mb-5">
                            <div className="u-pearl done col-4"><span className="u-pearl-number">1</span><span className="u-pearl-title">Account Info</span></div>
                            <div className="u-pearl current col-4"><span className="u-pearl-number">2</span><span className="u-pearl-title">Billing Info</span></div>
                            <div className="u-pearl col-4"><span className="u-pearl-number">3</span><span className="u-pearl-title">Confirmation</span></div>
                        </Row>
                        <Row className="mb-5">
                            <div className="u-pearl done col-4"><span className="u-pearl-number">1</span><span className="u-pearl-title">Account Info</span></div>
                            <div className="u-pearl current col-4"><span className="u-pearl-number">2</span><span className="u-pearl-title">Billing Info</span></div>
                            <div className="u-pearl col-4"><span className="u-pearl-number">3</span><span className="u-pearl-title">Confirmation</span></div>
                        </Row>
                        <Row className="u-pearls-lg">
                            <div className="u-pearl done col-4"><span className="u-pearl-number">1</span><span className="u-pearl-title">Account Info</span></div>
                            <div className="u-pearl current col-4"><span className="u-pearl-number">2</span><span className="u-pearl-title">Billing Info</span></div>
                            <div className="u-pearl col-4"><span className="u-pearl-number">3</span><span className="u-pearl-title">Confirmation</span></div>
                        </Row>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default PearlsStepSizingClass;