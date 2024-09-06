import React, { Fragment } from 'react';
import { Container } from 'reactstrap';
import { Breadcrumbs } from '../../AbstractElements';
import SamplePage from './SimplePage';

const FooterDark = () => {
    return (
        <Fragment>
            <Breadcrumbs mainTitle="Footer Dark" title="Footer Dark" parent="Page Layout" />
            <Container fluid={true}>
                <SamplePage />
            </Container>
        </Fragment>
    );
};

export default FooterDark;