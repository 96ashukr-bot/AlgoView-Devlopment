import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../AbstractElements';
import BasicClass from './Basic';
import DefaultSteps from './DefaultSteps';
import PearlsStepsClass from './PearlsSteps';
import PearlsStepSizingClass from './PearlsStepSizing';
import PearlsStepStatesClass from './PearlsStepStates';
import StepsSizingClass from './StepSizing';
import StepsStatesClass from './StepsStates';
import StepsWithIcon from './StepsWithIcon';
import VerticalStepClass from './VerticalStep';

const Steps = () => {
    return (
        <Fragment>
            <Breadcrumbs mainTitle="Steps" parent="Bonus Ui" title="Steps" />
            <Container fluid={true}>
                <Row>
                    <BasicClass />

                    <StepsWithIcon />

                    <StepsStatesClass />

                    <StepsSizingClass />

                    <VerticalStepClass />

                    <DefaultSteps />

                    <PearlsStepsClass />

                    <PearlsStepSizingClass />

                    <PearlsStepStatesClass />
                </Row>
            </Container>
        </Fragment>
    );
};

export default Steps;