import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../../AbstractElements';
import LeftContact from './Left-contact';

const ContactFirebase = () => {

  return (
    <Fragment>
      <Breadcrumbs mainTitle="Contact App" parent="Apps" title="Contact" />
      <Container fluid={true}>
        <div className="email-wrap bookmark-wrap">
          <Row>
            <LeftContact />
          </Row>
        </div>
      </Container>
    </Fragment>
  );
};
export default ContactFirebase;