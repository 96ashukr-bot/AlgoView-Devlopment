import React, { Fragment } from 'react';
import { Container, Row, Col } from 'reactstrap';
import { Breadcrumbs } from '../../../AbstractElements';
import Basic from './Basic/index';
import Small from './Small/index';
import Large from './Large/index';
import Custom from './Custom/index';
import States from './States/index';
import MultiBars from './MultiBars/index';
import Striped from './Stripped/index';
import Animated from './Animated/index';

const Progressbars = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle="Progress" parent="Ui Kits" title="Progress" />
      <Container fluid={true}>
        <Row>
          <Col sm="12">
            <Basic />
            <Small />
            <Large />
            <Custom />
            <States />
            <MultiBars />
            <Striped />
            <Animated />
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};

export default Progressbars;