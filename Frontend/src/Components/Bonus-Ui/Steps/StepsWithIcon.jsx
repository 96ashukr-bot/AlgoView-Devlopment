import React, { Fragment } from 'react';
import { Card, CardBody, Col, Row } from 'reactstrap';
import HeaderCard from '../../Common/Component/HeaderCard';

const StepsWithIcon = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <HeaderCard title="Step with icon" />
                    <CardBody>
                        <Row className="u-steps">
                            <Col md="4" className="u-step"><span className="u-step-icon icon-shopping-cart-full" aria-hidden="true"></span>
                                <div className="u-step-desc"><span className="u-step-title">Shopping</span></div>
                            </Col>
                            <Col md="4" className="u-step current"><span className="u-step-icon icon-notepad" aria-hidden="true"></span>
                                <div className="u-step-desc"><span className="u-step-title">Billing</span></div>
                            </Col>
                            <Col md="4" className="u-step"><span className="u-step-icon icon-time" aria-hidden="true"></span>
                                <div className="u-step-desc"><span className="u-step-title">Getting</span></div>
                            </Col>
                        </Row>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default StepsWithIcon;