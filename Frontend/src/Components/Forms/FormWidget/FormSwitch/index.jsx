import React, { Fragment } from 'react';
import { Card, CardHeader, Col, Container, Row } from 'reactstrap';
import { Breadcrumbs, H5 } from '../../../../AbstractElements';
import BasicSwitch from './BasicSwitch';
import BasicColor from './SwitchColor';
import SwitchIcon from './SwitchIcon';
import SwitchOutline from './SwitchOutline';
import SwitchSizing from './SwitchSizing';
import SwitchwithColor from './SwitchwithColor';

const FormSwitchContain = () => {
    return (
        <Fragment>
            <Breadcrumbs parent="Forms" title="Switch" subParent='Form Widgets' mainTitle="Switch" />
            <Container fluid={true}>
                <Row>
                    <BasicSwitch />
                    <BasicColor />
                    <Col sm="12" xl="6" lg="12" md="6">
                        <Card>
                            <CardHeader>
                                <H5>Switch Outline</H5>
                            </CardHeader>
                            <SwitchOutline />
                        </Card>
                    </Col>
                    <Col sm="12" xl="6" lg="12" md="6">
                        <Card>
                            <CardHeader>
                                <H5>Switch Unchecked Outline</H5>
                            </CardHeader>
                            <SwitchOutline />
                        </Card>
                    </Col>
                    <Col sm="12" xl="4">
                        <Card>
                            <CardHeader>
                                <H5>Switch Sizing</H5>
                            </CardHeader>
                            <SwitchSizing />
                        </Card>
                    </Col>
                    <Col sm="12" xl="4">
                        <Card>
                            <CardHeader>
                                <H5>Switch With Icon</H5>
                            </CardHeader>
                            <SwitchIcon />
                        </Card>
                    </Col>
                    <Col sm="12" xl="4">
                        <Card>
                            <CardHeader>
                                <H5>Switch With Color</H5>
                            </CardHeader>
                            <SwitchwithColor />
                        </Card>
                    </Col>
                </Row>
            </Container>
        </Fragment>
    );
};
export default FormSwitchContain;