import React, { Fragment } from 'react';
import { Breadcrumbs } from '../../../../AbstractElements';
import { WishlistTitle } from '../../../../Constant';
import WishListData from './WishListData';
import HeaderCard from '../../../Common/Component/HeaderCard';
import { Card, CardBody, Col, Container, Row } from 'reactstrap';

const WishListContain = () => {
  return (
    <Fragment>
      <Breadcrumbs parent='Ecommerce' title='Wishlist' mainTitle='Wishlist' />
      <Container fluid={true}>
        <Row>
          <Col sm='12'>
            <Card>
              <HeaderCard title={WishlistTitle} />
              <CardBody>
                <Row className='g-sm-4 g-3'>
                  <WishListData />
                </Row>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};
export default WishListContain;
