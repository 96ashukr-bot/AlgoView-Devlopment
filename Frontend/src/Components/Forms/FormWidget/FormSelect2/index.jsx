import React, { Fragment } from 'react';
import { Card, CardBody, CardHeader, Col, Container, Row } from 'reactstrap';
import { Breadcrumbs, H5 } from '../../../../AbstractElements';
import FullColored from './FullColored';
import OutlineColor from './OutlineColor';
import SelectForm from './SelectForm';

const FormSelectContain = () => {
    return (
        <Fragment>
            <Breadcrumbs parent="Forms" title="Select-2" subParent='Form Widgets' mainTitle="Select-2" />
            <Container fluid={true}>
                <div className="select2-drpdwn">
                    <Row >
                        <Col md="12">
                            <Card>
                                <CardHeader>
                                    <H5 attrH5={{ className: 'card-title' }}>Select-2</H5>
                                </CardHeader>
                                <CardBody>
                                    <SelectForm />
                                </CardBody>
                            </Card>
                        </Col>
                        <Col md="6">
                            <Card>
                                <CardHeader className=" pb-0">
                                    <H5 attrH5={{ className: 'card-title' }}>Outline Color Variant</H5>
                                </CardHeader>
                                <CardBody>
                                    <OutlineColor />
                                </CardBody>
                            </Card>
                        </Col>
                        <Col md="6">
                            <Card>
                                <CardHeader className=" pb-0">
                                    <H5 attrH5={{ className: 'card-title' }}>Full Colored Variant</H5>
                                </CardHeader>
                                <CardBody>
                                    <FullColored />
                                </CardBody>
                            </Card>
                        </Col>
                    </Row>
                </div>
            </Container>
        </Fragment>
    );
};
export default FormSelectContain;