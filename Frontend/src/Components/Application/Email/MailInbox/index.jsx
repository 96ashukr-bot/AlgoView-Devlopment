import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../../AbstractElements';

import Email from './Email';
import MailSidebar from './MailSidebar';

const MailInboxContain = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle='Email Compose' parent='Apps' title='Email Compose' />
      <Container fluid={true}>
        <div className='email-wrap'>
          <Row>
            <Email />
            <MailSidebar />
          </Row>
        </div>
      </Container>
    </Fragment>
  );
};
export default MailInboxContain;
