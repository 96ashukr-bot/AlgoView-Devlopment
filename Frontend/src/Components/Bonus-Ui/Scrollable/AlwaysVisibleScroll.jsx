import React, { Fragment } from 'react';
import { Card, CardBody, Col, Row } from 'reactstrap';
import { P } from '../../../AbstractElements';
import HeaderCard from '../../Common/Component/HeaderCard';
import { scrollpara, scrollpara1, scrollpara2, scrollpara3 } from '../../../Constant';

const AlwaysVisibleScroll = () => {
    return (
        <Fragment>
            <Col sm="6">
                <Card>
                    <HeaderCard title="Always Visible Scroll" />
                    <CardBody>
                        <div className="scroll-bar-wrap">
                            <div className="visible-scroll always-visible scroll-demo">
                                <div className="horz-scroll-content">
                                    <Row>
                                        <Col sm="3">
                                            <P>{scrollpara}</P>
                                            <P>{scrollpara1}</P>
                                            <P>{scrollpara2}</P>
                                        </Col>
                                        <Col sm="3">
                                            <P>{scrollpara2}</P>
                                            <P>{scrollpara1}</P>
                                            <P>{scrollpara3}</P>
                                        </Col>
                                        <Col sm="3">
                                            <P>{scrollpara}</P>
                                            <P>{scrollpara1}</P>
                                            <P>{scrollpara2}</P>
                                        </Col>
                                        <Col sm="3">
                                            <P>{scrollpara2}</P>
                                            <P>{scrollpara1}</P>
                                            <P>{scrollpara3}</P>
                                        </Col>
                                    </Row>
                                </div>
                            </div>
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default AlwaysVisibleScroll;