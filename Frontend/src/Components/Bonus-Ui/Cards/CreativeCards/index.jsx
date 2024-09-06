import React, { Fragment } from 'react';
import { Breadcrumbs } from '../../../../AbstractElements';
import { Container, Row } from 'reactstrap';
import CreativeCardsCommon from './themeCards';

const CreativeCards = () => {
    return (
        <Fragment>
            <Breadcrumbs mainTitle='Creative Cards' parent='Bonus Ui' title='Creative Cards' />
            <Container fluid={true}>
                <Row>
                    <CreativeCardsCommon />
                </Row>
            </Container>
        </Fragment>
    );
};

export default CreativeCards;