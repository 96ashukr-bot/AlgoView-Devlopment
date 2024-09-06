import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../AbstractElements';
import LeftGrid from './LeftGrid';
import MainGrid from './MainGrid';
import RightGrid from './RightGrid';

const Crypto = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle='Crypto' parent='Dashboard' title='Crypto' />
      <Container fluid={true}>
        <Row>
          <LeftGrid />
          <MainGrid />
          <RightGrid />
        </Row>
      </Container>
    </Fragment>
  );
};

export default Crypto;
