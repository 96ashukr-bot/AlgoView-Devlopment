import React, { Fragment } from 'react';
import { Row, Col, Card, CardHeader, CardBody, Media, Form, Label, Input, CardFooter } from 'reactstrap';
import { H5, H6, P, Btn } from '../../../../AbstractElements';
import { COD, Fast, Free, VerticalStyle, Local, XYZSeller, ABCSeller, Standard, DeliveryOption, BuyingOption } from '../../../../Constant';
import { Submit, Cancel } from "../../../../Constant";

const VerticalClass = () => {
    return (
        <Fragment>
            <Col sm="12" xxl="6" className="box-col-12">
                <Card className="height-equal">
                    <CardHeader>
                        <H5>{VerticalStyle}</H5><span>{'For Create inline megaoption add'} <code>{'.mega-vertical'}</code> {'class in form tag'}</span>
                    </CardHeader>
                    <CardBody>
                        <Form className="mega-vertical">
                            <Row>
                                <Col sm="12">
                                    <P attrPara={{ className: 'mega-title m-b-5' }} >{DeliveryOption}</P>
                                </Col>
                                <Col sm="6">
                                    <Card>
                                        <Media className="p-20">
                                            <div className="radio radio-primary me-3">
                                                <Input id="radio23" type="radio" name="radio1" value="option1" />
                                                <Label for="radio23"></Label>
                                            </div>
                                            <Media body>
                                                <H6 attrH6={{ className: 'mt-0 mega-title-badge' }} >{COD}<span className="badge badge-primary pull-right digits">{'50 INR'}</span></H6>
                                                <P>{'Estimated 10 to 15 Day Shipping ( Duties end tax may be due delivery )'}</P>
                                            </Media>
                                        </Media>
                                    </Card>
                                </Col>
                                <Col sm="6">
                                    <Card>
                                        <Media className="p-20">
                                            <div className="radio radio-secondary me-3">
                                                <Input id="radio24" type="radio" name="radio1" value="option1" />
                                                <Label for="radio24"></Label>
                                            </div>
                                            <Media body>
                                                <H6 attrH6={{ className: 'mt-0 mega-title-badge' }} >{Fast} <span className="badge badge-secondary pull-right digits">{'100 INR'}</span></H6>
                                                <P>{'Estimated 10 to 12 Day Shipping ( Duties end tax may be due delivery )'}</P>
                                            </Media>
                                        </Media>
                                    </Card>
                                </Col>
                                <Col sm="6">
                                    <Card>
                                        <Media className="p-20">
                                            <div className="radio radio-success me-3">
                                                <Input id="radio25" type="radio" name="radio1" value="option1" />
                                                <Label for="radio25"></Label>
                                            </div>
                                            <Media body>
                                                <H6 attrH6={{ className: 'mt-0 mega-title-badge' }} >{Standard} <span className="badge badge-success pull-right digits">{'80 INR'}</span></H6>
                                                <P>{'Estimated 3 to 5 Day Shipping ( Duties end tax may be due delivery )'}</P>
                                            </Media>
                                        </Media>
                                    </Card>
                                </Col>
                                <Col sm="6">
                                    <Card>
                                        <Media className="p-20">
                                            <div className="radio radio-info me-3">
                                                <Input id="radio5" type="radio" name="radio1" value="option1" />
                                                <Label for="radio5"></Label>
                                            </div>
                                            <Media body>
                                                <H6 attrH6={{ className: 'mt-0 mega-title-badge' }} >{Local} <span className="badge badge-info pull-right digits">{Free}</span></H6>
                                                <P>{'Estimated 3 to 5 Day Shipping ( Duties end taxes may be due upon delivery )'}</P>
                                            </Media>
                                        </Media>
                                    </Card>
                                </Col>
                                <Col sm="12">
                                    <P attrPara={{ className: 'mega-title m-b-5' }} >{BuyingOption}</P>
                                </Col>
                                <Col sm="6">
                                    <Card>
                                        <Media className="p-20">
                                            <div className="radio radio-warning me-3">
                                                <Input id="radio26" type="radio" name="radio1" value="option1" />
                                                <Label for="radio26"></Label>
                                            </div>
                                            <Media body>
                                                <H6 attrH6={{ className: 'mt-0 mega-title-badge' }} >{XYZSeller}<span className="badge badge-warning pull-right digits">{'250 INR'}</span></H6>
                                                <P attrPara={{ className: 'rating-star-wrapper' }} ><i className="icofont icofont-star txt-warning"></i><i className="icofont icofont-star txt-warning"></i><i className="icofont icofont-star txt-warning"></i><i className="icofont icofont-star txt-warning"></i><i className="icofont icofont-star txt-warning m-r-5"></i>{'5 start rating'}</P>
                                            </Media>
                                        </Media>
                                    </Card>
                                </Col>
                                <Col sm="6">
                                    <Card className="mb-0">
                                        <Media className="p-20">
                                            <div className="radio radio-danger me-3">
                                                <Input id="radio27" type="radio" name="radio1" value="option1" />
                                                <Label for="radio27"></Label>
                                            </div>
                                            <Media body>
                                                <H6 attrH6={{ className: 'mt-0 mega-title-badge' }} >{ABCSeller}<span className="badge badge-danger pull-right digits">{'150 INR'}</span></H6>
                                                <P attrPara={{ className: 'rating-star-wrapper' }} ><i className="icofont icofont-star txt-warning"></i><i className="icofont icofont-star"></i><i className="icofont icofont-star"></i><i className="icofont icofont-star"></i><i className="icofont icofont-star m-r-5"></i>{'1 start rating'}</P>
                                            </Media>
                                        </Media>
                                    </Card>
                                </Col>
                            </Row>
                        </Form>
                    </CardBody>
                    <CardFooter className="text-end">
                        <Btn attrBtn={{ color: "primary", className: "m-r-15 d-inline-flex", type: "submit" }} >{Submit}</Btn>
                        <Btn attrBtn={{ color: "light", className: 'd-inline-flex', type: "submit" }} >{Cancel}</Btn>
                    </CardFooter>
                </Card>
            </Col>
        </Fragment>
    );
};

export default VerticalClass;