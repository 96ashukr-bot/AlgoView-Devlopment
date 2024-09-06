import React, { Fragment } from 'react';
import { Card, CardBody, Col, Row } from 'reactstrap';
import HeaderCard from '../../Common/Component/HeaderCard';

const PearlsStepsClass = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <HeaderCard title='Pearls Steps with icon' />
                    <CardBody>
                        <Row>
                            <div className="u-pearl done col-4">
                                <div className="u-pearl-icon"><i className="icon-shopping-cart" aria-hidden="true"></i></div><span className="u-pearl-title">Account Info</span>
                            </div>
                            <div className="u-pearl current col-4">
                                <div className="u-pearl-icon"><i className="icon-write" aria-hidden="true"></i></div><span className="u-pearl-title">Billing Info</span>
                            </div>
                            <div className="u-pearl col-4">
                                <div className="u-pearl-icon"><i className="icon-check" aria-hidden="true"></i></div><span className="u-pearl-title">Confirmation</span>
                            </div>
                        </Row>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default PearlsStepsClass;