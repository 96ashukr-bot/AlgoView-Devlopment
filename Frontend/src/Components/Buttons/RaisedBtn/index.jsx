import React, { Fragment } from 'react';
import { Container, Row, Col, Card, CardHeader, CardBody } from 'reactstrap'
import { Breadcrumbs, Btn, H5 } from '../../../AbstractElements';
import { CustomStateButtons } from '../../../Constant';
import { RaisedButtonData } from '../../Common/Data/Buttons';

const RaisedButton = () => {
    return (
        <Fragment>
            <Breadcrumbs mainTitle="Raised Buttons" parent="Buttons" title="Raised Buttons" />
            <Container fluid={true}>
                <Row>
                    <Col sm="12">
                        {RaisedButtonData.map((item, i) =>
                            <Card key={i}>
                                <CardHeader>
                                    <H5>{item.title}</H5>
                                    <span>{item.span} <code>{item.code}</code> {item.detail}</span>
                                </CardHeader>
                                <CardBody>
                                    <div  className="btn-showcase">
                                    {
                                        item.btnSub.map((btnItem, i) =>
                                            <Fragment key={i}>
                                                <Btn attrBtn={{
                                                    className: btnItem.btnClass,
                                                    color: btnItem.colorClass, size: btnItem.size ? btnItem.size : '',
                                                    active: btnItem.active ? true : false,
                                                    disabled: btnItem.disabled ? true : false,
                                                    outline: btnItem.outline ? true : false
                                                }}
                                                >
                                                    {btnItem.title}
                                                </Btn>
                                            </Fragment>
                                        )
                                    }
                                    </div>
                                </CardBody>
                            </Card>
                        )}
                        <Card>
                            <CardHeader>
                                <H5>{CustomStateButtons}</H5>
                                <span>{"The"} <code>{".btn"}</code> {"class used with"} <code>&lt;{"button"}&gt;</code>, <code>&lt;{"a"}&gt;</code> {"and"} <code>&lt;{"input"}&gt;</code> {"elements."}</span>
                            </CardHeader>
                            <CardBody className="btn-showcase">
                                <Btn attrBtn={{ className: "btn btn-pill btn-air-primary", color: "primary" }} >{"Link"}</Btn>
                                <input className="btn btn-pill btn-air-secondary btn-secondary" type="button" value="Input" data-toggle="tooltip" title="btn btn-secondary" />
                                <input className="btn btn-pill btn-air-success btn-success" type="submit" value="Submit" data-toggle="tooltip" title="btn btn-success" />
                                <Btn attrBtn={{ className: "btn btn-pill btn-air-info", color: "btn-info", type: "submit" }} >{"Button"}</Btn>
                            </CardBody>
                        </Card>
                    </Col>
                </Row>
            </Container>
        </Fragment>
    );
};

export default RaisedButton;