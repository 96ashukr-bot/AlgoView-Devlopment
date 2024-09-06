import React, { Fragment } from 'react';
import { Row, Col, Card, CardBody, Form, FormGroup, Label, Input } from 'reactstrap';
import { EdgesInputStyle, EmailAddress, ExampleMultipleSelect, ExampleSelect, ExampleTextarea, Password } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';
import FooterCard from '../Common/FooterCard';

const EdgesInputStyleClass = () => {
    return (
        <Fragment>
            <Card>
                <HeaderCard title={EdgesInputStyle} />
                <Form className="form theme-form">
                    <CardBody>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label>{EmailAddress}</Label>
                                    <Input className="form-control btn-pill" id="exampleFormControlInput5" type="email" placeholder="name@example.com" />
                                </FormGroup>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label>{Password}</Label>
                                    <Input className="form-control btn-pill" id="exampleInputPassword6" type="password" placeholder="Password" />
                                </FormGroup>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label>{ExampleSelect}</Label>
                                    <Input type="select" name="select" className="form-control btn-pill digits" id="exampleFormControlSelect7">
                                        <option>{'1'}</option>
                                        <option>{'2'}</option>
                                        <option>{'3'}</option>
                                        <option>{'4'}</option>
                                        <option>{'5'}</option>
                                    </Input>
                                </FormGroup>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label>{ExampleMultipleSelect}</Label>
                                    <Input type="select" name="select" className="form-control btn-pill digits" multiple="">
                                        <option>{'1'}</option>
                                        <option>{'2'}</option>
                                        <option>{'3'}</option>
                                        <option>{'4'}</option>
                                        <option>{'5'}</option>
                                    </Input>
                                </FormGroup>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                                <div>
                                    <Label htmlFor="exampleFormControlTextarea9">{ExampleTextarea}</Label>
                                    <Input type="textarea" className="form-control btn-pill" rows="3" />
                                </div>
                            </Col>
                        </Row>
                    </CardBody>
                    <FooterCard footerClass="text-end" />
                </Form>
            </Card>
        </Fragment>
    );
};

export default EdgesInputStyleClass;