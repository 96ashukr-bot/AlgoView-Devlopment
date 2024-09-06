import { Breadcrumbs } from '../../../AbstractElements';
import Sidebar from '../JobCardView/Sidebar';
import MainCard from './MainCard';
import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';

const JobDetails = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle='Job Details' parent='Job Search' title='Job Details' />
      <Container fluid={true}>
        <Row className='mb-5'>
          <Sidebar />
          <MainCard />
        </Row>
      </Container>
    </Fragment>
  );
};

export default JobDetails;
