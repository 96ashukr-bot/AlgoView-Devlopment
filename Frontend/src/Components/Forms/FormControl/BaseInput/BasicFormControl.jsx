import React, { Fragment } from 'react';
import { Row, Col, Card, CardBody, Form, FormGroup, Label, Input } from 'reactstrap';
import { BasicFormControl, EmailAddress, ExampleMultipleSelect, ExampleSelect, ExampleTextarea, Password } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';
import FooterCard from '../Common/FooterCard';

const BasicFormControlClass = () => {
    return (
        <Fragment>
            <Card>
                <HeaderCard title={BasicFormControl} />
                <Form className="form theme-form">
                    <CardBody>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label htmlFor="exampleFormControlInput1">{EmailAddress}</Label>
                                    <Input className="form-control" type="email" placeholder="name@example.com" />
                                </FormGroup>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label htmlFor="exampleInputPassword2">{Password}</Label>
                                    <Input className="form-control" type="password" placeholder="Password" />
                                </FormGroup>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label htmlFor="exampleFormControlSelect9">{ExampleSelect}</Label>
                                    <Input type="select" name="select" className="form-control digits" defaultValue="1">
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
                                    <Label htmlFor="exampleFormControlSelect3">{ExampleMultipleSelect}</Label>
                                    <Input type="select" name="select" className="form-control digits" multiple="" defaultValue="1">
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
                                    <Label>{ExampleTextarea}</Label>
                                    <Input type="textarea" className="form-control" rows="3" />
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

export default BasicFormControlClass;