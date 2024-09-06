import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../AbstractElements';
import LeftGrid from './LeftGrid';
import RightGrid from './RightGrid';

const Ecommerce = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle='E-Commerce Dashboard' parent='Dashboard' title='E-Commerce' />
      <Container fluid={true}>
        <Row className='size-column'>
          <LeftGrid />
          <RightGrid />
        </Row>
      </Container>
    </Fragment>
  );
};

export default Ecommerce;
