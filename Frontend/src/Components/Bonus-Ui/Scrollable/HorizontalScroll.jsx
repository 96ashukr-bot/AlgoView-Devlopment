import React, { Fragment } from 'react';
import { Card, CardBody, Col, Row } from 'reactstrap';
import HeaderCard from '../../Common/Component/HeaderCard';
import { P } from '../../../AbstractElements';
import { horizontalscroll, Modalcontent, Pilltabcontent } from '../../../Constant';
import Scrollbars from 'react-custom-scrollbars-2';

const HorizontalScroll = () => {
    return (
        <Fragment>
            <Col sm="6">
                <Card>
                    <HeaderCard title={horizontalscroll} />
                    <CardBody>
                        <div className="scroll-bar-wrap">
                            <Scrollbars className="horizontal-scroll" style={{width: '100%',height:300}}>
                                <Row>
                                    <Col sm="3">
                                        <P>{Modalcontent}</P>
                                    </Col>
                                    <Col sm="3">
                                        <P>{Pilltabcontent}</P>
                                    </Col>
                                    <Col sm="3">
                                        <P>{Pilltabcontent}</P>
                                    </Col>
                                    <Col sm="3">
                                        <P>{Pilltabcontent}</P>
                                    </Col>
                                </Row>
                            </Scrollbars>
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default HorizontalScroll;