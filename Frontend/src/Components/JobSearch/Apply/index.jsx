import { Breadcrumbs } from '../../../AbstractElements';
 import Sidebar from '../JobCardView/Sidebar';
import JobApply from './Form';
import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';

const Apply = () => {
    return (
        <Fragment>
            <Breadcrumbs mainTitle='Apply' parent='Job Search' title='Apply' />
            <Container fluid={true}>
                <Row>
                    <Sidebar />
                    <JobApply />
                </Row>
            </Container>
        </Fragment>
    );
};

export default Apply;