import { Breadcrumbs } from '../../../AbstractElements';
import LearningFilter from '../Common/LearningFilter';
import LearningDeatil from './LearningDeatil';
import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';

const DetailCourse = () => {
    return (
        <Fragment>
            <Breadcrumbs mainTitle="Detailed Course" parent="Learning" title="Detailed Course" />
            <Container fluid={true}>
                <Row>
                    <LearningDeatil />
                    <LearningFilter />
                </Row>
            </Container>
        </Fragment>
    );
};

export default DetailCourse;