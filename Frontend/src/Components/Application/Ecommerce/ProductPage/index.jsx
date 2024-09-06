import BrandShipping from './BrandShipping';
import ImageSlider from './ImageSilder';
import ProductDetails from './ProductDetails';
import { Card, CardBody, Col, Container, Row } from 'reactstrap';
import { Fragment } from 'react';
import React from 'react';
import Tablet from './Tabsets';
import { Breadcrumbs } from '../../../../AbstractElements';

const ProductPageContain = () => {
  return (
    <Fragment>
      <Breadcrumbs parent='Ecommerce' title='Product Page' mainTitle='Product Page' />
      <Container fluid={true}>
        <div>
          <Row className='product-page-main p-0'>
            <Col xxl='4' md='6' className='box-col-12'>
              <Card>
                <CardBody>
                  {/* <Row> */}
                  <ImageSlider />
                  {/* </Row> */}
                </CardBody>
              </Card>
            </Col>
            <ProductDetails />
            <Col xxl="3" md="6" className='box-col-6'>
              <BrandShipping />
            </Col>
          </Row>
        </div>
        <Tablet />
      </Container>
    </Fragment>
  );
};
export default ProductPageContain;
