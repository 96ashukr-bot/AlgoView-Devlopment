import React from "react";
import { Fragment } from "react";
import { H5 } from "../../../../AbstractElements"
import { DatePickers } from "../../../../Constant/index"
import { Card, CardBody, CardHeader, Col, Container, Row } from "reactstrap";
import DatePickersData from "./DatePicker";
const FormDatapickerContain = () => {
    return (
        <Fragment>
            <Container fluid={true}>
                <Row>
                    <Col>
                        <Card>
                            <CardHeader>
                                <H5>{DatePickers}</H5>
                            </CardHeader>
                            <CardBody>
                                <Row>
                                    <Col md="12">
                                        <div className="date-picker">
                                            <DatePickersData />
                                        </div>
                                    </Col>
                                </Row>
                            </CardBody>
                        </Card>
                    </Col>
                </Row>
            </Container>
        </Fragment>
    )
}
export default FormDatapickerContain