import React, { Fragment } from 'react';
import { Row, Col, Card, CardBody, Form, FormGroup, Label, Input } from 'reactstrap';
import { FlatInputStyle, EmailAddress, ExampleMultipleSelect, ExampleSelect, ExampleTextarea, Password } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';
import FooterCard from '../Common/FooterCard';

const FlatInputStyleClass = () => {
    return (
        <Fragment>
            <Card>
                <HeaderCard title={FlatInputStyle} />
                <Form className="form theme-form">
                    <CardBody>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label>{EmailAddress}</Label>
                                    <Input className="form-control btn-square" type="email" placeholder="name@example.com" />
                                </FormGroup>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label>{Password}</Label>
                                    <Input className="form-control btn-square" type="password" placeholder="Password" />
                                </FormGroup>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label>{ExampleSelect}</Label>
                                    <Input type="select" name="select" className="form-control btn-square digits" >
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
                                    <Input type="select" name="select" className="form-control btn-square digits" multiple="">
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
                                    <Input type="textarea" className="form-control btn-square" rows="3" />
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

export default FlatInputStyleClass;