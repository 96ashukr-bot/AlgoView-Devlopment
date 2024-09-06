import React, { Fragment } from 'react';
import { Container, Row, Col, Card, CardHeader } from 'reactstrap';
import { Breadcrumbs, H5 } from '../../../AbstractElements';
import RibbonClass from './RibbonClass';
import RibbonComponent from './RibbonCommon';

const Ribbons = () => {
  return (
    <Fragment>
      <Breadcrumbs parent="Bouns Ui" title="Ribbons" mainTitle='Ribbons' />
      <Container fluid={true}>
        <Row>
          <Col sm="12" xl="12">
            <Card>
              <CardHeader>
                <H5>Colored Ribbons</H5><span>{'use class'} <code>{'.Colored-colored .bg-primary'}</code></span>
              </CardHeader>
              <RibbonClass />
            </Card>
          </Col>

          <RibbonComponent />
        </Row>

      </Container>
    </Fragment>
  );
};

export default Ribbons;