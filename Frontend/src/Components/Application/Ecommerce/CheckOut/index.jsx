import React, { Fragment } from 'react';
import { Card, CardBody, Col, Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../../AbstractElements';
import { BillingDetails } from '../../../../Constant';
import CheckoutTableData from './CheckoutTableData';
import ProductPlaceOrder from './ProductPlaceOrder';
import HeaderCard from '../../../Common/Component/HeaderCard';

const CheckOutContain = () => {
  return (
    <Fragment>
      <Breadcrumbs parent='Ecommerce' title='Checkout' mainTitle='Checkout' />
      <Container fluid={true}>
        <Row>
          <Col>
            <Card className='checkout'>
              <HeaderCard title={BillingDetails} />
              <CardBody>
                <Row>
                  <CheckoutTableData />
                  <ProductPlaceOrder />
                </Row>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};
export default CheckOutContain;
