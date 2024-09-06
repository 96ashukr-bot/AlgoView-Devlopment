import React, { Fragment } from 'react';
import { Row, Col, Card, CardBody, Form, FormGroup, Label, Input } from 'reactstrap';
import { Disabled, EmailAddress, ExampleMultipleSelect, ExampleSelect, ExampleTextarea, Password, SolidInputStyle } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';
import FooterCard from '../Common/FooterCard';

const SolidInputStyleClass = () => {
    return (
        <Fragment>
            <Card>
                <HeaderCard title={SolidInputStyle} />
                <Form className="form theme-form">
                    <CardBody>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label>{EmailAddress}</Label>
                                    <Input className="form-control" type="email" placeholder="name@example.com" />
                                </FormGroup>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label>{Password}</Label>
                                    <Input className="form-control" type="password" placeholder="Password" />
                                </FormGroup>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label>{Disabled}</Label>
                                    <Input className="form-control" type="text" disabled="" placeholder="Disabled" />
                                </FormGroup>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label>{ExampleSelect}</Label>
                                    <Input type="select" name="select" className="form-control digits">
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
                                    <Input type="select" name="select" className="form-control digits" multiple="">
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
                                    <Label >{ExampleTextarea}</Label>
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

export default SolidInputStyleClass;