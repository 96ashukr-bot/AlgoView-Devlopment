import React, { Fragment } from 'react';
import { Container } from 'reactstrap';
import { Breadcrumbs } from '../../AbstractElements';
import SamplePage from './SimplePage';

const FooterFixed = () => {
    return (
        <Fragment>
            <Breadcrumbs mainTitle="Footer Fixed" title="Footer Fixed" parent="Page Layout" />
            <Container fluid={true}>
                <SamplePage />
            </Container>
        </Fragment>
    )
}

export default FooterFixed;