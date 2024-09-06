import React, { Fragment } from 'react';
import { Col, Card, CardHeader, CardBody, Form, FormGroup, Label, Input } from 'reactstrap';
import { H5 } from '../../../../AbstractElements';
import { DefaultFormLayout, EmailAddress, Password } from '../../../../Constant';
import FooterCard from '../../FormControl/Common/FooterCard';

const DefaultFormLayoutClass = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <H5>{DefaultFormLayout}</H5><span>{'Using the'} <a href="#javascript">{'card'}</a> {'component, you can extend the default collapse behavior to create an accordion.'}</span>
                    </CardHeader>
                    <CardBody>
                        <Form className="theme-form">
                            <FormGroup>
                                <Label className="col-form-label pt-0" >{EmailAddress}</Label>
                                <Input className="form-control" type="email" placeholder="Enter email" />
                                <small className="form-text text-muted">{'We\'ll never share your email with anyone else.'}</small>
                            </FormGroup>
                            <FormGroup>
                                <Label htmlFor="exampleInputPassword1">{Password}</Label>
                                <Input className="form-control" type="password" placeholder="Password" />
                            </FormGroup>
                            <div className="checkbox p-0">
                                <Input id="dafault-checkbox" type="checkbox" data-original-title="" title="" />
                                <Label className="mb-0" for="dafault-checkbox">{'Remember my preference'}</Label>
                            </div>
                        </Form>
                    </CardBody>
                    <FooterCard />
                </Card>
            </Col>
        </Fragment>
    );
};

export default DefaultFormLayoutClass;