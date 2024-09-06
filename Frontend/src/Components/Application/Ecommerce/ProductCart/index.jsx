import CartData from './CartData';
import React, { Fragment } from 'react';
import { Breadcrumbs } from '../../../../AbstractElements';
import { Card, Col, Container, Row } from 'reactstrap';

const ProductCartConatain = () => {
    return (
        <Fragment>
            <Breadcrumbs parent="Ecommerce" title="Cart" mainTitle='Cart' />
            <Container fluid={true}>
                <Row>
                    <Col sm="12">
                        <Card>
                            <CartData />
                        </Card>
                    </Col>
                </Row>
            </Container>
        </Fragment>
    );
};
export default ProductCartConatain;