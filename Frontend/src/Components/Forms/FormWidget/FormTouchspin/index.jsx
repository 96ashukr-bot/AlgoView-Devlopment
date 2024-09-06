import React from 'react';
import { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import DefaultTouchSpin from './DefaultTouchspin';
import MinMax from './MinMax';
import TickIcon from './TickIcon';
import DropdownTouchspin from './Dropdown';
import HorizontalTouchspin from './HorizontalTouchspin';
import LargeHorizontal from './LargeHorizontal';
import Vertical from './Vertical';
import Postfix from './Postfix';
import Prefix from './Prefix';
import InitialValue from './InitialValue';
import DecimalValues from './DecimalValue';
import StepValues from './StepValues';
import ButtonClass from './ButtonClass';
import IconButton from './IconButton';
import MouseDisabled from './MouseDisable';
import { Breadcrumbs } from '../../../../AbstractElements';

const FormTouchspinContain = () => {
    return (
        <Fragment>
            <Breadcrumbs parent="Forms" title="Touchspin" subParent='Form Widgets' mainTitle="Touchspin" />
            <Container fluid={true}>
                <div className="bootstrap-touchspin">
                    <Row>
                        <DefaultTouchSpin />
                        <Vertical />
                        <Postfix />
                        <Prefix />
                        <MinMax />
                        <InitialValue />
                        <StepValues />
                        <DecimalValues />
                        <ButtonClass />
                        <TickIcon />
                        <IconButton />
                        <DropdownTouchspin />
                        <MouseDisabled />
                        <HorizontalTouchspin />
                        <LargeHorizontal />
                    </Row>
                </div>
            </Container>
        </Fragment>
    );
};
export default FormTouchspinContain;