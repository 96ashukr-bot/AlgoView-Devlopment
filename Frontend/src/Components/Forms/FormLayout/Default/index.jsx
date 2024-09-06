import React, { Fragment } from 'react';
import { Container, Row, Col } from 'reactstrap';
import { Breadcrumbs } from '../../../../AbstractElements';
import DefaultFormLayoutClass from './DefaultFormLayout';
import HorizontalFormLayoutClass from './HorizontalFormLayout';
import MegaFormClass from './MegaFormClass';
import InlineFormClass from './InlineFormClass';

const FormDefault = () => {
    return (
        <Fragment>
            <Breadcrumbs parent="Forms" title="Default Forms" subParent='Form Layout' mainTitle='Default Forms' />
            <Container fluid={true}>
                <Row>
                    <Col sm="12" xl="6">
                        <Row>
                            <DefaultFormLayoutClass />
                            <HorizontalFormLayoutClass />
                        </Row>
                    </Col>
                    <Col sm="12" xl="6">
                        <Row>
                            <MegaFormClass />
                            <InlineFormClass />
                        </Row>
                    </Col>
                </Row>
            </Container>
        </Fragment>
    );
};

export default FormDefault;