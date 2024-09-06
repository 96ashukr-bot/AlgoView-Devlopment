import React, { Fragment } from 'react';
import { Breadcrumbs } from '../../../AbstractElements';
import { Container, Row } from 'reactstrap';
import Basic from './Basic';
import Advanced from './Advance';
import Alert from './Alert';

const SweetAlerts = () => {

  return (
    <Fragment>
      <Breadcrumbs mainTitle="Sweet Alert" parent="Bouns Ui" title="Sweet Alert" />
      <Container fluid={true}>
        <Row>
         
          <Basic />
         
          <Advanced />
         
          <Alert />

        </Row>
      </Container>
    </Fragment>
  );
}

export default SweetAlerts;