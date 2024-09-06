import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap'
import { Breadcrumbs } from '../../../../AbstractElements';
import AnimatedCheckboxButtonsClass from './AnimatedCheckboxButtons';
import AnimatedClass from './AnimatedClass';
import CustomCheckboxClass from './CustomCheckbox';
import CustomRadioClass from './CustomRadio';
import SquareCheckboxClass from './SquareCheckbox';

const CheckboxandRadio = () => {
    return (
        <Fragment>
            <Breadcrumbs mainTitle='Checkbox & Radio' parent="Forms" title="Checkbox & Radio" subParent='Forms Controls' />
            <Container fluid={true}>
                <Row>
                    <CustomRadioClass />
                    <CustomCheckboxClass />
                    <AnimatedClass />
                    <AnimatedCheckboxButtonsClass />
                    <SquareCheckboxClass />
                </Row>
            </Container>
        </Fragment>
    );
}

export default CheckboxandRadio;