import React, { Fragment } from 'react';
import { Row, Col, Card, CardBody, Form, FormGroup, Label, Input } from 'reactstrap';
import { CustomControls, CustomSelect, UploadFile } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';
import FooterCard from '../Common/FooterCard';


const CustomControlsClass = () => {
    return (
        <Fragment>
            <Card>
                <HeaderCard title={CustomControls} />
                <Form className="form theme-form">
                    <CardBody>
                        <Row>
                            <Col>
                                <FormGroup className="row">
                                    <Label className="col-sm-3 col-form-label">{UploadFile}</Label>
                                    <Col sm="9">
                                        <Input className="form-control" type="file" />
                                    </Col>
                                </FormGroup>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                                <Row>
                                    <Label className="col-sm-3 col-form-label">{CustomSelect}</Label>
                                    <Col sm="9">
                                        <Input type="select" name="select" className="form-select form-control">
                                            <option select="">{'Open this select menu'}</option>
                                            <option defaultValue="1">{'One'}</option>
                                            <option defaultValue="2">{'Two'}</option>
                                            <option defaultValue="3">{'Three'}</option>
                                        </Input>
                                    </Col>
                                </Row>
                            </Col>
                        </Row>
                    </CardBody>
                    <FooterCard footerClass="text-end" />
                </Form>
            </Card>
        </Fragment>
    );
};

export default CustomControlsClass;