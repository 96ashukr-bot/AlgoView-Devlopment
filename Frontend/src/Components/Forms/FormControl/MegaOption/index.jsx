import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap'
import { Breadcrumbs } from '../../../../AbstractElements';
import DefaultClass from './DefaultOption';
import NoBorderClass from './NoBorder';
import SolidBorderClass from './SolidBorder';
import OfferBorderClass from './OfferStyleBorder';
import InlineClass from './InlineStyle';
import VerticalClass from './VerticalStyle';
import HorizontalClass from './HorizontalStyle';


const MegaOption = () => {
    return (
        <Fragment>
            <Breadcrumbs parent="Form" title="Mega Options" mainTitle='Mega Options' subParent='Form Controls' />
            <Container fluid={true}>
                <Row>
                    <DefaultClass />
                    <NoBorderClass />
                    <SolidBorderClass />
                    <OfferBorderClass />
                    <InlineClass />
                    <VerticalClass />
                    <HorizontalClass />
                </Row>
            </Container>
        </Fragment>
    );
}

export default MegaOption;