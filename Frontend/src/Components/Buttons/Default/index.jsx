import React, { Fragment } from 'react';
import { Container, Row, Col, Card, CardHeader, CardBody } from 'reactstrap';
import { CustomStateButtons } from '../../../Constant';
import { Breadcrumbs, Btn, H5 } from '../../../AbstractElements';
import { DefaultButtonData } from '../../Common/Data/Buttons';

const DefaultButton = () => {
    return (
        <Fragment>
            <Breadcrumbs mainTitle='Default Style' parent="Buttons" title="Default Style" />
            <Container fluid={true}>
                <Row>
                    <Col sm="12">
                        {DefaultButtonData.map((item, i) =>
                            <Card id={item.cardId ? item.cardId : ''} key={i}>
                                <CardHeader>
                                    <H5>{item.title}</H5>
                                    <span>{item.span} {item.code ? <code>{item.code}</code> : ''}{item.detail ? item.detail : ''}
                                        {item.code1 ? <code>{item.code1}</code> : ''} {item.detail1 ? item.detail1 : ''} </span>
                                </CardHeader>
                                <CardBody>
                                    <div className="btn-showcase">
                                        {
                                            item.btnSub.map((btnItem, i) =>
                                                <Fragment key={i}>
                                                    <Btn attrBtn={{
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
                        <Card id="custom-state-button">
                            <CardHeader>
                                <H5>{CustomStateButtons}</H5>
                                <span>{'The'} <code>{'.btn'}</code> {'class used with'} <code>&lt;{'button'}&gt;</code>, <code>&lt;{'a'}&gt;</code> {'and'} <code>&lt;{'input'}&gt;</code> {'elements.'}</span>
                            </CardHeader>
                            <CardBody className=" btn-showcase">
                                <Btn attrBtn={{ color: 'primary' }}>{'Link'}</Btn>
                                <input className="btn btn-secondary" type="button" value="Input" data-toggle="tooltip" title="btn btn-secondary" />
                                <input className="btn btn-success" type="submit" value="Submit" data-toggle="tooltip" title="btn btn-success" />
                                <Btn attrBtn={{ color: 'info', type: 'submit' }} >{'Button'}</Btn>
                            </CardBody>
                        </Card>
                    </Col>
                </Row>
            </Container>
        </Fragment>
    );
};

export default DefaultButton;