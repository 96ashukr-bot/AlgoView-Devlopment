import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader, Col, Input, Label, Media } from 'reactstrap';
import { H5 } from '../../../../AbstractElements';
import { Switchcolor } from '../../../../Data/FormWidgets';

const BasicColor = () => {
    return (
        <Fragment>
            <Col sm="12" xl="6" lg="12" md="6">
                <Card>
                    <CardHeader>
                        <H5>Switch Color</H5>
                    </CardHeader>
                    <CardBody className="row switch-showcase height-equal">
                        <Col sm="12">
                            {
                                Switchcolor.map((item) => {
                                    return (
                                        <Media key={item.id}>
                                            <Label className="col-form-label m-r-10">{item.title}</Label>
                                            <Media body className="text-end icon-state">
                                                <Label className="switch">
                                                    <Input type="checkbox" /><span className={item.spanclass}></span>
                                                </Label>
                                            </Media>
                                        </Media>
                                    );
                                })
                            }
                        </Col>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};
export default BasicColor;