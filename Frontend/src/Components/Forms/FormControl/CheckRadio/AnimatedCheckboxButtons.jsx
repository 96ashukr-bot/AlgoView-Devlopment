import React, { Fragment } from "react";
import { Row, Col, Card, CardBody, Label, Input } from 'reactstrap'
import { AnimatedCheckboxButtons, Option } from "../../../../Constant";
import HeaderCard from "../../../Common/Component/HeaderCard";

const AnimatedCheckboxButtonsClass = () => {
    return (
        <Fragment>
            <Col md="6">
                <Card>
                    <HeaderCard title={AnimatedCheckboxButtons} />
                    <CardBody className="animate-chk">
                        <Row>
                            <Col>
                                <Label className="d-block" for="chk-ani">
                                    <Input className="checkbox_animated" id="chk-ani" type="checkbox" defaultChecked />{Option} {"1"}
                                </Label>
                                <Label className="d-block" for="chk-ani1">
                                    <Input className="checkbox_animated" id="chk-ani1" type="checkbox" />{Option} {"2"}
                                </Label>
                                <Label className="d-block" for="chk-ani2">
                                    <Input className="checkbox_animated" id="chk-ani2" type="checkbox" defaultChecked />{Option} {"3"}
                                </Label>
                                <Label className="d-block" for="chk-ani3">
                                    <Input className="checkbox_animated" id="chk-ani3" type="checkbox" />{Option} {"4"}
                                </Label>
                            </Col>
                        </Row>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}

export default AnimatedCheckboxButtonsClass;