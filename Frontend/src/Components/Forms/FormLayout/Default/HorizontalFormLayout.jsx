import React, { Fragment } from 'react';
import { Row, Col, Card, CardHeader, CardBody, Form, FormGroup, Label, Input } from 'reactstrap';
import { H5 } from '../../../../AbstractElements';
import { Email, Password, Website, HorizontalFormLayout, Option, ContactNumber, CompanyName, Checkboxes, Radios, Disabled } from '../../../../Constant';
import FooterCard from '../../FormControl/Common/FooterCard';

const HorizontalFormLayoutClass = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <H5>{HorizontalFormLayout}</H5><span>{'Using the'} <a href="#javascript">{'card'}</a> {'component, you can extend the default collapse behavior to create an accordion.'}</span>
                    </CardHeader>
                    <CardBody>
                        <Form className="theme-form">
                            <FormGroup className="row">
                                <Label className="col-sm-3 col-form-label" htmlFor="inputEmail3">{Email}</Label>
                                <Col sm="9">
                                    <Input className="form-control" type="email" placeholder="Email" />
                                </Col>
                            </FormGroup>
                            <FormGroup className="row">
                                <Label className="col-sm-3 col-form-label" htmlFor="inputPassword3">{Password}</Label>
                                <Col sm="9">
                                    <Input className="form-control" type="password" placeholder="Password" />
                                </Col>
                            </FormGroup>
                            <FormGroup className="row">
                                <Label className="col-sm-3 col-form-label" htmlFor="inputPassword3">{ContactNumber}</Label>
                                <Col sm="9">
                                    <Input className="form-control" type="number" placeholder="Contact" />
                                </Col>
                            </FormGroup>
                            <FormGroup className="row">
                                <Label className="col-sm-3 col-form-label" htmlFor="inputPassword3">{CompanyName}</Label>
                                <Col sm="9">
                                    <Input className="form-control" type="text" placeholder="Company name" />
                                </Col>
                            </FormGroup>
                            <FormGroup className="row">
                                <Label className="col-sm-3 col-form-label">{Website}</Label>
                                <Col sm="9">
                                    <Input className="form-control" type="url" placeholder="Website" />
                                </Col>
                            </FormGroup>
                            <FormGroup tag="fieldset">
                                <Row>
                                    <Label className="col-form-label col-sm-3 pt-0">{Radios}</Label>
                                    <Col sm="9">
                                        <div className="radio radio-primary ms-2">
                                            <Input type="radio" name="radio1" id="radio1" value="option1" />
                                            <Label for="radio1">{Option} {'1'}</Label>
                                        </div>
                                        <div className="radio radio-primary ms-2">
                                            <Input type="radio" name="radio1" id="radio2" value="option1" />
                                            <Label for="radio2">{Option} {'2'}</Label>
                                        </div>
                                        <div className="radio radio-primary ms-2">
                                            <Input type="radio" name="radio1" value="option1" disabled />
                                            <Label>{Disabled}</Label>
                                        </div>
                                        <div className="radio radio-primary ms-2">
                                            <Input type="radio" name="radio1" value="option1" defaultChecked />
                                            <Label>{Option} {'3'}</Label>
                                        </div>
                                        <div className="radio radio-primary ms-2">
                                            <Input type="radio" name="radio1" id="radio3" value="option1" />
                                            <Label for="radio3">{Option} {'4'}</Label>
                                        </div>
                                    </Col>
                                </Row>
                            </FormGroup>
                            <div className="form-group row mb-0">
                                <Label className="col-sm-3 col-form-Label pb-0">{Checkboxes}</Label>
                                <Col sm="9">
                                    <div className="form-group m-checkbox-inline mb-0">
                                        <div className="checkbox checkbox-primary">
                                            <Input id="inline-form-1" type="checkbox" />
                                            <Label className="mb-0" htmlFor="inline-form-1">{Option} {'1'}</Label>
                                        </div>
                                        <div className="checkbox checkbox-primary">
                                            <Input id="inline-form-2" type="checkbox" />
                                            <Label className="mb-0" htmlFor="inline-form-2">{Option} {'2'}</Label>
                                        </div>
                                    </div>
                                </Col>
                            </div>
                        </Form>
                    </CardBody>
                    <FooterCard />
                </Card>
            </Col>
        </Fragment>
    );
};

export default HorizontalFormLayoutClass;