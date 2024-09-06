import React, { Fragment } from 'react';
import { Codepen, FileText, Youtube } from 'react-feather';
import { Card, CardBody, Col, Media, Row } from 'reactstrap';
import { H5, H6, P } from '../../../AbstractElements';

const LatestArticlesClass = () => {
    return (
        <Fragment>
            <Col lg="12">
                <div className="header-faq">
                    <H5 attrH5={{ className: "mb-0" }} >{"Latest articles and videos"}</H5>
                </div>
                <Row>
                    <Col xl="4" md="6">
                        <Row>
                            <Col sm="12">
                                <Card>
                                    <CardBody>
                                        <div className="media"><Codepen className="m-r-30" />
                                            <Media body>
                                                <H6 attrH6={{ className: "f-w-600" }} >{"Using Video"}</H6>
                                                <P>{"Cras dapibus. Vivamus elementum semper nisi. Aenean vulputate eleifend tellus."}</P>
                                            </Media>
                                        </div>
                                    </CardBody>
                                </Card>
                            </Col>
                            <Col sm="12">
                                <Card>
                                    <CardBody>
                                        <div className="media"><Codepen className="m-r-30" />
                                            <Media body>
                                                <H6 attrH6={{ className: "f-w-600" }}>{"Vel illum qu"}</H6>
                                                <P>{"Cras dapibus. Vivamus elementum semper nisi. Aenean vulputate eleifend tellus."}</P>
                                            </Media>
                                        </div>
                                    </CardBody>
                                </Card>
                            </Col>
                            <Col sm="12">
                                <Card>
                                    <CardBody>
                                        <div className="media"><Codepen className="m-r-30" />
                                            <Media body>
                                                <H6 attrH6={{ className: "f-w-600" }}>{"Cum sociis natoqu"}</H6>
                                                <P>{"Cras dapibus. Vivamus elementum semper nisi. Aenean vulputate eleifend tellus. "}</P>
                                            </Media>
                                        </div>
                                    </CardBody>
                                </Card>
                            </Col>
                        </Row>
                    </Col>
                    <Col xl="4" md="6">
                        <Row>
                            <Col sm="12">
                                <Card>
                                    <CardBody>
                                        <div className="media"><FileText className="m-r-30" />
                                            <Media body>
                                                <H6 attrH6={{ className: "f-w-600" }}>{"Donec pede justo"}</H6>
                                                <P>{" Cras dapibus. Vivamus elementum semper nisi. Aenean vulputate eleifend tellus. "}</P>
                                            </Media>
                                        </div>
                                    </CardBody>
                                </Card>
                            </Col>
                            <Col sm="12">
                                <Card>
                                    <CardBody>
                                        <div className="media"><FileText className="m-r-30" />
                                            <Media body>
                                                <H6 attrH6={{ className: "f-w-600" }}>{"Nam quam nunc"}</H6>
                                                <P>{" Cras dapibus. Vivamus elementum semper nisi. Aenean vulputate eleifend tellus."}</P>
                                            </Media>
                                        </div>
                                    </CardBody>
                                </Card>
                            </Col>
                            <Col sm="12">
                                <Card>
                                    <CardBody>
                                        <div className="media">
                                            <FileText className="m-r-30" />
                                            <Media body>
                                                <H6 attrH6={{ className: "f-w-600" }}>{"Using Video"} </H6>
                                                <P>{"Cras dapibus. Vivamus elementum semper nisi. Aenean vulputate eleifend tellus."}</P>
                                            </Media>
                                        </div>
                                    </CardBody>
                                </Card>
                            </Col>
                        </Row>
                    </Col>
                    <Col xl="4">
                        <Row>
                            <Col xl="12" md="6">
                                <Card>
                                    <CardBody>
                                        <div className="media"><Youtube className="m-r-30" />
                                            <Media body>
                                                <H6 attrH6={{ className: "f-w-600" }}>{"Vel illum qu"}</H6>
                                                <P>{"Cras dapibus. Vivamus elementum semper nisi. Aenean vulputate eleifend tellus."}</P>
                                            </Media>
                                        </div>
                                    </CardBody>
                                </Card>
                            </Col>
                            <Col xl="12" md="6">
                                <Card>
                                    <CardBody>
                                        <div className="media"><Youtube className="m-r-30" />
                                            <Media body>
                                                <H6 attrH6={{ className: "f-w-600" }}>{"Cum sociis natoqu"}</H6>
                                                <P>{"Cras dapibus. Vivamus elementum semper nisi. Aenean vulputate eleifend tellus."}</P>
                                            </Media>
                                        </div>
                                    </CardBody>
                                </Card>
                            </Col>
                            <Col xl="12">
                                <Card>
                                    <CardBody>
                                        <div className="media"><Youtube className="m-r-30" />
                                            <Media body>
                                                <H6 attrH6={{ className: "f-w-600" }}>{"Donec pede justo"}</H6>
                                                <P>{"Cras dapibus. Vivamus elementum semper nisi. Aenean vulputate eleifend tellus."}</P>
                                            </Media>
                                        </div>
                                    </CardBody>
                                </Card>
                            </Col>
                        </Row>
                    </Col>
                </Row>
            </Col>
        </Fragment>
    )
}

export default LatestArticlesClass;