import React, { Fragment } from 'react';
import { Card, CardBody, Col, Row } from 'reactstrap';
import { P } from '../../../AbstractElements';
import HeaderCard from '../../Common/Component/HeaderCard';

const VerticalStepClass = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <HeaderCard title="Vertical Step" />
                    <CardBody>
                        <Row>
                            <Col lg="4">
                                <div className="u-steps u-steps-vertical">
                                    <div className="u-step"><span className="u-step-number">1</span>
                                        <div className="u-step-desc"><span className="u-step-title">Shopping</span>
                                            <P> Choose what you want</P>
                                        </div>
                                    </div>
                                    <div className="u-step current"><span className="u-step-number">2</span>
                                        <div className="u-step-desc"><span className="u-step-title">Billing</span>
                                            <P>Pay for the bill</P>
                                        </div>
                                    </div>
                                    <div className="u-step"><span className="u-step-number">3</span>
                                        <div className="u-step-desc"><span className="u-step-title">Getting</span>
                                            <P>Waiting for the goods</P>
                                        </div>
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

export default VerticalStepClass;