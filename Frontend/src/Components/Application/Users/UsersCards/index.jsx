import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../../AbstractElements';
import AllCards from './AllCards';

const UsersCardssContain = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle='User Cards' parent='Users' title='User Cards' />
      <Container fluid className='user-card'>
        <Row>
          <AllCards />
        </Row>
      </Container>
    </Fragment>
  );
};
export default UsersCardssContain;
