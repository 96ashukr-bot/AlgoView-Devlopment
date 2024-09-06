import { Breadcrumbs } from '../../../AbstractElements';
import DetailedSidebar from './DetailedSidebar';
import MainCard from './MainCard';
import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';

const KnowledgeDetailContain = () => {
    return (
        <Fragment>
            <Breadcrumbs mainTitle='Knowledge Details' parent='Knowledgebase' title='Knowledge Details' />
            <Container fluid={true}>
                <Row>
                    <DetailedSidebar />
                    <MainCard />
                </Row>
            </Container>
        </Fragment>
    );
};
export default KnowledgeDetailContain;