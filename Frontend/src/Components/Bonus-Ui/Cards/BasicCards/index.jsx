import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../../AbstractElements';
import BasicCommon from './BasicCommon';

const BasicCards = () => {
    return (
        <Fragment>
            <Breadcrumbs mainTitle="Basic Card" parent="Bonus Ui" title="Basic Card" />
            <Container fluid={true}>
                <Row>
                    <BasicCommon />
                </Row>
            </Container>
        </Fragment>
    );
};

export default BasicCards;