import React, { Fragment } from 'react';
import { Row, Col, Card, CardHeader, CardBody, Media, Form, Label, Input } from 'reactstrap';
import { H5, H6, P } from '../../../../AbstractElements';
import { COD, Fast, InlineStyle, Free, Local, Standard } from '../../../../Constant';
import FooterCard from '../Common/FooterCard';

const InlineClass = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <H5>{InlineStyle}</H5><span>{'For Create inline megaoption add'} <code>{'.mega-inline'}</code> {'class in form tag'}</span>
                    </CardHeader>
                    <CardBody className="megaoptions-border-space-sm">
                        <Form className="mega-inline">
                            <Row>
                                <Col sm="6">
                                    <Card>
                                        <Media className="p-20">
                                            <div className="radio radio-primary me-3">
                                                <Input id="radio19" type="radio" name="radio1" value="option1" />
                                                <Label for="radio19"></Label>
                                            </div>
                                            <Media body>
                                                <h6 className="mt-0 mega-title-badge">{COD}<span className="badge badge-primary pull-right digits">{'50 INR'}</span></h6>
                                                <p>{'Estimated 14-20 Day Shipping ( Duties end taxes may be due upon delivery )'}</p>
                                            </Media>
                                        </Media>
                                    </Card>
                                </Col>
                                <Col sm="6">
                                    <Card>
                                        <Media className="p-20">
                                            <div className="radio radio-secondary me-3">
                                                <Input id="radio20" type="radio" name="radio1" value="option1" />
                                                <Label for="radio20"></Label>
                                            </div>
                                            <Media body>
                                                <H6 attrH6={{ className: 'mt-0 mega-title-badge' }} >{Fast}<span className="badge badge-secondary pull-right digits">{'100 INR'}</span></H6>
                                                <P>{'Estimated 1 Day Shipping ( Duties end taxes may be due upon delivery )'}</P>
                                            </Media>
                                        </Media>
                                    </Card>
                                </Col>
                                <Col sm="6">
                                    <Card>
                                        <Media className="p-20">
                                            <div className="radio radio-secondary me-3">
                                                <Input id="radio21" type="radio" name="radio1" value="option1" />
                                                <Label for="radio21"></Label>
                                            </div>
                                            <Media body>
                                                <H6 attrH6={{ className: 'mt-0 mega-title-badge' }}>{Standard}<span className="badge badge-secondary pull-right digits">{'80 INR'}</span></H6>
                                                <P>{'Estimated 3 Day Shipping ( Duties end taxes may be due upon delivery )'}</P>
                                            </Media>
                                        </Media>
                                    </Card>
                                </Col>
                                <Col sm="6">
                                    <Card>
                                        <Media className="p-20">
                                            <div className="radio radio-primary me-3">
                                                <Input id="radio22" type="radio" name="radio1" value="option1" />
                                                <Label for="radio22"></Label>
                                            </div>
                                            <Media body>
                                                <H6 attrH6={{ className: 'mt-0 mega-title-badge' }}>{Local} <span className="badge badge-primary pull-right digits">{Free}</span></H6>
                                                <P>{'Estimated 15 Day Shipping ( Duties end taxes may be due upon delivery )'}</P>
                                            </Media>
                                        </Media>
                                    </Card>
                                </Col>
                            </Row>
                        </Form>
                    </CardBody>
                    <FooterCard />
                </Card>
            </Col>
        </Fragment>
    );
};

export default InlineClass;