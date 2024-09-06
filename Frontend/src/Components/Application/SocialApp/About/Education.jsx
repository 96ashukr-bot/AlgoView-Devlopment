import React, { Fragment } from 'react';
import { MoreVertical } from 'react-feather';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';
import { H5, P } from '../../../../AbstractElements';

const Education = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader className="social-header">
                        <H5><span>{"Education and Employement"}</span><span className="pull-right"><MoreVertical /></span></H5>
                    </CardHeader>
                    <CardBody>
                        <Row className="details-about">
                            <Col sm="6">
                                <div className="your-details"><span className="f-w-600">{"The New College of Design"}</span>
                                    <P>{"2001 - 2006"}</P>
                                    <P>{"Breaking Good, RedDevil, People of Interest, The Running Dead, Found, American Guy."}</P>
                                </div>
                            </Col>
                            <Col sm="6">
                                <div className="your-details your-details-xs"><span className="f-w-600">{"Digital Design Intern"}</span>
                                    <P>{"2006-2008"}</P>
                                    <P>{"Digital Design Intern for the “Multimedz” agency. Was in charge of the communication with the clients."}</P>
                                </div>
                            </Col>
                        </Row>
                        <Row className="details-about">
                            <Col sm="6">
                                <div className="your-details"><span className="f-w-600">{"Rembrandt Institute"}</span>
                                    <P>{"2008"}</P>
                                    <P>{"Five months Digital Illustration course. Professor: Leonardo Stagg."}</P>
                                </div>
                            </Col>
                            <Col sm="6">
                                <div className="your-details your-details-xs"><span className="f-w-600">{"UI/UX Designer"}</span>
                                    <P>{"2001 - 2006"}</P>
                                    <P>{"Breaking Good, RedDevil, People of Interest, The Running Dead, Found, American Guy."}</P>
                                </div>
                            </Col>
                        </Row>
                        <Row className="details-about">
                            <Col sm="6">
                                <div className="your-details"><span className="f-w-600">{"The Digital College"}</span>
                                    <P>{"2010"}</P>
                                    <P>{"6 months intensive Motion Graphics course. After Effects and Premire. Professor: Donatello Urtle."}</P>
                                </div>
                            </Col>
                            <Col sm="6">
                                <div className="your-details your-details-xs"><span className="f-w-600">{"The New College of Design"}</span>
                                    <P>{"2008 - 2013"}</P>
                                    <P>{"UI/UX Designer for the “Daydreams” agency."}</P>
                                </div>
                            </Col>
                        </Row>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}

export default Education;