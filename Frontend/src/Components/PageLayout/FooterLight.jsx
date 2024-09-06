import React, { Fragment } from 'react';
import { Container } from 'reactstrap';
import { Breadcrumbs } from '../../AbstractElements';
import SamplePage from './SimplePage';

const FooterLight = () => {
    return (
        <Fragment>
            <Breadcrumbs mainTitle="Footer Light" title="Footer Light" parent="Page Layout" />
            <Container fluid={true}>
                <SamplePage />
            </Container>
        </Fragment>
    );
};

export default FooterLight;