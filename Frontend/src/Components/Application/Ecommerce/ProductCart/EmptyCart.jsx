import React, { Fragment } from 'react';
import { H3, H4 } from '../../../../AbstractElements';
import { CartEmpty, ExploreShortlistItems } from '../../../../Constant';
import { Col, Container, Row } from 'reactstrap';

const EmptyCart = () => {
  return (
    <Fragment>
      <section className='cart-section section-b-space'>
        <Container fluid={true}>
          <Row>
            <Col sm='12'>
              <div className='empty-cart-cls text-center'>
                <H3>
                  <strong>{CartEmpty}</strong>
                </H3>
                <H4>{ExploreShortlistItems}</H4>
              </div>
            </Col>
          </Row>
        </Container>
      </section>
    </Fragment>
  );
};
export default EmptyCart;
