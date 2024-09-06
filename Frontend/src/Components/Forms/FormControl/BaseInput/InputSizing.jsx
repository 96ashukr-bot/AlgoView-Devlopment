import React, { Fragment } from 'react';
import { Row, Col, Card, CardBody, Form, FormGroup, Label, Input } from 'reactstrap';
import { DefaultInput, DefaultSelect, InputSizing, LargeInput, LargeSelect, SmallInput, SmallSelect } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';
import FooterCard from '../Common/FooterCard';

const InputSizingClass = () => {
    return (
        <Fragment>
            <Card>
                <HeaderCard title={InputSizing} />
                <Form className="form theme-form">
                    <CardBody>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label className="col-form-label-sm">{LargeInput}</Label>
                                    <Input className="form-control form-control-lg" type="text" placeholder="col-form-label-lg" />
                                </FormGroup>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label>{DefaultInput}</Label>
                                    <Input className="form-control" type="text" placeholder="form-control" />
                                </FormGroup>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label className="col-form-label-sm">{SmallInput}</Label>
                                    <Input className="form-control form-control-sm" type="text" placeholder="col-form-label-sm" />
                                </FormGroup>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                                <FormGroup>
                                    <Label>{LargeSelect}</Label>
                                    <Input type="select" name="select" className="form-control form-control-lg digits">
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
                                    <Label>{DefaultSelect}</Label>
                                    <Input type="select" name="select" className="form-control digits" >
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
                                    <Label>{SmallSelect}</Label>
                                    <Input type="select" name="select" className="form-control form-control-sm digits">
                                        <option>{'1'}</option>
                                        <option>{'2'}</option>
                                        <option>{'3'}</option>
                                        <option>{'4'}</option>
                                        <option>{'5'}</option>
                                    </Input>
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

export default InputSizingClass;