import React, { Fragment } from 'react';
import TooltipForm from '../TooltipForm';
import { Container, Row, Col, Card, CardHeader, CardBody } from 'reactstrap';
import { Tooltips } from '../../../../Constant';
import { Breadcrumbs, H5 } from '../../../../AbstractElements';
import CustomStylesClass from './CustomStyles';
import BrowserDefaultsClass from './BrowserDefaults';
import SupportedElementsClass from './SupportedElements';

const FormValidation = () => {

    return (
        <Fragment>
            <Breadcrumbs mainTitle='Validation Forms' parent="Forms" title="Validation Forms" subParent='Forms Controls' />
            <Container fluid={true}>
                <Row>
                    <Col sm="12">
                        <CustomStylesClass />
                        <BrowserDefaultsClass />
                        <SupportedElementsClass />
                        <Card>
                            <CardHeader>
                                <H5>{Tooltips}</H5>
                                <span>{'If your form layout allows it, you can swap the'} <code className="text-danger">{'.feedback'}</code> {'classes for'} <code className="text-danger">{'.tooltip'}</code> {'classes to display validation feedback in a styled tooltip. Be sure to have a parent with'} <code className="text-danger">{'position: relative'}</code> {'on it for tooltip positioning. In the example below, our column classes have this already, but your project may require an alternative setup.'}</span>
                            </CardHeader>
                            <CardBody>
                                <TooltipForm />
                            </CardBody>
                        </Card> 
                    </Col>
                </Row>
            </Container>
        </Fragment>
    );
};

export default FormValidation;