import { Breadcrumbs } from '../../../AbstractElements';
import Sidebar from '../JobCardView/Sidebar';
import ListCard from './ListCard';
import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';

const ListView = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle='List View' parent='Job Search' title='List View' />
      <Container fluid={true}>
        <Row className='mb-5'>
          <Sidebar />
          <ListCard colClass='col-xl-9 xl-60 box-col-8' />
        </Row>
      </Container>
    </Fragment>
  );
};

export default ListView;
