import React, { Fragment } from 'react';
import { Row, Col, Card, CardBody, Form, FormGroup, Label, Input, InputGroup,  InputGroupText } from 'reactstrap';
import { BasicInputGroups, LeftAddon, RightAddon, JointAddon, LeftRightAddon, SolidStyle, FlatStyle, RaiseStyle } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';
import FooterCard from '../Common/FooterCard';


const BasicInputCard2 = () => {
    return (
        <Fragment>
            <Card>
                <HeaderCard title={BasicInputGroups} />
                <CardBody>
                    <Row>
                        <Col>
                            <Form>
                                <FormGroup className=" m-form__group">
                                    <Label>{LeftAddon}</Label>
                                    <InputGroup>
                                        <InputGroupText><i className="icofont icofont-pencil-alt-5"></i></InputGroupText>
                                        <Input className="form-control" type="text" placeholder="Email" />
                                    </InputGroup>
                                </FormGroup>
                                <FormGroup className="">
                                    <Label>{RightAddon}</Label>
                                    <InputGroup>
                                        <Input className="form-control" type="text" placeholder="Recipient's username" aria-label="Recipient's username" />
                                        <InputGroupText><i className="icofont icofont-ui-dial-phone"></i></InputGroupText>
                                    </InputGroup>
                                </FormGroup>
                                <FormGroup className="">
                                    <Label>{JointAddon}</Label>
                                    <InputGroup>
                                        <InputGroupText><i className="icofont icofont-unlink"></i></InputGroupText><InputGroupText>{'0.00'}</InputGroupText>
                                        <Input className="form-control" type="text" aria-label="Amount (to the nearest dollar)" />
                                    </InputGroup>
                                </FormGroup>
                                <FormGroup className="">
                                    <Label>{LeftRightAddon}</Label>
                                    <InputGroup className="mb-3">
                                        <InputGroupText><i className="icofont icofont-ui-zoom-out"></i></InputGroupText>
                                        <Input className="form-control" type="text" aria-label="Amount (to the nearest dollar)" />
                                        <InputGroupText><i className="icofont icofont-ui-zoom-in"></i></InputGroupText>
                                    </InputGroup>
                                </FormGroup>
                                <FormGroup className=" input-group-solid">
                                    <Label>{SolidStyle}</Label>
                                    <InputGroup>
                                        <InputGroupText><i className="icofont icofont-users"></i></InputGroupText>
                                        <Input className="form-control" type="text" placeholder="999999" />
                                    </InputGroup>
                                </FormGroup>
                                <FormGroup className=" input-group-square">
                                    <Label>{FlatStyle}</Label>
                                    <InputGroup>
                                        <InputGroupText><i className="icofont icofont-credit-card"></i></InputGroupText>
                                        <Input className="form-control" type="text" placeholder="" />
                                    </InputGroup>
                                </FormGroup>
                                <FormGroup className=" input-group-square">
                                    <Label>{RaiseStyle}</Label>
                                    <InputGroup>
                                        <InputGroupText><i className="icofont icofont-download"></i></InputGroupText>
                                        <Input className="form-control input-group-air" type="text" placeholder="https://www.example.com" />
                                    </InputGroup>
                                </FormGroup>
                                <div>
                                    <Label>{LeftRightAddon}</Label>
                                    <InputGroup className="pill-input-group">
                                        <InputGroupText><i className="icofont icofont-ui-copy"></i></InputGroupText>
                                        <Input className="form-control" type="text" aria-label="Amount (to the nearest dollar)" />
                                        <InputGroupText><i className="icofont icofont-stock-search"></i></InputGroupText>
                                    </InputGroup>
                                </div>
                            </Form>
                        </Col>
                    </Row>
                </CardBody>
                <FooterCard />
            </Card>
        </Fragment>
    );
};

export default BasicInputCard2;