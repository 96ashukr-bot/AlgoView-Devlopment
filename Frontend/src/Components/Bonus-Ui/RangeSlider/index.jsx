import React, { Fragment } from 'react';
import { Breadcrumbs } from '../../../AbstractElements';
import { Container, Row } from 'reactstrap';
import BasicSliderClass from './BasicSlider';
import NegativeValuesClass from './NegativeValues';
import DisabledClass from './Disabled';
import FormatedLabelClass from './FormatedLabel';
import FormatedLabelClass2 from './FormatedLabel2';
import DraggableRangeClass from './DraggableRange';

const RangeSlider = () => {

    return (
        <Fragment>
            <Breadcrumbs mainTitle="Range Slider" parent="Bouns Ui" title="Range Slider" />
            <Container fluid={true}>
                <Row>
                    <BasicSliderClass />

                    <NegativeValuesClass />

                    <DisabledClass />

                    <FormatedLabelClass />

                    <FormatedLabelClass2 />

                    <DraggableRangeClass />

                </Row>
            </Container>
        </Fragment>
    );
}

export default RangeSlider;