import React, { Fragment } from 'react';
import { CardBody, Col, Input, Label, Media } from 'reactstrap';
import { Switchcolor } from '../../../../Data/FormWidgets';

const SwitchOutline = () => {
    return (
        <Fragment>
            <CardBody className="row switch-showcase height-equal">
                <Col sm="12">
                    {
                        Switchcolor.map((item) => {
                            return (
                                <Media key={item.id}>
                                    <Label className="col-form-label m-r-10">{item.title}</Label>
                                    <Media body className={item.mediaclass}>
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
        </Fragment>
    );
};
export default SwitchOutline;