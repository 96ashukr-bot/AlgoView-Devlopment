import { Btn, H1, H3, H5, H6 } from '../../../../AbstractElements';
import { Standard, Premium, LorumIpsum, Business, Extra, Purchase } from '../../../../Constant';
import React, { Fragment } from 'react';
import { Col, CardBody, Card, Row } from 'reactstrap';

const Standards = () => {
    return (
        <Fragment>
            <CardBody className="pricing-content">
                <Row>
                    <Col xl="3 xl-50" sm="6" className="box-col-6">
                        <Card className="text-center pricing-simple">
                            <CardBody>
                                <H3>{Standard}</H3>
                                <H1>{"$15"}</H1>
                                <H6 attrH6={{ className: "mb-0" }}>{LorumIpsum}</H6>
                            </CardBody><Btn attrBtn={{ size: "lg", color: "primary" }} >
                                <H5 attrH5={{ className: "mb-0" }}>{Purchase}</H5></Btn>
                        </Card>
                    </Col>
                    <Col xl="3 xl-50" sm="6" className="box-col-6">
                        <Card className="text-center pricing-simple">
                            <CardBody>
                                <H3>{Business}</H3>
                                <H1>{"$25"}</H1>
                                <H6 attrH6={{ className: "mb-0" }} >{LorumIpsum}</H6>
                            </CardBody><Btn attrBtn={{ size: "lg", color: "primary" }} >
                                <H5 attrH5={{ className: "mb-0" }} >{Purchase}</H5></Btn>
                        </Card>
                    </Col>
                    <Col xl="3 xl-50" sm="6" className="box-col-6">
                        <Card className="text-center pricing-simple">
                            <CardBody>
                                <H3>{Premium}</H3>
                                <H1>{"$35"}</H1>
                                <H6 attrH6={{ className: "mb-0" }} >{LorumIpsum}</H6>
                            </CardBody><Btn attrBtn={{ size: "lg", color: "primary" }} >
                                <H5 attrH5={{ className: "mb-0" }} >{Purchase}</H5></Btn>
                        </Card>
                    </Col>
                    <Col xl="3 xl-50" sm="6" className="box-col-6">
                        <Card className="text-center pricing-simple">
                            <CardBody>
                                <H3>{Extra}</H3>
                                <H1>{"$45"}</H1>
                                <H6 attrH6={{ className: "mb-0" }} >{LorumIpsum}</H6>
                            </CardBody><Btn attrBtn={{ size: "lg", color: "primary" }} >
                                <H5 attrH5={{ className: "mb-0" }} >{Purchase}</H5></Btn>
                        </Card>
                    </Col>
                </Row>
            </CardBody>
        </Fragment>
    );
};
export default Standards;