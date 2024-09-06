import React, { Fragment } from 'react';
import { Breadcrumbs } from '../../../../AbstractElements';
import BasicInputCard1 from './BasicInputCard1';
import BasicInputCard2 from './BasicInputCard2';
import { Container, Row, Col } from 'reactstrap';

const InputGroups = () => {
  return (
    <Fragment>
      <Breadcrumbs parent='Forms' title='Input Groups' mainTitle='Input Groups' subParent='Form Controls' />
      <Container fluid={true}>
        <Row>
          <Col sm='12'>
            <BasicInputCard1 />
            <BasicInputCard2 />
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};

export default InputGroups;
