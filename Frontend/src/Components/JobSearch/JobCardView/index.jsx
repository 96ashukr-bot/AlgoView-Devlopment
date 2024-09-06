import { Breadcrumbs } from '../../../AbstractElements';
 import Sidebar from './Sidebar';
import CardsClass from './Cards';
import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';

const JobCards = () => {
    return (
        <Fragment>
            <Breadcrumbs mainTitle='Cards View' parent='Job Search' title='Cards View' />
            <Container fluid={true}>
                <Row>
                    <Sidebar />
                    <CardsClass />
                </Row>
            </Container>
        </Fragment>
    );
};

export default JobCards;